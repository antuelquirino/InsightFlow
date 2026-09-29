"""Structural invariants of the generated raw tables (stories are tested separately)."""
from datetime import date, timedelta

import pandas as pd
import pytest

from data_generation import config as C
from data_generation.config import BuildConfig
from data_generation.schemas import RAW_TABLES
from data_generation.tables import generate

CFG = BuildConfig(seed=C.DEFAULT_SEED, end_month=date(2026, 8, 1))


@pytest.fixture(scope="module")
def tables():
    return generate(CFG)


def test_window_is_24_months_ending_in_end_month():
    assert CFG.start_month == date(2024, 9, 1)
    assert CFG.window_end == date(2026, 8, 31)
    assert CFG.price_change_date == date(2025, 11, 15)


def test_same_seed_same_data(tables):
    again = generate(CFG)
    for name, df in tables.items():
        pd.testing.assert_frame_equal(df, again[name], obj=name)


def test_different_seed_different_data(tables):
    other = generate(BuildConfig(seed=C.DEFAULT_SEED + 1, end_month=CFG.end_month))
    assert not tables["subscriptions"].equals(other["subscriptions"])


def test_columns_match_schemas(tables):
    for name, df in tables.items():
        assert list(df.columns) == [column for column, _, _ in RAW_TABLES[name]], name
        required = [column for column, _, is_required in RAW_TABLES[name] if is_required]
        assert not df[required].isna().any().any(), f"nulls in required columns of {name}"


def test_primary_keys_are_unique(tables):
    keys = {
        "organizations": ["organization_id"],
        "plans": ["plan_id", "valid_from"],
        "subscriptions": ["subscription_id"],
        "invoices": ["invoice_id"],
        "product_events": ["organization_id", "week_start"],
        "marketing_spend": ["month", "acquisition_channel"],
    }
    for name, key in keys.items():
        assert not tables[name].duplicated(key).any(), name


def test_foreign_keys(tables):
    org_ids = set(tables["organizations"]["organization_id"])
    sub_ids = set(tables["subscriptions"]["subscription_id"])
    for name in ["subscriptions", "invoices", "product_events"]:
        assert set(tables[name]["organization_id"]) <= org_ids, name
    assert set(tables["invoices"]["subscription_id"]) <= sub_ids
    assert set(tables["subscriptions"]["plan_id"]) <= set(tables["plans"]["plan_id"])


def test_all_dates_inside_window(tables):
    date_columns = {
        "organizations": ["signup_date"],
        "subscriptions": ["start_date", "end_date"],
        "invoices": ["invoice_date"],
        "product_events": ["week_start"],
        "marketing_spend": ["month"],
    }
    for name, cols in date_columns.items():
        for col in cols:
            values = tables[name][col].dropna()
            assert values.max() <= CFG.window_end, f"{name}.{col}"
    assert tables["organizations"]["signup_date"].min() >= CFG.start_month


def test_accepted_values(tables):
    subs = tables["subscriptions"]
    assert set(subs["end_reason"].dropna()) <= {
        "churned", "upgraded", "downgraded", "seats_changed", "price_changed",
        "trial_converted", "trial_expired",
    }
    assert set(tables["invoices"]["status"]) == {"paid", "failed", "refunded"}
    assert set(tables["organizations"]["acquisition_channel"]) == set(C.CHANNELS)
    assert set(tables["organizations"]["company_size"]) == set(C.COMPANY_SIZES)


def test_end_reason_iff_end_date(tables):
    subs = tables["subscriptions"]
    assert (subs["end_date"].isna() == subs["end_reason"].isna()).all()


def test_periods_form_a_chain_per_organization(tables):
    subs = tables["subscriptions"].sort_values(["organization_id", "start_date", "subscription_id"])
    for _, periods in subs.groupby("organization_id"):
        rows = periods.to_dict("records")
        assert rows[0]["is_trial"], "every organization starts with a trial"
        assert not any(r["is_trial"] for r in rows[1:])
        for previous, current in zip(rows, rows[1:]):
            assert pd.notna(previous["end_date"]), "only the last period can be open"
            assert current["start_date"] >= previous["end_date"]
            if previous["end_reason"] != "churned":
                assert current["start_date"] == previous["end_date"], "non-churn changes are contiguous"
            assert current["start_date"] > previous["start_date"]


def test_trials_last_14_days_and_are_free(tables):
    trials = tables["subscriptions"][tables["subscriptions"]["is_trial"]]
    assert (trials["mrr"] == 0).all()
    ended = trials.dropna(subset=["end_date"])
    assert ((ended["end_date"] - ended["start_date"]) == timedelta(days=C.TRIAL_DAYS)).all()
    assert set(ended["end_reason"]) == {"trial_converted", "trial_expired"}


def test_mrr_is_seats_times_price_valid_at_start(tables):
    paid = tables["subscriptions"][~tables["subscriptions"]["is_trial"]]
    assert (abs(paid["mrr"] - paid["seats"] * paid["monthly_price_per_seat"]) < 0.01).all()
    plans = tables["plans"]
    for row in paid.itertuples():
        valid = plans[
            (plans["plan_id"] == row.plan_id)
            & (plans["valid_from"] <= row.start_date)
            & (plans["valid_to"].isna() | (plans["valid_to"] > row.start_date))
        ]
        assert list(valid["monthly_price_per_seat"]) == [row.monthly_price_per_seat]


def test_seats_respect_plan_minimums(tables):
    paid = tables["subscriptions"][~tables["subscriptions"]["is_trial"]]
    minimums = paid["plan_id"].map({plan: spec["min_seats"] for plan, spec in C.PLANS.items()})
    assert (paid["seats"] >= minimums).all()


def test_paying_customers_at_window_end(tables):
    subs = tables["subscriptions"]
    paying = subs[~subs["is_trial"] & subs["end_date"].isna()]
    assert 400 <= paying["organization_id"].nunique() <= 600
    assert paying["organization_id"].is_unique


def test_invoices_match_their_subscription(tables):
    invoices = tables["invoices"].merge(
        tables["subscriptions"], on=["subscription_id", "organization_id"], validate="many_to_one"
    )
    assert not invoices["is_trial"].any()
    assert (abs(invoices["amount"] - invoices["mrr"]) < 0.01).all()
    assert (invoices["invoice_date"] >= invoices["start_date"]).all()
    ended = invoices.dropna(subset=["end_date"])
    assert (ended["invoice_date"] < ended["end_date"]).all()


def test_invoice_failures_are_occasional(tables):
    failed_share = (tables["invoices"]["status"] == "failed").mean()
    assert 0.01 < failed_share < 0.08


def test_activity_only_while_subscribed(tables):
    subs = tables["subscriptions"]
    events = tables["product_events"].merge(subs, on="organization_id")
    week_end = events["week_start"] + timedelta(days=7)
    overlaps = (events["start_date"] < week_end) & (
        events["end_date"].isna() | (events["end_date"] > events["week_start"])
    )
    covered = overlaps.groupby([events["organization_id"], events["week_start"]]).any()
    assert covered.all()
    assert (tables["product_events"]["week_start"].map(date.weekday) == 0).all()


def test_marketing_spend_covers_every_month_and_channel(tables):
    spend = tables["marketing_spend"]
    assert len(spend) == C.HISTORY_MONTHS * len(C.CHANNELS)
    assert (spend["spend"] > 0).all()
