with staging as (
    select * from {{ ref('stg_products') }}
)

select distinct
    brand_queried                       as brand_id,
    brand_queried                       as brand_name
from staging
where brand_queried is not null