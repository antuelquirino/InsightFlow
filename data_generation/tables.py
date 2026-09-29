"""Turns the simulation into the raw tables, cut to the reporting window."""
from __future__ import annotations

import pandas as pd

from data_generation import config as C
from data_generation.activity import build_product_activity
from data_generation.billing import build_invoices
from data_generation.config import BuildConfig
from data_generation.marketing import build_marketing_spend
from data_generation.schemas import columns
from data_generation.simulation import Organization, simulate


def generate(cfg: BuildConfig) -> dict[str, pd.DataFrame]:
    organizations = simulate(cfg)
    tables = {
        "organizations": _organizations(cfg, organizations),
        "plans": _plans(cfg),
        "subscriptions": _subscriptions(cfg, organizations),
        "invoices": build_invoices(cfg, organizations),
        "product_events": build_product_activity(cfg, organizations),
        "marketing_spend": build_marketing_spend(cfg, organizations),
    }
    return {name: df[columns(name)] for name, df in tables.items()}


def _organizations(cfg: BuildConfig, organizations: list[Organization]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "organization_id": org.organization_id,
            "name": org.name,
            "industry": org.industry,
            "country": org.country,
            "company_size": org.company_size,
            "acquisition_channel": org.acquisition_channel,
            "signup_date": org.signup_date,
        }
        for org in organizations
        if org.signup_date <= cfg.window_end
    )


def _plans(cfg: BuildConfig) -> pd.DataFrame:
    rows = []
    for plan_id in C.PLAN_ORDER:
        plan = C.PLANS[plan_id]
        row = {"plan_id": plan_id, "plan_name": plan["name"], "valid_from": cfg.start_month}
        if plan_id == "starter":
            change = cfg.price_change_date
            rows.append({**row, "monthly_price_per_seat": plan["price"], "valid_to": change})
            rows.append({**row, "monthly_price_per_seat": C.STARTER_NEW_PRICE, "valid_from": change, "valid_to": None})
        else:
            rows.append({**row, "monthly_price_per_seat": plan["price"], "valid_to": None})
    return pd.DataFrame(rows)


def _subscriptions(cfg: BuildConfig, organizations: list[Organization]) -> pd.DataFrame:
    rows = []
    for org in organizations:
        for p in org.periods:
            if p.start_date > cfg.window_end:
                continue
            # Anything that ends after the window is still open as of the window end.
            ended = p.end_date is not None and p.end_date <= cfg.window_end
            rows.append(
                {
                    "subscription_id": p.subscription_id,
                    "organization_id": p.organization_id,
                    "plan_id": p.plan_id,
                    "is_trial": p.is_trial,
                    "seats": p.seats,
                    "monthly_price_per_seat": p.monthly_price_per_seat,
                    "mrr": p.mrr,
                    "start_date": p.start_date,
                    "end_date": p.end_date if ended else None,
                    "end_reason": p.end_reason if ended else None,
                }
            )
    return pd.DataFrame(rows).sort_values("subscription_id", ignore_index=True)
