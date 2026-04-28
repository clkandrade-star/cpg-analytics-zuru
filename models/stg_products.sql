with source as (
    select * from {{ source('raw', 'open_food_facts') }}
),

renamed as (
    select
        product_code                    as barcode,
        vertical                        as brand_queried,
        category_tag                    as primary_category,
        raw_json                        as raw_json,
        loaded_at                       as extracted_at
    from source
    where product_code is not null
)

select * from renamed