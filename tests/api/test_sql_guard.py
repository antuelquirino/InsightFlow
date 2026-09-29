import pytest

from api.agent.sql_guard import MAX_ROWS, SqlRejected, validate

PROJECT = "insightflow-analytics-489617"
KPI = f"`{PROJECT}.dbt_marts.kpi_summary`"


@pytest.mark.parametrize("sql", [
    # Writes and DDL
    f"DELETE FROM {KPI} WHERE TRUE",
    f"DROP TABLE {KPI}",
    f"INSERT INTO {KPI} (mrr) VALUES (1)",
    f"UPDATE {KPI} SET mrr = 0 WHERE TRUE",
    f"MERGE {KPI} t USING {KPI} s ON FALSE WHEN NOT MATCHED THEN INSERT ROW",
    f"CREATE TABLE `{PROJECT}.dbt_marts.copy` AS SELECT * FROM {KPI}",
    f"TRUNCATE TABLE {KPI}",
    f"ALTER TABLE {KPI} ADD COLUMN x INT64",
    # Several statements
    f"SELECT * FROM {KPI}; DROP TABLE {KPI}",
    f"SELECT * FROM {KPI}; SELECT * FROM {KPI}",
    # Tables outside the marts allowlist
    "SELECT * FROM raw.organizations",
    f"SELECT * FROM `{PROJECT}.raw.subscriptions`",
    "SELECT * FROM dbt_staging.stg_subscriptions",
    "SELECT * FROM dbt_intermediate.int_mrr_movements",
    "SELECT * FROM `other-project.dbt_marts.kpi_summary`",
    "SELECT * FROM `bigquery-public-data.samples.shakespeare`",
    "SELECT * FROM dbt_marts.fact_mrr",  # legacy table in the same dataset
    "SELECT * FROM dbt_marts.kpi_churn_rate",
    "SELECT * FROM dbt_marts.INFORMATION_SCHEMA.TABLES",
    f"SELECT * FROM `{PROJECT}.region-eu.INFORMATION_SCHEMA.JOBS`",
    "SELECT * FROM `dbt_marts.fct_*`",
    # Disallowed tables hidden inside allowed queries
    f"SELECT * FROM {KPI} WHERE month IN (SELECT signup_date FROM raw.organizations)",
    "WITH o AS (SELECT * FROM raw.organizations) SELECT * FROM o",
    f"SELECT * FROM {KPI} UNION ALL SELECT * FROM raw.organizations",
    f"SELECT * FROM {KPI} k JOIN raw.plans p ON TRUE",
    # Scripting and table functions
    "EXECUTE IMMEDIATE 'DROP TABLE raw.organizations'",
    "DECLARE x INT64",
    "CALL dbt_marts.some_procedure()",
    "SELECT * FROM EXTERNAL_QUERY('conn', 'SELECT 1')",
    # Not a query at all
    "",
    "   ;  ",
    "SELECT FROM WHERE",
    "SELECT 1",  # reads no mart
    f"SELECT * FROM {KPI} LIMIT @n",
])
def test_rejected(sql):
    with pytest.raises(SqlRejected):
        validate(sql)


def test_rejection_message_lists_the_allowed_tables():
    with pytest.raises(SqlRejected, match="kpi_summary") as error:
        validate("SELECT * FROM raw.organizations")
    assert "raw.organizations" in str(error.value)


@pytest.mark.parametrize("sql", [
    "SELECT month, mrr FROM kpi_summary",
    "SELECT month, mrr FROM dbt_marts.kpi_summary",
    f"SELECT month, mrr FROM {KPI}",
    f"SELECT month, mrr FROM `{PROJECT}`.dbt_marts.kpi_summary",
])
def test_mart_names_are_qualified(sql):
    result = validate(sql)
    assert result.tables == (f"{PROJECT}.dbt_marts.kpi_summary",)
    assert PROJECT in result.sql


def test_accepts_ctes_joins_subqueries_and_unions():
    sql = """
        WITH starter AS (
            SELECT month, logo_churn_rate FROM fct_churn
            WHERE breakdown = 'plan' AND breakdown_value = 'starter'
        )
        SELECT s.month, s.logo_churn_rate, k.nrr
        FROM starter s
        JOIN kpi_summary k USING (month)
        WHERE k.mrr > (SELECT AVG(mrr) FROM kpi_summary)
        UNION ALL
        SELECT month, NULL, NULL FROM fct_mrr_movements
    """
    result = validate(sql)
    assert set(result.tables) == {
        f"{PROJECT}.dbt_marts.fct_churn",
        f"{PROJECT}.dbt_marts.kpi_summary",
        f"{PROJECT}.dbt_marts.fct_mrr_movements",
    }


def test_trailing_semicolon_is_fine():
    assert validate("SELECT * FROM kpi_summary;").tables


def test_limit_is_added_when_missing():
    assert validate("SELECT * FROM kpi_summary").sql.endswith(f"LIMIT {MAX_ROWS}")


def test_limit_is_capped():
    assert validate("SELECT * FROM kpi_summary LIMIT 100000").sql.endswith(f"LIMIT {MAX_ROWS}")


def test_smaller_limit_is_kept():
    assert validate("SELECT * FROM kpi_summary ORDER BY mrr DESC LIMIT 5").sql.endswith("LIMIT 5")


def test_limit_applies_to_the_whole_union():
    sql = validate("SELECT month FROM kpi_summary UNION ALL SELECT month FROM fct_mrr_movements").sql
    assert sql.endswith(f"LIMIT {MAX_ROWS}")
