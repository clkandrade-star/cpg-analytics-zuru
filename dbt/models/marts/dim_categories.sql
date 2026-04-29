SELECT DISTINCT
    MD5(RAW_JSON:main_category::string)  AS category_id,
    RAW_JSON:main_category::string        AS category_name
FROM {{ source('raw', 'open_food_facts') }}
WHERE RAW_JSON:main_category::string IS NOT NULL
  AND RAW_JSON:main_category::string != ''
