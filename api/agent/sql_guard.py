"""Validates SQL written by the LLM before it reaches BigQuery.

A query passes only if it is a single read-only SELECT (CTEs and set operations
allowed) over the allowlisted marts. Unqualified mart names are qualified, and
the outermost LIMIT is added or capped. Anything else raises SqlRejected with a
reason worded for the LLM, which gets one chance to fix its query.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from api.agent.context import allowed_tables, load_schema

MAX_ROWS = 500

# sqlglot logs a warning when it falls back to parsing unsupported syntax as a
# generic command; those statements are rejected anyway.
logging.getLogger("sqlglot").setLevel(logging.ERROR)

WRITE_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Create, exp.Drop, exp.Alter,
    exp.TruncateTable, exp.Command, exp.Set, exp.Use,
)


class SqlRejected(ValueError):
    """The query is not safe or not allowed; the message says why."""


@dataclass(frozen=True)
class ValidatedQuery:
    sql: str
    tables: tuple[str, ...]


def validate(sql: str, max_rows: int = MAX_ROWS) -> ValidatedQuery:
    sql = (sql or "").strip().rstrip(";").strip()
    if not sql:
        raise SqlRejected("The query is empty.")
    try:
        statements = [s for s in sqlglot.parse(sql, read="bigquery") if s is not None]
    except ParseError as error:
        raise SqlRejected(f"The query is not valid BigQuery SQL: {str(error).splitlines()[0]}") from error
    if len(statements) != 1:
        raise SqlRejected("Send exactly one SQL statement.")

    query = statements[0]
    if not isinstance(query, exp.Query):
        raise SqlRejected("Only SELECT queries are allowed.")
    for node in query.walk():
        if isinstance(node, WRITE_NODES):
            raise SqlRejected("Only SELECT queries are allowed; the query contains a write or DDL clause.")

    tables = _check_tables(query)
    _cap_limit(query, max_rows)
    return ValidatedQuery(sql=query.sql(dialect="bigquery"), tables=tables)


def _check_tables(query: exp.Query) -> tuple[str, ...]:
    schema = load_schema()
    project, dataset = schema["project"], schema["dataset"]
    marts = set(schema["tables"])
    cte_names = {cte.alias_or_name.lower() for cte in query.find_all(exp.CTE)}
    allowed = allowed_tables()
    used = []
    for table in query.find_all(exp.Table):
        name, db, catalog = table.name, table.db, table.catalog
        if not name:
            raise SqlRejected("Table functions are not allowed; select from the marts tables.")
        if not db and not catalog and name.lower() in cte_names:
            continue
        # Qualify what the LLM left implicit: `kpi_summary` or `dbt_marts.kpi_summary`.
        if not db and name in marts:
            db = dataset
        if not catalog and db == dataset:
            catalog = project
        full_name = f"{catalog}.{db}.{name}".lower()
        if full_name not in allowed:
            raise SqlRejected(
                f"Table `{'.'.join(p for p in (table.catalog, table.db, name) if p)}` is not allowed. "
                f"Use only these tables: {', '.join(f'`{project}.{dataset}.{m}`' for m in sorted(marts))}."
            )
        table.set("catalog", exp.to_identifier(catalog))
        table.set("db", exp.to_identifier(db))
        used.append(f"{catalog}.{db}.{name}")
    if not used:
        raise SqlRejected("The query must read at least one of the marts tables.")
    return tuple(dict.fromkeys(used))


def _cap_limit(query: exp.Query, max_rows: int) -> None:
    limit = query.args.get("limit")
    if limit is None:
        query.limit(max_rows, copy=False)
        return
    value = limit.expression
    if not (isinstance(value, exp.Literal) and value.is_int):
        raise SqlRejected("LIMIT must be a whole number.")
    if int(value.name) > max_rows:
        limit.set("expression", exp.Literal.number(max_rows))
