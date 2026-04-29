# dbt Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `dbt/` directory to the repo with mart models, source definition, config, and schema tests that formally define the CPG Analytics Snowflake schema.

**Architecture:** Seven new files under `dbt/`. Models read from `CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS` via a dbt source macro and materialize into `CPG_ANALYTICS.DBT_CANDRADE`. No existing files are modified.

**Tech Stack:** dbt Core, Snowflake, YAML, Python (for YAML validation only)

---

## File Map

| File | Action |
|---|---|
| `dbt/dbt_project.yml` | Create — project name, profile, materialization config |
| `dbt/profiles.yml.example` | Create — safe credential template |
| `dbt/models/sources.yml` | Create — declares `CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS` as a source |
| `dbt/models/marts/fct_products.sql` | Create — one row per product-load |
| `dbt/models/marts/dim_brands.sql` | Create — distinct brands |
| `dbt/models/marts/dim_categories.sql` | Create — distinct categories |
| `dbt/models/marts/schema.yml` | Create — column docs and data quality tests |

---

### Task 1: Scaffold dbt project config

**Files:**
- Create: `dbt/dbt_project.yml`
- Create: `dbt/profiles.yml.example`

- [ ] **Step 1: Create `dbt/dbt_project.yml`**

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

- [ ] **Step 2: Create `dbt/profiles.yml.example`**

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

- [ ] **Step 3: Validate both YAML files**

```bash
python -c "import yaml; yaml.safe_load(open('dbt/dbt_project.yml'))" && echo "dbt_project.yml valid"
python -c "import yaml; yaml.safe_load(open('dbt/profiles.yml.example'))" && echo "profiles.yml.example valid"
```

Expected:
```
dbt_project.yml valid
profiles.yml.example valid
```

- [ ] **Step 4: Commit**

```bash
git add dbt/dbt_project.yml dbt/profiles.yml.example
git commit -m "feat: scaffold dbt project config"
```

---

### Task 2: Declare the raw source

**Files:**
- Create: `dbt/models/sources.yml`

- [ ] **Step 1: Create `dbt/models/sources.yml`**

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

- [ ] **Step 2: Validate YAML**

```bash
python -c "import yaml; yaml.safe_load(open('dbt/models/sources.yml'))" && echo "sources.yml valid"
```

Expected: `sources.yml valid`

- [ ] **Step 3: Commit**

```bash
git add dbt/models/sources.yml
git commit -m "feat: declare open_food_facts as dbt source"
```

---

### Task 3: Add `fct_products` model

**Files:**
- Create: `dbt/models/marts/fct_products.sql`

- [ ] **Step 1: Create `dbt/models/marts/fct_products.sql`**

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

- [ ] **Step 2: Verify file was written correctly**

```bash
python -c "
content = open('dbt/models/marts/fct_products.sql').read()
assert 'source(' in content, 'Missing source macro'
assert 'brand_queried' in content, 'Missing brand_queried column'
assert 'primary_category' in content, 'Missing primary_category column'
assert 'MD5' in content, 'Missing surrogate key'
print('fct_products.sql OK')
"
```

Expected: `fct_products.sql OK`

- [ ] **Step 3: Commit**

```bash
git add dbt/models/marts/fct_products.sql
git commit -m "feat: add fct_products dbt model"
```

---

### Task 4: Add `dim_brands` and `dim_categories` models

**Files:**
- Create: `dbt/models/marts/dim_brands.sql`
- Create: `dbt/models/marts/dim_categories.sql`

- [ ] **Step 1: Create `dbt/models/marts/dim_brands.sql`**

```sql
SELECT DISTINCT
    MD5(RAW_JSON:brands::string)  AS brand_id,
    RAW_JSON:brands::string        AS brand_name
FROM {{ source('raw', 'open_food_facts') }}
WHERE RAW_JSON:brands::string IS NOT NULL
  AND RAW_JSON:brands::string != ''
```

- [ ] **Step 2: Create `dbt/models/marts/dim_categories.sql`**

```sql
SELECT DISTINCT
    MD5(RAW_JSON:main_category::string)  AS category_id,
    RAW_JSON:main_category::string        AS category_name
FROM {{ source('raw', 'open_food_facts') }}
WHERE RAW_JSON:main_category::string IS NOT NULL
  AND RAW_JSON:main_category::string != ''
```

- [ ] **Step 3: Verify both files**

```bash
python -c "
for f in ['dbt/models/marts/dim_brands.sql', 'dbt/models/marts/dim_categories.sql']:
    content = open(f).read()
    assert 'source(' in content, f'{f} missing source macro'
    assert 'MD5' in content, f'{f} missing surrogate key'
    assert 'DISTINCT' in content, f'{f} missing DISTINCT'
    print(f'{f} OK')
"
```

Expected:
```
dbt/models/marts/dim_brands.sql OK
dbt/models/marts/dim_categories.sql OK
```

- [ ] **Step 4: Commit**

```bash
git add dbt/models/marts/dim_brands.sql dbt/models/marts/dim_categories.sql
git commit -m "feat: add dim_brands and dim_categories dbt models"
```

---

### Task 5: Add schema.yml with tests and documentation

**Files:**
- Create: `dbt/models/marts/schema.yml`

- [ ] **Step 1: Create `dbt/models/marts/schema.yml`**

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

- [ ] **Step 2: Validate YAML**

```bash
python -c "import yaml; yaml.safe_load(open('dbt/models/marts/schema.yml'))" && echo "schema.yml valid"
```

Expected: `schema.yml valid`

- [ ] **Step 3: Verify all 7 dbt files exist**

```bash
python -c "
import os
files = [
    'dbt/dbt_project.yml',
    'dbt/profiles.yml.example',
    'dbt/models/sources.yml',
    'dbt/models/marts/fct_products.sql',
    'dbt/models/marts/dim_brands.sql',
    'dbt/models/marts/dim_categories.sql',
    'dbt/models/marts/schema.yml',
]
for f in files:
    assert os.path.exists(f), f'Missing: {f}'
    print(f'OK: {f}')
print('All 7 dbt files present.')
"
```

Expected:
```
OK: dbt/dbt_project.yml
OK: dbt/profiles.yml.example
OK: dbt/models/sources.yml
OK: dbt/models/marts/fct_products.sql
OK: dbt/models/marts/dim_brands.sql
OK: dbt/models/marts/dim_categories.sql
OK: dbt/models/marts/schema.yml
All 7 dbt files present.
```

- [ ] **Step 4: Run existing Python test suite to confirm nothing was broken**

```bash
pytest tests/ -v
```

Expected: all 27 tests pass (dbt files are inert — they don't affect Python tests)

- [ ] **Step 5: Commit**

```bash
git add dbt/models/marts/schema.yml
git commit -m "feat: add dbt schema tests and column documentation"
```
