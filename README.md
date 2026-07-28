# InsightFlow: AI-Powered SaaS Analytics Platform

InsightFlow is an end-to-end data platform that simulates, processes, and analyzes SaaS business data using a modern data stack. It combines automated data pipelines, cloud data warehousing, transformation with dbt, and an AI-powered analytics interface that enables natural language querying over business metrics.

**Live Application:** [insightflow-agent2.streamlit.app](https://insightflow-agent2.streamlit.app/)

## Architecture Overview

The project follows a modular and production-oriented architecture based on the Modern Data Stack:

**Data Generation & Ingestion**
Custom Python scripts generate realistic SaaS data (organizations, users, subscriptions, product events) using synthetic data techniques. The pipeline supports both full refresh and incremental data loading.

**Orchestration & Automation**
The pipeline runs on a daily schedule via GitHub Actions, which triggers a Prefect flow (`orchestrator.py`). Prefect coordinates the sequence of tasks — data generation, ingestion, and dbt transformation — and handles retries and logging within each run.

**Data Warehouse**
Google BigQuery is used as the centralized data warehouse, optimized with partitioning and clustering for performance and cost efficiency.

**Data Transformation (dbt)**
dbt structures the data into layered models:
- **Staging** — Cleaned and standardized data
- **Marts (Core)** — Fact and dimension tables
- **Marts (KPI)** — Business-ready metrics such as MRR, churn rate, and active companies

**AI Analytics Layer**
A Streamlit application integrates with the OpenAI API to allow users to query the data using natural language. The system translates user questions into SQL queries and returns results, charts, and insights.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Data Warehouse | Google BigQuery |
| Transformation | dbt (dbt-bigquery) |
| Orchestration | GitHub Actions + Prefect |
| AI / LLM | OpenAI API |
| Frontend | Streamlit |
| Data Generation | Faker (Synthetic Data) |

## Project Structure

```
.
├── .github/workflows/      # CI/CD pipelines (scheduled data runs)
├── agent/                  # Streamlit app and AI agent logic
│   ├── app.py               # UI entry point
│   ├── agent.py              # LLM + SQL generation logic
│   └── bq_client.py           # BigQuery client wrapper
├── data_generation/        # Synthetic data generation & ingestion
├── dbt_insightflow/        # dbt project
│   ├── models/               # Staging, marts, and KPI models
│   ├── profiles.yml           # dbt connection profiles
│   └── dbt_project.yml        # dbt configuration
├── requirements.txt        # Project dependencies
└── orchestrator.py         # Prefect flow / pipeline execution
```

## Data Model

The transformation layer is organized into three levels:

- **Staging** (`dbt_staging`) — Cleaned versions of raw tables with standardized formats and data validation.
- **Core Marts** (`dbt_marts`) — `fact_product_events` · `fact_subscriptions` · `fact_mrr` · `dim_organizations`
- **KPI Layer** (`dbt_marts`) — `kpi_mrr_growth` · `kpi_churn_rate` · `kpi_active_companies`

This structure separates raw ingestion, business logic, and analytics consumption. Data quality is enforced with dbt data tests across all layers.

## Key Features

**Automated Data Pipeline**
Daily data generation and ingestion fully automated via GitHub Actions and Prefect.

**Incremental Processing**
Efficient incremental loading strategy to simulate real SaaS data growth while avoiding duplication.

**Production-Ready dbt Models**
Well-structured transformations with testing, modular design, and clear separation of concerns.

**Natural Language Querying**
Users can ask business questions (e.g., "What is our MRR growth?"), and the system generates and executes SQL queries automatically.

**AI-Generated Insights**
Query results are enriched with automatically generated business insights.

## Getting Started

### Prerequisites
- Google Cloud Project with BigQuery enabled
- Service Account with appropriate permissions
- OpenAI API Key

### 1. Environment Configuration

Configure credentials using Streamlit secrets or a local `.env` file:

```
OPENAI_API_KEY=your_openai_key

[gcp_service_account]
type = "service_account"
project_id = "your_project_id"
...
```

### 2. Installation

```bash
pip install -r requirements.txt
```

### 3. Run Data Pipeline

```bash
python orchestrator.py
```

Or rely on scheduled execution via GitHub Actions.

### 4. Launch AI Interface

```bash
streamlit run agent/app.py
```

## CI/CD

The project includes automated workflows using GitHub Actions that:
- Run the data generation pipeline
- Load data into BigQuery
- Execute dbt transformations
- Keep the dataset updated daily

## Use Cases

- SaaS analytics simulation and prototyping
- Demonstration of modern data stack architecture
- AI-powered business intelligence interface
- Portfolio project for data engineering / analytics engineering roles

## License

This project is licensed under the MIT License.

---

**Author:** Antuel Quirino
