"""Weekly product activity per organization.

Activity follows seats and a per-organization engagement level, with weekly
noise, holiday dips and occasional one-week dips. Before a churn, activity
fades linearly over 6 to 10 weeks (story 4).
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from data_generation import config as C
from data_generation.config import BuildConfig
from data_generation.dates import monday_on_or_before
from data_generation.simulation import Organization, Period

# Weekly actions per active user.
LOGINS_PER_USER = 3.5
DASHBOARDS_PER_USER = 6.0
QUERIES_PER_USER = {"starter": 2.5, "pro": 4.0, "enterprise": 5.5}
EXPORTS_PER_USER = 0.6


def build_product_activity(cfg: BuildConfig, organizations: list[Organization]) -> pd.DataFrame:
    rng = np.random.default_rng([cfg.seed, 2])
    first_week = monday_on_or_before(cfg.start_month)
    last_week = monday_on_or_before(cfg.window_end - timedelta(days=6))  # complete weeks only
    rows = []
    for org in organizations:
        engagement = rng.beta(6, 2.5)
        churn_fades = _churn_fades(rng, org)
        trial_level = C.TRIAL_ACTIVITY["converted" if org.first_paid_start else "expired"]
        week = max(first_week, monday_on_or_before(org.signup_date))
        while week <= last_week:
            period = _period_in_week(org, week)
            if period is not None:
                level = trial_level if period.is_trial else 1.0
                level *= _fade(week, churn_fades) * _holiday(week)
                if rng.random() < C.HEALTHY_DIP_RATE:
                    level *= 0.6
                level *= rng.lognormal(0, 0.12)
                rows.append(_week_row(rng, org, period, week, min(engagement * level, 1.0)))
            week += timedelta(weeks=1)
    return pd.DataFrame(rows)


def _period_in_week(org: Organization, week: date) -> Period | None:
    """The latest period that overlaps the week [week, week + 7)."""
    week_end = week + timedelta(days=7)
    overlapping = [
        p for p in org.periods
        if p.start_date < week_end and (p.end_date is None or p.end_date > week)
    ]
    return overlapping[-1] if overlapping else None


def _churn_fades(rng: np.random.Generator, org: Organization) -> list[tuple[date, date]]:
    """(fade start, churn date) for every churn of the organization."""
    fades = []
    for period in org.periods:
        if period.end_reason == "churned":
            weeks = int(rng.integers(C.PRE_CHURN_DECLINE_WEEKS[0], C.PRE_CHURN_DECLINE_WEEKS[1] + 1))
            fades.append((period.end_date - timedelta(weeks=weeks), period.end_date))
    return fades


def _fade(week: date, fades: list[tuple[date, date]]) -> float:
    for start, churned_on in fades:
        if start <= week < churned_on:
            progress = (week - start).days / (churned_on - start).days
            return 1 - (1 - C.PRE_CHURN_FLOOR) * progress
    return 1.0


def _holiday(week: date) -> float:
    for (month, day), multiplier in C.HOLIDAY_WEEKS.items():
        for year in (week.year, week.year + 1):
            if week <= date(year, month, day) < week + timedelta(days=7):
                return multiplier
    return 1.0


def _week_row(rng, org: Organization, period: Period, week: date, activity: float) -> dict:
    active_users = int(rng.binomial(period.seats, activity))
    return {
        "organization_id": org.organization_id,
        "week_start": week,
        "active_users": active_users,
        "logins": int(rng.poisson(active_users * LOGINS_PER_USER)),
        "dashboards_viewed": int(rng.poisson(active_users * DASHBOARDS_PER_USER)),
        "queries_run": int(rng.poisson(active_users * QUERIES_PER_USER[period.plan_id])),
        "reports_exported": int(rng.poisson(active_users * EXPORTS_PER_USER)),
    }
