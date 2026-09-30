"""The committed agent context must match dbt's marts documentation (no BigQuery needed)."""
from api.agent import context

FIX = "Run `python -m api.agent.context` to regenerate it."


def test_every_documented_mart_has_a_type_snapshot():
    documented = {model["name"] for model in context.load_models()}
    assert documented == set(context.load_schema()["tables"]), FIX


def test_documented_columns_match_the_warehouse_columns():
    tables = context.load_schema()["tables"]
    for model in context.load_models():
        documented = [column["name"] for column in model["columns"]]
        assert documented == list(tables[model["name"]]), f"{model['name']}: {FIX}"


def test_every_model_and_column_has_a_description():
    for model in context.load_models():
        assert model["description"], model["name"]
        for column in model["columns"]:
            assert column["description"], f"{model['name']}.{column['name']}"


def test_committed_context_is_up_to_date():
    expected = context.render(context.load_models(), context.load_schema())
    assert context.CONTEXT_MD.read_text(encoding="utf-8") == expected, FIX


def test_allowlist_is_the_marts():
    schema = context.load_schema()
    prefix = f"{schema['project']}.{schema['dataset']}."
    assert context.allowed_tables() == {
        prefix + name for name in [
            "kpi_summary", "fct_mrr_monthly", "fct_mrr_movements", "fct_churn",
            "fct_retention_cohorts", "fct_unit_economics", "dim_organizations", "dim_plans",
        ]
    }
