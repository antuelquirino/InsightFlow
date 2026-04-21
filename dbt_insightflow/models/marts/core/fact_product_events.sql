{{ config(
    materialized='table'
) }}


SELECT
    event_id,
    user_id,
    organization_id,
    event_name,
    CAST(event_timestamp AS DATETIME) AS event_timestamp
FROM {{ ref('stg_product_events') }}
WHERE event_id IS NOT NULL