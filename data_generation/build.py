"""Generate the full synthetic history and load it into BigQuery.

    python -m data_generation.build                  # generate, write Parquet, load to raw
    python -m data_generation.build --dry-run        # generate and write Parquet only
    python -m data_generation.build --end-month 2026-08 --seed 42

The same seed and end month always produce the same data.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from data_generation.config import DEFAULT_SEED, BuildConfig
from data_generation.dates import last_complete_month
from data_generation.tables import generate

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="write local Parquet files only; skip BigQuery")
    parser.add_argument(
        "--end-month",
        type=lambda s: datetime.strptime(s, "%Y-%m").date(),
        default=last_complete_month(date.today()),
        help="last month of the 24-month window, YYYY-MM (default: last complete month)",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    cfg = BuildConfig(seed=args.seed, end_month=args.end_month)
    print(f"Window {cfg.start_month:%Y-%m} to {cfg.end_month:%Y-%m}, seed {cfg.seed}, "
          f"Starter price change on {cfg.price_change_date}")

    tables = generate(cfg)
    _print_summary(cfg, tables)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(args.output_dir / f"{name}.parquet", index=False)
    print(f"Parquet files written to {args.output_dir}")

    if args.dry_run:
        print("Dry run: BigQuery not touched.")
        return
    # Imported here so --dry-run works without the BigQuery client or credentials.
    from data_generation.loader import load_raw_tables

    print("Loading to BigQuery (full refresh)...")
    load_raw_tables(tables)
    print("Done.")


def _print_summary(cfg: BuildConfig, tables: dict[str, pd.DataFrame]) -> None:
    for name, df in tables.items():
        print(f"  {name:<16} {len(df):>7,} rows")
    subs = tables["subscriptions"]
    paying = subs[~subs["is_trial"] & subs["end_date"].isna()]
    print(f"  paying customers at {cfg.window_end}: {len(paying):,}, "
          f"MRR ${paying['mrr'].sum():,.0f}")


if __name__ == "__main__":
    main()
