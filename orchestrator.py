from prefect import flow, task
import subprocess
import os
import sys

# --- PATH CONFIGURATION ---
# Getting the current working directory to ensure relative paths work in any environment
BASE_DIR = os.getcwd()

# Path to the data ingestion script
DATA_GEN_SCRIPT = os.path.join(BASE_DIR, "data_generation", "automation_daily.py")

# Path to the dbt project folder
DBT_PROJECT_DIR = os.path.join(BASE_DIR, "dbt_insightflow")

@task(name="Generate Daily SaaS Data", retries=2, retry_delay_seconds=60)
def run_generator():
    """
    Task 1: Executes the daily data generation and ingestion script.
    This script populates the raw layer in BigQuery.
    """
    print(f"🚀 Starting Data Generation Script at: {DATA_GEN_SCRIPT}")
    
    # Safety check: Verify if the script exists before execution
    if not os.path.exists(DATA_GEN_SCRIPT):
        raise FileNotFoundError(f"❌ Script not found: {DATA_GEN_SCRIPT}")

    # Executes the Python script using the current environment's executable
    try:
        result = subprocess.run(
            [sys.executable, DATA_GEN_SCRIPT], 
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return "Ingestion successful: Raw data loaded to BigQuery."
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during data generation: {e.stderr}")
        raise

@task(name="Execute dbt Models", retries=1)
def run_dbt_transformations():
    """
    Task 2: Runs dbt transformations to update the Analytics Marts.
    Only runs if Task 1 completes successfully.
    """
    print(f"Transformation: Running 'dbt run' in {DBT_PROJECT_DIR}")
    
    # Safety check: Verify if the dbt project folder exists
    if not os.path.exists(DBT_PROJECT_DIR):
        raise FileNotFoundError(f"❌ dbt project directory not found: {DBT_PROJECT_DIR}")

    # Executes dbt run. Ensure your profiles.yml is accessible.
    try:
        result = subprocess.run(
            ["dbt", "run", "--profiles-dir", "."], 
            check=True, 
            cwd=DBT_PROJECT_DIR,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return "Transformation successful: dbt Marts updated."
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during dbt execution: {e.stderr}")
        raise

@flow(name="InsightFlow End-to-End Pipeline", log_prints=True)
def insightflow_pipeline():
    """
    Main Orchestrator:
    1. Ingests raw data from Python source.
    2. Transforms data into Business Metrics using dbt.
    """
    print("--- [PIPELINE START] Starting Ingestion & Transformation ---")
    
    # Step 1: Ingestion
    ingestion_result = run_generator()
    
    # Step 2: Transformation (Dependent on Step 1)
    transformation_result = run_dbt_transformations()
    
    print("--- [PIPELINE FINISHED] All tasks completed successfully ---")

if __name__ == "__main__":
    # To run this locally, simply execute: python orchestrator.py
    insightflow_pipeline()