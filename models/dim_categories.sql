with staging as (
    select * from {{ ref('stg_products') }}
)

select distinct
    primary_category                    as category_id,
    primary_category                    as category_name
from staging
where primary_category is not null
    and primary_category != ''
    and trim(primary_category) != ''