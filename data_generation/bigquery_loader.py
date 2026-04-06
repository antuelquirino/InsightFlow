from google.cloud import bigquery
import pandas as pd
from config import PROJECT_ID, DATASET_RAW

client = bigquery.Client(project=PROJECT_ID)

def create_dataset():
    dataset_id = f"{PROJECT_ID}.{DATASET_RAW}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "EU"
    # exists_ok=True ensures we don't crash if it exists, but we don't need to recreate it every time
    client.create_dataset(dataset, exists_ok=True)
    print(f"INFO: Dataset {DATASET_RAW} verified or created in {PROJECT_ID}.")

def load_dataframe(df: pd.DataFrame, table_name: str, full_refresh=False):
    """
    Loads a DataFrame to BigQuery.
    If full_refresh=True, uses WRITE_TRUNCATE (overwrites existing data).
    If full_refresh=False, uses WRITE_APPEND (adds data to the table).
    """
    table_id = f"{PROJECT_ID}.{DATASET_RAW}.{table_name}"
    
    # Determine write disposition based on the refresh flag
    disposition = "WRITE_TRUNCATE" if full_refresh else "WRITE_APPEND"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=disposition,
        autodetect=True,
    )

    print(f"DEBUG: Preparing to load {len(df)} rows into {table_name}")
    print(f"DEBUG: Write disposition set to {disposition}")

    try:
        # Execute the load job
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for the job to complete
        print(f"SUCCESS: Data successfully loaded into {table_name}")
    except Exception as e:
        print(f"ERROR: Failed to load data into {table_name}. Details: {e}")