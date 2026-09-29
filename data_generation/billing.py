"""Monthly invoices derived from paid subscription periods."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data_generation import config as C
from data_generation.config import BuildConfig
from data_generation.dates import add_months
from data_generation.simulation import Organization, Period


def build_invoices(cfg: BuildConfig, organizations: list[Organization]) -> pd.DataFrame:
    """One invoice per month of paid service, billed on the day the service started.

    A "spell" is an uninterrupted run of paid periods (plan, seat and price changes
    do not interrupt it; churn does). Each spell bills on its start day, clamped to
    the 28th, for the MRR of the period active on that day.
    """
    rng = np.random.default_rng([cfg.seed, 1])
    rows = []
    for org in organizations:
        for spell in _paid_spells(org):
            start, end = spell[0].start_date, spell[-1].end_date
            anchor = min(start.day, 28)
            billing_day, n = start, 0
            while billing_day <= cfg.window_end and (end is None or billing_day < end):
                period = next(p for p in spell if p.is_active_on(billing_day))
                rows.append(
                    {
                        "organization_id": org.organization_id,
                        "subscription_id": period.subscription_id,
                        "invoice_date": billing_day,
                        "amount": period.mrr,
                        "status": _status(rng, period.plan_id),
                    }
                )
                n += 1
                billing_day = add_months(start.replace(day=anchor), n)

    invoices = pd.DataFrame(rows).sort_values(["invoice_date", "organization_id"], ignore_index=True)
    invoices.insert(0, "invoice_id", [f"inv_{i:07d}" for i in range(1, len(invoices) + 1)])
    return invoices


def _paid_spells(org: Organization) -> list[list[Period]]:
    spells: list[list[Period]] = []
    for period in org.periods:
        if period.is_trial:
            continue
        previous = spells[-1][-1] if spells else None
        if previous is not None and previous.end_date == period.start_date and previous.end_reason != "churned":
            spells[-1].append(period)
        else:
            spells.append([period])
    return spells


def _status(rng: np.random.Generator, plan_id: str) -> str:
    u = rng.random()
    if u < C.INVOICE_FAILED_RATE[plan_id]:
        return "failed"
    if u < C.INVOICE_FAILED_RATE[plan_id] + C.INVOICE_REFUNDED_RATE:
        return "refunded"
    return "paid"
