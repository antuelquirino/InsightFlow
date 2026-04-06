import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery

PROJECT_ID = "insightflow-analytics-489617"
DATASET = "raw"

def get_bq_client():
    # 4 espacios aquí
    if "gcp_service_account" in st.secrets:
        # 8 espacios aquí
        info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=credentials, project=PROJECT_ID)
    else:
        # 8 espacios aquí
        return bigquery.Client(project=PROJECT_ID)

def run_query(query):

    client = get_bq_client()

    query_job = client.query(query)

    df = query_job.to_dataframe()

    return df


def get_schema():

    client = get_bq_client()

    dataset_ref = client.dataset(DATASET, project=PROJECT_ID)

    tables = client.list_tables(dataset_ref)

    schema_text = ""

    for table in tables:

        table_ref = dataset_ref.table(table.table_id)

        table_obj = client.get_table(table_ref)

        schema_text += f"\nTable {DATASET}.{table.table_id}\n"

        for field in table_obj.schema:

            schema_text += f"- {field.name}\n"

    return schema_text
