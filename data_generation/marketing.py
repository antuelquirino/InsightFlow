"""Monthly marketing spend per acquisition channel."""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from data_generation import config as C
from data_generation.config import BuildConfig
from data_generation.dates import add_months
from data_generation.simulation import Organization


def build_marketing_spend(cfg: BuildConfig, organizations: list[Organization]) -> pd.DataFrame:
    """Spend ramps linearly from SPEND_START to SPEND_END with ±8% noise.

    Partner spend adds a commission for each trial that converted that month.
    """
    rng = np.random.default_rng([cfg.seed, 3])
    partner_conversions = Counter(
        org.first_paid_start.replace(day=1)
        for org in organizations
        if org.acquisition_channel == "partner" and org.first_paid_start
    )
    rows = []
    for index in range(C.HISTORY_MONTHS):
        month = add_months(cfg.start_month, index)
        progress = index / (C.HISTORY_MONTHS - 1)
        for channel in C.CHANNELS:
            spend = C.SPEND_START[channel] + progress * (C.SPEND_END[channel] - C.SPEND_START[channel])
            spend *= rng.normal(1, 0.08)
            if channel == "partner":
                spend += partner_conversions[month] * C.PARTNER_COMMISSION_PER_CONVERSION
            rows.append({"month": month, "acquisition_channel": channel, "spend": round(spend, 2)})
    return pd.DataFrame(rows)
