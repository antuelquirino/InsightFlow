"""The agent's knowledge of the marts, generated from dbt's documentation.

    python -m api.agent.context      # regenerate after changing the marts or their .yml

Reads model and column descriptions (and accepted values) from the marts'
schema.yml, and column types plus the months covered from BigQuery. Writes:

- marts_schema.json: types and coverage snapshot; also the validator's allowlist.
- marts_context.md: the text the LLM receives.

Both files are committed, so the API needs neither dbt nor extra queries at run
time. tests/api/test_context.py fails when they fall out of sync with the .yml.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MARTS_YML = REPO_ROOT / "dbt_insightflow" / "models" / "marts" / "schema.yml"
AGENT_DIR = Path(__file__).resolve().parent
SCHEMA_JSON = AGENT_DIR / "marts_schema.json"
CONTEXT_MD = AGENT_DIR / "marts_context.md"

CONVENTIONS = """\
Conventions for every table:
- Month columns hold the first day of the month; values are as of the month end.
  To match a date (such as a price change) to a month row, use DATE_TRUNC(date, MONTH).
- Money is USD. Rates and ratios are fractions (0.05 = 5%), never percentages.
- A paying customer is an organization with a paid (non-trial) subscription.
- The company launched with the data window, so the first months have very few
  customers and noisy rates.
- Always reference tables with their full name, including project and dataset."""


def load_models(path: Path = MARTS_YML) -> list[dict]:
    """Model name, description and columns (with accepted values) from schema.yml."""
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    models = []
    for model in spec["models"]:
        columns = []
        for column in model.get("columns", []):
            accepted = None
            for test in column.get("data_tests", []):
                if isinstance(test, dict) and "accepted_values" in test:
                    accepted = test["accepted_values"]["arguments"]["values"]
            columns.append({
                "name": column["name"],
                "description": " ".join(column.get("description", "").split()),
                "accepted_values": accepted,
            })
        models.append({
            "name": model["name"],
            "description": " ".join(model.get("description", "").split()),
            "columns": columns,
        })
    return models


def load_schema(path: Path = SCHEMA_JSON) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_schema(models: list[dict]) -> dict:
    """Column types and months covered, read from BigQuery."""
    from api.bigquery import MartsClient
    from api.settings import Settings

    settings = Settings()
    marts = MartsClient(settings)
    names = [model["name"] for model in models]
    columns = marts.query(
        f"""
        select table_name, column_name, data_type
        from `{settings.gcp_project}.{settings.marts_dataset}`.INFORMATION_SCHEMA.COLUMNS
        where table_name in unnest(@tables)
        order by table_name, ordinal_position
        """,
        {"tables": names},
        cache=False,
    )
    window = marts.query(
        f"select min(month) as first_month, max(month) as last_month from {settings.marts}.kpi_summary",
        cache=False,
    )[0]
    tables: dict[str, dict[str, str]] = {name: {} for name in names}
    for row in columns:
        tables[row["table_name"]][row["column_name"]] = row["data_type"]
    return {
        "project": settings.gcp_project,
        "dataset": settings.marts_dataset,
        "first_month": window["first_month"].isoformat(),
        "last_month": window["last_month"].isoformat(),
        "tables": tables,
    }


def render(models: list[dict], schema: dict) -> str:
    prefix = f"{schema['project']}.{schema['dataset']}"
    lines = [
        "# InsightFlow marts",
        "",
        "BigQuery tables describing InsightFlow, a B2B SaaS company. Data covers "
        f"{schema['first_month'][:7]} to {schema['last_month'][:7]}; the latest month is "
        f"{schema['last_month'][:7]}.",
        "",
        CONVENTIONS,
    ]
    for model in models:
        types = schema["tables"][model["name"]]
        lines += ["", f"## `{prefix}.{model['name']}`", "", model["description"], "", "Columns:"]
        for column in model["columns"]:
            line = f"- {column['name']} ({types[column['name']]}): {column['description']}"
            if column["accepted_values"]:
                line += " Values: " + ", ".join(f"'{v}'" for v in column["accepted_values"]) + "."
            lines.append(line)
    return "\n".join(lines) + "\n"


@lru_cache
def marts_context() -> str:
    return CONTEXT_MD.read_text(encoding="utf-8")


@lru_cache
def allowed_tables() -> frozenset[str]:
    """Fully qualified names (project.dataset.table, lowercase) the agent may query."""
    schema = load_schema()
    return frozenset(f"{schema['project']}.{schema['dataset']}.{name}".lower() for name in schema["tables"])


def main() -> None:
    models = load_models()
    schema = fetch_schema(models)
    SCHEMA_JSON.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    CONTEXT_MD.write_text(render(models, schema), encoding="utf-8")
    print(f"Wrote {SCHEMA_JSON.name} and {CONTEXT_MD.name} ({len(models)} tables)")


if __name__ == "__main__":
    main()
