from prefect import flow, task
import subprocess
import os
import sys

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.getcwd()
# Ruta exacta: Carpeta 'data_generation' -> Archivo 'automation_daily.py'
DATA_GEN_SCRIPT = os.path.join(BASE_DIR, "data_generation", "automation_daily.py")
DBT_PROJECT_DIR = os.path.join(BASE_DIR, "insightflow_dbt")

@task(name="Generate Daily SaaS Data", retries=2)
def run_generator():
    """Executes the daily data generation script"""
    print(f"🚀 Ejecutando generador en: {DATA_GEN_SCRIPT}")
    
    if not os.path.exists(DATA_GEN_SCRIPT):
        raise FileNotFoundError(f"❌ No se encontró el archivo: {DATA_GEN_SCRIPT}")

    # Ejecutamos el script
    result = subprocess.run([sys.executable, DATA_GEN_SCRIPT], check=True)
    return "Data generation completed successfully"

@task(name="Execute dbt Models", retries=1)
def run_dbt():
    """Runs dbt transformations to update BigQuery Marts"""
    print(f"Transformation: Ejecutando dbt run en {DBT_PROJECT_DIR}")
    
    if not os.path.exists(DBT_PROJECT_DIR):
        raise FileNotFoundError(f"❌ No se encontró la carpeta dbt: {DBT_PROJECT_DIR}")
        
    result = subprocess.run(["dbt", "run"], check=True, cwd=DBT_PROJECT_DIR)
    return "Marts updated successfully"

@flow(name="InsightFlow Daily Pipeline", log_prints=True)
def insightflow_pipeline():
    """Main flow to orchestrate data ingestion and transformation"""
    print("--- Pipeline Execution Started ---")
    
    # 1. Ingestion (Generador Python)
    run_generator()
    
    # 2. Transformation (dbt)
    run_dbt()
    
    print("--- Pipeline Execution Finished ---")

if __name__ == "__main__":
    insightflow_pipeline()