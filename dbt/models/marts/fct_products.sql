SELECT
    MD5(PRODUCT_CODE || '|' || VERTICAL || '|' || LOADED_AT::string) AS product_id,
    PRODUCT_CODE                                AS barcode,
    RAW_JSON:brands::string                     AS brand_queried,
    RAW_JSON:main_category::string              AS primary_category,
    VERTICAL,
    LOADED_AT
FROM {{ source('raw', 'open_food_facts') }}
WHERE RAW_JSON:brands::string IS NOT NULL
  AND RAW_JSON:brands::string != ''
