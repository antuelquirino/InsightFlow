{{ config(
    materialized='table'
) }}



SELECT
    organization_id,
    plan_id,
    mrr AS total_mrr,
    
    SAFE.DATE_TRUNC(SAFE_CAST(start_date AS DATE), MONTH) AS month
FROM {{ ref('stg_subscriptions') }}