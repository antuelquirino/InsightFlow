-- Month-end MRR by plan, acquisition channel and company size. Sum over any
-- combination of dimensions to get totals.
with paying as (

    select *
    from {{ ref('int_mrr_by_org_monthly') }}
    where is_paying

)

select
    paying.month,
    paying.plan_id,
    organizations.acquisition_channel,
    organizations.company_size,
    count(*) as paying_customers,
    sum(paying.seats) as seats,
    sum(paying.mrr) as mrr,
    sum(paying.mrr) * 12 as arr
from paying
inner join {{ ref('stg_organizations') }} as organizations
    on organizations.organization_id = paying.organization_id
group by 1, 2, 3, 4
