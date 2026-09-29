"""Each story in docs/data-stories.md must be visible in the generated data.

Metrics here mirror the definitions the dbt marts use (see the doc), computed
directly on the raw tables.
"""
from datetime import date, timedelta

import pandas as pd
import pytest

from data_generation import config as C
from data_generation.config import BuildConfig
from data_generation.dates import add_months, month_end
from data_generation.tables import generate

CFG = BuildConfig(seed=C.DEFAULT_SEED, end_month=date(2026, 8, 1))
MONTHS = [add_months(CFG.start_month, i) for i in range(C.HISTORY_MONTHS)]


@pytest.fixture(scope="module")
def tables():
    return generate(CFG)


@pytest.fixture(scope="module")
def paid(tables):
    subs = tables["subscriptions"]
    channels = tables["organizations"][["organization_id", "acquisition_channel"]]
    return subs[~subs["is_trial"]].merge(channels, on="organization_id")


def active_on(periods: pd.DataFrame, d: date) -> pd.DataFrame:
    return periods[(periods["start_date"] <= d) & (periods["end_date"].isna() | (periods["end_date"] > d))]


def logo_churn_rate(paid: pd.DataFrame, month: date, plans: list[str] | None = None) -> float:
    """Customers paying at the previous month end who pay nothing at this month end.

    `plans` filters on the plan held at the previous month end, so a Starter
    customer who upgrades to Pro is not a Starter churn. Same definition as the
    dbt marts.
    """
    at_start = active_on(paid, month - timedelta(days=1))
    if plans is not None:
        at_start = at_start[at_start["plan_id"].isin(plans)]
    if at_start.empty:
        return float("nan")
    paying_at_end = set(active_on(paid, month_end(month))["organization_id"])
    return (~at_start["organization_id"].isin(paying_at_end)).mean()


def mrr_by_org(periods: pd.DataFrame, d: date) -> pd.Series:
    return active_on(periods, d).groupby("organization_id")["mrr"].sum()


def month_index(d: date) -> int:
    return MONTHS.index(d.replace(day=1))


# --- Story 1: Starter price increase ------------------------------------------

def test_starter_churn_doubles_for_three_months_after_price_change(paid):
    change = month_index(CFG.price_change_date)
    rates = [logo_churn_rate(paid, m, ["starter"]) for m in MONTHS]
    before = sum(rates[change - 6:change]) / 6  # the six months before the change month
    after = sum(rates[change + 1:change + 4]) / 3  # the three full months after it
    assert after >= 1.7 * before


def test_starter_churn_settles_after_the_spike(paid):
    change = month_index(CFG.price_change_date)
    rates = [logo_churn_rate(paid, m, ["starter"]) for m in MONTHS]
    after = sum(rates[change + 1:change + 4]) / 3
    settled = sum(rates[change + 4:]) / len(rates[change + 4:])
    assert settled < 0.75 * after


def test_other_plans_do_not_spike(paid):
    # Pro and Enterprise churn so rarely that a ratio of two tiny rates is noise;
    # compare the increase in percentage points instead.
    change = month_index(CFG.price_change_date)

    def increase(plans):
        rates = [logo_churn_rate(paid, m, plans) for m in MONTHS]
        return sum(rates[change + 1:change + 4]) / 3 - sum(rates[change - 6:change]) / 6

    starter = increase(["starter"])
    others = increase(["pro", "enterprise"])
    assert others < 0.5 * starter


# --- Story 2: paid ads customers leave early ----------------------------------

def early_churn_share(paid: pd.DataFrame, months: int = 6) -> pd.Series:
    """Share of customers of each channel who churned within `months` of first paying."""
    first = paid.groupby("organization_id").agg(
        first_paid=("start_date", "min"), channel=("acquisition_channel", "first")
    )
    first = first[first["first_paid"] <= add_months(CFG.end_month, -months)]  # fully observed
    first_churn = paid[paid["end_reason"] == "churned"].groupby("organization_id")["end_date"].min()
    first["churned_early"] = [
        org in first_churn.index and first_churn[org] < add_months(start, months)
        for org, start in zip(first.index, first["first_paid"])
    ]
    return first.groupby("channel")["churned_early"].mean()


def test_paid_ads_early_churn_is_about_double_organic(paid):
    share = early_churn_share(paid)
    ratio = share["paid_ads"] / share["organic"]
    assert 1.6 <= ratio <= 3.0


def test_paid_ads_gap_closes_after_six_months(paid):
    # Customers who survive the first 6 months churn at a similar pace afterwards.
    survivors = paid.copy()
    first_paid = survivors.groupby("organization_id")["start_date"].transform("min")
    later = survivors[
        (survivors["end_reason"] == "churned")
        & (survivors["end_date"] >= first_paid.map(lambda d: add_months(d, 6)))
    ]
    customers = survivors.groupby("acquisition_channel")["organization_id"].nunique()
    late_churn = later.groupby("acquisition_channel")["organization_id"].nunique() / customers
    assert late_churn["paid_ads"] / late_churn["organic"] < 1.6


# --- Story 3: Enterprise expansion drives NRR above 100% ----------------------

