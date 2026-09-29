"""Column order and BigQuery types of every raw table.

(column, BigQuery type, required). The loader turns these into explicit load
schemas, so nothing depends on BigQuery's type autodetection. Money is FLOAT64
here and cast to NUMERIC in staging.
"""
from __future__ import annotations

RAW_TABLES: dict[str, list[tuple[str, str, bool]]] = {
    "organizations": [
        ("organization_id", "STRING", True),
        ("name", "STRING", True),
        ("industry", "STRING", True),
        ("country", "STRING", True),
        ("company_size", "STRING", True),
        ("acquisition_channel", "STRING", True),
        ("signup_date", "DATE", True),
    ],
    "plans": [
        ("plan_id", "STRING", True),
        ("plan_name", "STRING", True),
        ("monthly_price_per_seat", "FLOAT64", True),
        ("valid_from", "DATE", True),
        ("valid_to", "DATE", False),
    ],
    "subscriptions": [
        ("subscription_id", "STRING", True),
        ("organization_id", "STRING", True),
        ("plan_id", "STRING", True),
        ("is_trial", "BOOL", True),
        ("seats", "INT64", True),
        ("monthly_price_per_seat", "FLOAT64", True),
        ("mrr", "FLOAT64", True),
        ("start_date", "DATE", True),
        ("end_date", "DATE", False),
        ("end_reason", "STRING", False),
    ],
    "invoices": [
        ("invoice_id", "STRING", True),
        ("organization_id", "STRING", True),
        ("subscription_id", "STRING", True),
        ("invoice_date", "DATE", True),
        ("amount", "FLOAT64", True),
        ("status", "STRING", True),
    ],
    "product_events": [
        ("organization_id", "STRING", True),
        ("week_start", "DATE", True),
        ("active_users", "INT64", True),
        ("logins", "INT64", True),
        ("dashboards_viewed", "INT64", True),
        ("queries_run", "INT64", True),
        ("reports_exported", "INT64", True),
    ],
    "marketing_spend": [
        ("month", "DATE", True),
        ("acquisition_channel", "STRING", True),
        ("spend", "FLOAT64", True),
    ],
}


def columns(table: str) -> list[str]:
    return [name for name, _, _ in RAW_TABLES[table]]
