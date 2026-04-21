{{ config(
    materialized='table',
    unique_key='organization_id',
    partition_by={"field": "created_at", "data_type": "DATE"}
) }}

select *
from {{ ref('stg_organizations') }}

{% if is_incremental() %}
where created_at > (select max(created_at) from {{ this }})
{% endif %}