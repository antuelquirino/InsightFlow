"""Full-refresh load of the raw tables into BigQuery."""
from __future__ import annotations

import pandas as pd
from google.cloud import bigquery

from data_generation.config import BQ_LOCATION, DATASET_RAW, PROJECT_ID
from data_generation.schemas import RAW_TABLES


def load_raw_tables(tables: dict[str, pd.DataFrame], project: str = PROJECT_ID) -> None:
    """Replace every raw table (WRITE_TRUNCATE). Any failed load raises."""
    client = bigquery.Client(project=project, location=BQ_LOCATION)
    dataset = bigquery.Dataset(f"{project}.{DATASET_RAW}")
    dataset.location = BQ_LOCATION
    client.create_dataset(dataset, exists_ok=True)

    for name, df in tables.items():
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            schema=[
                bigquery.SchemaField(column, field_type, mode="REQUIRED" if required else "NULLABLE")
                for column, field_type, required in RAW_TABLES[name]
            ],
        )
        table_id = f"{project}.{DATASET_RAW}.{name}"
        client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
        print(f"  loaded {len(df):>7,} rows into {table_id}")
