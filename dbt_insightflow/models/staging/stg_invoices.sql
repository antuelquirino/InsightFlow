select
    invoice_id,
    organization_id,
    subscription_id,
    invoice_date,
    date_trunc(invoice_date, month) as invoice_month,
    round(cast(amount as numeric), 2) as amount,
    status
from {{ source('raw', 'invoices') }}
