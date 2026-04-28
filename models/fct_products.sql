with staging as (
    select * from {{ ref('stg_products') }}
)

select
    barcode                             as product_id,
    barcode,
    brand_queried,
    primary_category,
    extracted_at
from staging