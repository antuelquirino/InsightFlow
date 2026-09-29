"""Everything that shapes the synthetic data lives here.

Rates are monthly probabilities unless stated otherwise. The parameters marked
"story" are the levers behind docs/data-stories.md; change them together with
that document and the story tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from data_generation.dates import add_months, month_end

# --- BigQuery -----------------------------------------------------------------
PROJECT_ID = "insightflow-analytics-489617"
DATASET_RAW = "raw"
BQ_LOCATION = "EU"

# --- Time window --------------------------------------------------------------
DEFAULT_SEED = 42
HISTORY_MONTHS = 24
# The simulation runs past the window so customers about to churn right after
# it already show declining usage inside it. Nothing after the window is emitted.
LOOKAHEAD_MONTHS = 3
TRIAL_DAYS = 14


@dataclass(frozen=True)
class BuildConfig:
    seed: int
    end_month: date  # first day of the last month in the window

    @property
    def start_month(self) -> date:
        return add_months(self.end_month, -(HISTORY_MONTHS - 1))

    @property
    def window_end(self) -> date:
        return month_end(self.end_month)

    @property
    def sim_end_month(self) -> date:
        return add_months(self.end_month, LOOKAHEAD_MONTHS)

    @property
    def price_change_date(self) -> date:
        # Story 1: mid-month 15 of the window.
        return add_months(self.start_month, STARTER_PRICE_CHANGE_MONTH - 1).replace(day=15)


# --- Plans (price per seat per month, USD) ------------------------------------
PLANS = {
    "starter": {"name": "Starter", "price": 15.0, "min_seats": 1},
    "pro": {"name": "Pro", "price": 39.0, "min_seats": 3},
    "enterprise": {"name": "Enterprise", "price": 79.0, "min_seats": 10},
}
PLAN_ORDER = ["starter", "pro", "enterprise"]

# Story 1: Starter price increase.
STARTER_PRICE_CHANGE_MONTH = 15  # 1-based month of the window
STARTER_NEW_PRICE = 19.0

# --- Organizations ------------------------------------------------------------
INDUSTRIES = {
    "Software": 0.24, "Fintech": 0.14, "E-commerce": 0.14, "Healthcare": 0.10,
    "Logistics": 0.10, "Education": 0.09, "Marketing": 0.10, "Manufacturing": 0.09,
}
COUNTRIES = {
    "US": 0.38, "GB": 0.12, "DE": 0.09, "CA": 0.07, "FR": 0.05, "NL": 0.05,
    "ES": 0.05, "AU": 0.05, "BR": 0.05, "MX": 0.04, "SE": 0.03, "IE": 0.02,
}
COMPANY_SIZES = ["small", "medium", "large"]  # 1-50, 51-500, 500+ employees
SIZE_MIX_BY_CHANNEL = {
    "organic": [0.58, 0.32, 0.10],
    "paid_ads": [0.64, 0.30, 0.06],
    "partner": [0.40, 0.42, 0.18],
    "outbound": [0.18, 0.45, 0.37],
}
PLAN_MIX_BY_SIZE = {
    "small": [0.78, 0.20, 0.02],
    "medium": [0.36, 0.49, 0.15],
    "large": [0.05, 0.40, 0.55],
}
# (median seats, lognormal sigma, max seats); clipped below at the plan's min_seats.
SEATS_BY_PLAN = {
    "starter": (3, 0.45, 5),
    "pro": (8, 0.50, 30),
    "enterprise": (22, 0.45, 120),
}

# --- Acquisition --------------------------------------------------------------
CHANNELS = ["organic", "paid_ads", "partner", "outbound"]
# Channel mix of new trials at the start and end of the window (paid ads ramps up).
CHANNEL_MIX_START = [0.40, 0.24, 0.17, 0.19]
CHANNEL_MIX_END = [0.30, 0.40, 0.14, 0.16]

# New trials per month: ramps from BASE toward BASE + GROWTH (growth that slows down).
SIGNUPS_BASE = 30
SIGNUPS_GROWTH = 33
SIGNUPS_RAMP_MONTHS = 9
# Story 5: seasonality of new trials by calendar month.
SEASONALITY = {
    1: 0.70, 2: 0.95, 3: 1.45, 4: 1.05, 5: 1.02, 6: 0.97,
    7: 0.90, 8: 0.88, 9: 1.05, 10: 1.08, 11: 1.00, 12: 0.62,
}
TRIAL_CONVERSION = {"organic": 0.58, "paid_ads": 0.46, "partner": 0.64, "outbound": 0.55}

# --- Lifecycle (monthly probabilities for paying customers) -------------------
CHURN_BASE = {"starter": 0.030, "pro": 0.019, "enterprise": 0.009}
# Story 2: paid ads customers churn about twice as fast in their first months.
CHANNEL_CHURN_MULTIPLIER = {"organic": 1.0, "paid_ads": 1.15, "partner": 0.9, "outbound": 1.0}
PAID_ADS_EARLY_MONTHS = 6
PAID_ADS_EARLY_CHURN_MULTIPLIER = 2.3
# Story 1: Starter churn after the price change.
# Applies from the change date to the end of the third full month after it.
PRICE_CHANGE_CHURN_MULTIPLIER = 2.3
PRICE_CHANGE_EFFECT_MONTHS = 3

# Seat changes: (probability, min share, max share) of current seats.
# Story 3: Enterprise keeps adding seats.
EXPANSION = {
    "starter": (0.025, 0.2, 0.6),
    "pro": (0.060, 0.10, 0.30),
    "enterprise": (0.300, 0.04, 0.12),
}
CONTRACTION = {
    "starter": (0.015, 0.2, 0.5),
    "pro": (0.030, 0.10, 0.25),
    "enterprise": (0.020, 0.05, 0.12),
}
UPGRADE = {"starter": 0.012, "pro": 0.006}
DOWNGRADE = {"pro": 0.007, "enterprise": 0.003}
# Churned customers who come back, within this many months of leaving.
REACTIVATION_RATE = 0.02
REACTIVATION_WINDOW_MONTHS = 12

# --- Billing ------------------------------------------------------------------
INVOICE_FAILED_RATE = {"starter": 0.05, "pro": 0.03, "enterprise": 0.015}
INVOICE_REFUNDED_RATE = 0.01

# --- Marketing spend (USD per month): start and end of window -----------------
SPEND_START = {"organic": 2000, "paid_ads": 9000, "partner": 1500, "outbound": 6000}
SPEND_END = {"organic": 3500, "paid_ads": 24000, "partner": 2500, "outbound": 9500}
PARTNER_COMMISSION_PER_CONVERSION = 180  # on top of the partner base spend

# --- Product activity (weekly, per organization) ------------------------------
# Story 4: usage fades before a customer churns.
PRE_CHURN_DECLINE_WEEKS = (6, 10)  # inclusive range, sampled per churn
PRE_CHURN_FLOOR = 0.25  # activity multiplier reached just before churning
TRIAL_ACTIVITY = {"converted": 0.85, "expired": 0.35}
HEALTHY_DIP_RATE = 0.02  # weekly chance of a one-week dip for any customer
HOLIDAY_WEEKS = {(12, 25): 0.55, (1, 1): 0.75}  # (month, day) inside the week -> multiplier
