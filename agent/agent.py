import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from bq_client import run_query, get_schema
from datetime import datetime

client = OpenAI()
DATASET = "dbt_marts"

def clean_sql(sql):
    # Removes markdown blocks and extra spaces
    sql = sql.replace("```sql", "").replace("```", "").strip()
    if sql.endswith(";"): sql = sql[:-1]
    return sql

def detect_kpi_query(user_prompt):
    prompt = user_prompt.lower()
    # Speed layer: Direct routing to pre-computed KPI tables
    if "mrr" in prompt and "growth" in prompt:
        return f"SELECT month, total_mrr, previous_mrr, mrr_growth FROM {DATASET}.kpi_mrr_growth ORDER BY month LIMIT 100"
    if "churn" in prompt:
        return f"SELECT month, churn_rate FROM {DATASET}.kpi_churn_rate ORDER BY month LIMIT 100"
    if "active compan" in prompt:
        return f"SELECT month, active_companies FROM {DATASET}.kpi_active_companies ORDER BY month LIMIT 100"
    return None

def validate_sql(sql):
    sql_lower = sql.lower().strip()
    
    # 1. Basic Security Guardrails
    if not (sql_lower.startswith("select") or sql_lower.startswith("with")):
        raise ValueError("Only SELECT queries are allowed for security reasons.")

    forbidden = ["drop", "delete", "update", "insert", "alter", "truncate", "create", "merge"]
    for word in forbidden:
        if f" {word} " in sql_lower:
            raise ValueError(f"Unsafe SQL command detected: {word}")

    # 2. STRICT TABLE MAPPING
    # This prevents the AI from using raw tables or guessing shorthand names
    mapping = {
        "subscriptions": "fact_subscriptions",
        "organizations": "dim_organizations",
        "product_events": "fact_product_events",
        "mrr": "fact_mrr"
    }

    for simple_name, full_name in mapping.items():
        # Replace shorthand with full Dataset.Table path if not already there
        if f" {simple_name}" in sql and f"{DATASET}.{full_name}" not in sql:
            sql = sql.replace(f" {simple_name}", f" {DATASET}.{full_name}")
            sql = sql.replace(f"\n{simple_name}", f"\n{DATASET}.{full_name}")

    # 3. Final Check: Ensure Mart tables always have the dataset prefix
    tables_with_prefix = ["fact_subscriptions", "dim_organizations", "fact_product_events", "fact_mrr", 
                          "kpi_mrr_growth", "kpi_churn_rate", "kpi_active_companies"]
    
    for table in tables_with_prefix:
        if f" {table}" in sql and f"{DATASET}.{table}" not in sql:
            sql = sql.replace(f" {table}", f" {DATASET}.{table}")

    if "limit" not in sql.lower():
        sql += "\nLIMIT 100"
        
    return sql

def query_to_sql(user_prompt):
    schema = get_schema()
    # High-level system prompt to guide the AI Analyst
    system_prompt = f"""
    You are a Senior Data Analyst for a SaaS company. Today is {datetime.now().strftime('%Y-%m-%d')}.
    The dataset is: {DATASET}
    
    STRICT TABLE SCHEMA (ONLY USE THESE):
    - {DATASET}.fact_subscriptions (Columns: subscription_id, organization_id, plan_id, mrr, status, start_date, end_date)
    - {DATASET}.dim_organizations (Columns: organization_id, name, industry, country, company_size, created_at)
    - {DATASET}.fact_product_events (Columns: event_id, user_id, organization_id, event_name, event_timestamp)
    - {DATASET}.kpi_mrr_growth, {DATASET}.kpi_churn_rate, {DATASET}.kpi_active_companies
    
    CRITICAL RULES:
    1. NEVER use the 'raw' dataset (raw.organizations, etc.). It contains STRING dates.
    2. ALWAYS use the '{DATASET}' dataset. It has correctly casted DATE types.
    3. To count 'users', use 'COUNT(DISTINCT user_id)' from {DATASET}.fact_product_events.
    4. To get users by country, JOIN {DATASET}.fact_product_events (pe) with {DATASET}.dim_organizations (org) on organization_id.
    5. In GROUP BY clauses, repeat the full column name (e.g., GROUP BY org.industry), never use aliases.
    6. For 'today', use DATE(event_timestamp) = CURRENT_DATE().
    7. Return ONLY the raw SQL code. No markdown, no prose.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Schema context: {schema}\n\nQuestion: {user_prompt}"}
        ],
        temperature=0
    )
    
    sql = response.choices[0].message.content.strip()
    return clean_sql(sql)

def create_chart(df, title):
    if df.empty or len(df.columns) < 2:
        return None
    try:
        plt.figure(figsize=(10, 6))
        # Decide chart type based on column names (Line for time, Bar for categories)
        first_col = str(df.columns[0]).lower()
        chart_type = "line" if "month" in first_col or "date" in first_col else "bar"
        
        df.plot(kind=chart_type, x=df.columns[0], y=df.columns[1], ax=plt.gca(), color='#1f77b4')
        plt.title(title, fontsize=14)
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        chart_path = "chart.png"
        plt.savefig(chart_path)
        plt.close()
        return chart_path
    except:
        return None

def generate_insight(user_prompt, df):
    if df.empty:
        return "Insufficient data found to generate business insights."
    
    prompt = f"""
    You are a Business Intelligence Manager. 
    Analyze this BigQuery result to answer: "{user_prompt}"
    
    Data Result:
    {df.to_string()}
    
    Provide 3 brief, high-level business insights in English. 
    Highlight any interesting trends or performance indicators.
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def run_agent(user_prompt):
    try:
        # Step 1: KPI Router (Optimization)
        sql = detect_kpi_query(user_prompt)
        
        # Step 2: Dynamic SQL Generation
        if sql is None:
            sql = query_to_sql(user_prompt)
            sql = validate_sql(sql)
        
        # Step 3: Database Execution
        df = run_query(sql)
        
        # Step 4: Analytical Layer
        chart = create_chart(df, user_prompt)
        insight = generate_insight(user_prompt, df)
        
        return {
            "sql": sql,
            "data": df,
            "chart": chart,
            "insight": insight
        }
    except Exception as e:
        # Error reporting in English for global standards
        return {"error": f"Agent Exception: {str(e)}", "sql": locals().get('sql', 'N/A')}