def nrr_12m(periods: pd.DataFrame) -> tuple[float, float]:
    """(NRR, logo retention) of customers paying 12 months before the window end."""
    base_day = month_end(add_months(CFG.end_month, -12))
    base = mrr_by_org(periods, base_day)
    now = mrr_by_org(periods, CFG.window_end).reindex(base.index).fillna(0)
    return now.sum() / base.sum(), (now > 0).mean()


def test_nrr_above_100_despite_logo_churn(paid):
    nrr, logo_retention = nrr_12m(paid)
    assert nrr > 1.0
    assert logo_retention < 0.9


def test_enterprise_expansion_is_the_driver(paid):
    base_day = month_end(add_months(CFG.end_month, -12))
    enterprise_ids = active_on(paid, base_day).query("plan_id == 'enterprise'")["organization_id"]
    enterprise_nrr, _ = nrr_12m(paid[paid["organization_id"].isin(enterprise_ids)])
    others_nrr, _ = nrr_12m(paid[~paid["organization_id"].isin(enterprise_ids)])
    assert enterprise_nrr > 1.05
    assert enterprise_nrr > others_nrr + 0.05


def test_enterprise_seats_grow(paid):
    enterprise = paid[paid["plan_id"] == "enterprise"]
    seats_changes = enterprise[enterprise["end_reason"] == "seats_changed"]
    added = removed = 0
    for row in seats_changes.itertuples():
        nxt = enterprise[(enterprise["organization_id"] == row.organization_id)
                         & (enterprise["start_date"] == row.end_date)]
        delta = int(nxt["seats"].iloc[0]) - row.seats
        added, removed = added + max(delta, 0), removed + max(-delta, 0)
    assert added > 3 * removed


# --- Story 4: usage decline anticipates churn ---------------------------------

def test_activity_fades_before_churn(tables, paid):
    events = tables["product_events"]
    churns = paid[paid["end_reason"] == "churned"][["organization_id", "end_date"]]
    x = events.merge(churns, on="organization_id")
    x["weeks_before"] = (pd.to_datetime(x["end_date"]) - pd.to_datetime(x["week_start"])).dt.days // 7
    by_week = x[(x["weeks_before"] >= 0) & (x["weeks_before"] <= 15)].groupby("weeks_before")["active_users"].mean()
    baseline = by_week.loc[11:15].mean()
    assert by_week.loc[0:1].mean() < 0.5 * baseline  # last two weeks: less than half
    assert by_week.loc[4:5].mean() < 0.85 * baseline  # already falling a month earlier
    assert by_week.loc[11:15].std() < 0.1 * baseline  # flat before the fade starts


def test_some_current_customers_are_fading(tables, paid):
    # Customers who churn just after the window already fade inside it. Same
    # windows as dim_organizations.usage_trend, for customers paying at the end.
    paying = active_on(paid, CFG.window_end)["organization_id"]
    events = tables["product_events"][tables["product_events"]["organization_id"].isin(paying)]
    last = events["week_start"].max()
    recent = events[events["week_start"] > last - timedelta(weeks=4)]
    prior = events[(events["week_start"] <= last - timedelta(weeks=4))
                   & (events["week_start"] > last - timedelta(weeks=12))]
    ratio = (recent.groupby("organization_id")["active_users"].mean()
             / prior.groupby("organization_id")["active_users"].mean()).dropna()
    fading_share = (ratio < 0.6).mean()
    assert 0.02 <= fading_share <= 0.20


# --- Story 5: seasonality of new signups --------------------------------------

def test_signup_seasonality(tables):
    signups = pd.to_datetime(tables["organizations"]["signup_date"])
    by_month = signups.groupby([signups.dt.year, signups.dt.month]).size()
    for year in (2025, 2026):
        assert by_month[(year, 3)] > 1.15 * (by_month[(year, 2)] + by_month[(year, 4)]) / 2
    # December and January against the two months on each side of them.
    for dec_year in (2024, 2025):
        winter = (by_month[(dec_year, 12)] + by_month[(dec_year + 1, 1)]) / 2
        around = [(dec_year, 10), (dec_year, 11), (dec_year + 1, 2), (dec_year + 1, 3)]
        assert winter < 0.8 * sum(by_month[k] for k in around) / 4, dec_year


# --- Background trends --------------------------------------------------------

def test_mrr_grows_and_decelerates(paid):
    mrr = pd.Series([mrr_by_org(paid, month_end(m)).sum() for m in MONTHS])
    growth = mrr.pct_change()
    assert mrr.iloc[-1] > mrr.iloc[12] > mrr.iloc[0]
    assert growth.iloc[-6:].mean() < 0.6 * growth.iloc[6:12].mean()


def test_some_customers_reactivate(paid):
    ordered = paid.sort_values(["organization_id", "start_date"])
    after_churn = ordered.groupby("organization_id")["end_reason"].shift(1) == "churned"
    reactivations = after_churn.sum()
    churned_orgs = paid.loc[paid["end_reason"] == "churned", "organization_id"].nunique()
    assert 0 < reactivations < 0.2 * churned_orgs
