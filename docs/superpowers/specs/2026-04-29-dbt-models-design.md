# dbt Models Design

**Date:** 2026-04-29
**Status:** Approved
**Scope:** Add a `dbt/` directory to the repo with mart models, source definition, tests, and config. No changes to any existing files.

---

## Goal

The `fct_products`, `dim_brands`, and `dim_categories` tables already exist in Snowflake (`CPG_ANALYTICS.DBT_CANDRADE`) but have no corresponding dbt project in the repo. This spec defines the dbt project that formally declares and documents those tables so the portfolio demonstrates end-to-end dbt skills.

**Constraint:** Models must match the existing Snowflake schema exactly so the Streamlit dashboard continues working without changes.

---

## Architecture

Option B: mart models + source definition. Models reference the raw table via `{{ source('raw', 'open_food_facts') }}`. Materialized as tables in `CPG_ANALYTICS.DBT_CANDRADE`. No staging layer (that is Option C / future work).

---

## Directory Structure

```
dbt/
├── dbt_project.yml          # project name, profile, materialization config
├── profiles.yml.example     # safe-to-commit credential template (no real values)
└── models/
    ├── sources.yml          # declares CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS
    └── marts/
        ├── fct_products.sql
        ├── dim_brands.sql
        ├── dim_categories.sql
        └── schema.yml       # column descriptions + not_null/unique/accepted_values tests
```

`profiles.yml` (real credentials) stays out of the repo — covered by `.gitignore`.

---

## Files

### `dbt/dbt_project.yml`

```yaml
name: cpg_analytics
version: "1.0.0"
config-version: 2

profile: cpg_analytics

model-paths: ["models"]
test-paths: ["tests"]
macro-paths: ["macros"]

target-path: "target"
clean-targets:
  - target
  - dbt_packages

models:
  cpg_analytics:
    marts:
      +materialized: table
      +schema: DBT_CANDRADE
```

### `dbt/profiles.yml.example`

```yaml
cpg_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE', 'SYSADMIN') }}"
      database: CPG_ANALYTICS
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      schema: DBT_CANDRADE
      threads: 1
```

### `dbt/models/sources.yml`

```yaml
version: 2

sources:
  - name: raw
    database: CPG_ANALYTICS
    schema: RAW
    tables:
      - name: open_food_facts
        description: "Raw Open Food Facts product JSON loaded by extract_off.py"
        columns:
          - name: PRODUCT_CODE
            description: "OFF barcode"
          - name: VERTICAL
            description: "ZURU Edge vertical (pet_care, baby_care, etc.)"
          - name: CATEGORY_TAG
            description: "OFF API category tag used to fetch this row"
          - name: RAW_JSON
            description: "Full product JSON from the Open Food Facts API"
          - name: LOADED_AT
            description: "UTC timestamp of the pipeline run"
```

### `dbt/models/marts/fct_products.sql`

```sql
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
```

### `dbt/models/marts/dim_brands.sql`

```sql
SELECT DISTINCT
    MD5(RAW_JSON:brands::string)  AS brand_id,
    RAW_JSON:brands::string        AS brand_name
FROM {{ source('raw', 'open_food_facts') }}
WHERE RAW_JSON:brands::string IS NOT NULL
  AND RAW_JSON:brands::string != ''
```

### `dbt/models/marts/dim_categories.sql`

```sql
SELECT DISTINCT
    MD5(RAW_JSON:main_category::string)  AS category_id,
    RAW_JSON:main_category::string        AS category_name
FROM {{ source('raw', 'open_food_facts') }}
WHERE RAW_JSON:main_category::string IS NOT NULL
  AND RAW_JSON:main_category::string != ''
```

### `dbt/models/marts/schema.yml`

```yaml
version: 2

models:
  - name: fct_products
    description: "One row per product-load. Extracted from Open Food Facts across ZURU's five CPG verticals."
    columns:
      - name: product_id
        description: "Surrogate key (MD5 of barcode + vertical + load timestamp)"
        tests: [unique, not_null]
      - name: barcode
        description: "Open Food Facts product code"
        tests: [not_null]
      - name: brand_queried
        description: "Brand name extracted from RAW_JSON:brands"
        tests: [not_null]
      - name: primary_category
        description: "Main product category from RAW_JSON:main_category"
        tests: [not_null]
      - name: vertical
        description: "ZURU Edge vertical"
        tests:
          - not_null
          - accepted_values:
              values: [pet_care, baby_care, personal_care, home_care, health_wellness]
      - name: loaded_at
        description: "UTC timestamp of the pipeline run that loaded this row"
        tests: [not_null]

  - name: dim_brands
    description: "Distinct brands observed across all pipeline loads."
    columns:
      - name: brand_id
        tests: [unique, not_null]
      - name: brand_name
        tests: [unique, not_null]

  - name: dim_categories
    description: "Distinct product categories observed across all pipeline loads."
    columns:
      - name: category_id
        tests: [unique, not_null]
      - name: category_name
        tests: [unique, not_null]
```

---

## Notes

- `RAW_JSON:main_category` is the assumed JSON path for `primary_category`. Verify this matches the actual field name in your Snowflake `fct_products` before running `dbt run`.
- The models are safe to commit regardless — they only execute when you explicitly run `dbt run` or `dbt test`.
- `profiles.yml` must be created locally by copying `profiles.yml.example` and filling in real Snowflake credentials before running dbt.

---

## Files Changed

| File | Action |
|---|---|
| `dbt/dbt_project.yml` | Create |
| `dbt/profiles.yml.example` | Create |
| `dbt/models/sources.yml` | Create |
| `dbt/models/marts/fct_products.sql` | Create |
| `dbt/models/marts/dim_brands.sql` | Create |
| `dbt/models/marts/dim_categories.sql` | Create |
| `dbt/models/marts/schema.yml` | Create |

No existing files modified.
