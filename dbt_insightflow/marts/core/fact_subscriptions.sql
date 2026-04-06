{{ config(
    materialized='table'
) }}

SELECT
    subscription_id,
    organization_id,
    plan_id,
    mrr,
    start_date,
    end_date,
    status
FROM {{ ref('stg_subscriptions') }}
