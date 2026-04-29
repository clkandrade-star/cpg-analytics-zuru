SELECT DISTINCT
    MD5(RAW_JSON:brands::string)  AS brand_id,
    RAW_JSON:brands::string        AS brand_name
FROM {{ source('raw', 'open_food_facts') }}
WHERE RAW_JSON:brands::string IS NOT NULL
  AND RAW_JSON:brands::string != ''
