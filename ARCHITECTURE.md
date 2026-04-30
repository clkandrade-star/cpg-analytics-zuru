# Architecture

## Pipeline Overview

```
Open Food Facts API
        │
        ▼
GitHub Actions (daily 6am UTC)
        │  src/extract_off.py
        ▼
Snowflake: CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS
        │  (raw JSON stored in VARIANT column)
        ▼
dbt Staging: stg_products
        │  (parse fields from RAW_JSON, filter nulls)
        ▼
dbt Marts: fct_products + dim_brands + dim_categories
        │  (star schema, business-ready)
        ▼
Streamlit Dashboard (Streamlit Community Cloud)
```

A parallel pipeline scrapes zuru.com via Firecrawl and synthesizes competitive intelligence into `knowledge/wiki/` pages, which inform dashboard design and ZURU vertical definitions.

## Why Snowflake

Snowflake's `VARIANT` type stores the raw Open Food Facts JSON without schema enforcement at load time, allowing the extraction script to run without knowing which fields are populated across products. dbt then parses only the fields the dashboard needs. This separates the "land everything" concern from the "model what matters" concern.

## Why dbt

dbt provides SQL-based transformations with built-in testing (`not_null`, `unique`, `accepted_values`), version control, and documentation generation (`dbt docs generate`). The star schema is a natural fit for dashboard queries that aggregate across brands and categories.

## Star Schema Design

```
fct_products (one row per product-load)
    ├── brand_queried ──→ dim_brands.brand_name
    └── primary_category ──→ dim_categories.category_name
```

`fct_products` is a **snapshot table** — each daily pipeline run appends rows rather than upserts. This preserves load history for the day-over-day delta metrics visible in the dashboard KPI cards.

`dim_brands` and `dim_categories` are derived from `fct_products` via `SELECT DISTINCT`, so they always reflect whatever brands and categories exist in the fact table without requiring separate maintenance.

## Vertical → Category Tag Mapping

ZURU Edge's five CPG verticals map to Open Food Facts category tags:

| ZURU Vertical | OFF Category Tag |
|---|---|
| `pet_care` | `en:pet-food` |
| `baby_care` | `en:baby-foods` |
| `personal_care` | `en:cosmetics` |
| `home_care` | `en:household-cleaning` |
| `health_wellness` | `en:dietary-supplements` |

This mapping lives in `src/extract_off.py:VERTICALS`. To add a vertical:
1. Append a new key-value pair to `VERTICALS` in `extract_off.py`
2. Add the new value to the `accepted_values` test in `dbt/models/marts/schema.yml`

## Data Quality Assumptions

- Products without a barcode (`code` field) are loaded with an empty string — the dbt staging model filters these out.
- `brand_queried` comes from `RAW_JSON:brands` (first listed brand). Products with no brand are filtered by the `not_null` test in staging.
- `primary_category` comes from `RAW_JSON:main_category`. Products without one are filtered similarly.
- **Deduplication is not applied at load time.** The `product_id` surrogate key (MD5 of barcode + vertical + loaded_at) ensures uniqueness per load, not per product. The same product may appear across multiple load dates.

## GitHub Actions Orchestration

The daily workflow (`.github/workflows/extract.yml`) runs at 6am UTC (11pm PT). It:
1. Installs `src/requirements.txt`
2. Runs `extract_off.py` — loads ~500 products per vertical (~2,500 total) from the OFF API
3. Runs `extract_zuru.py` — scrapes zuru.com, updates `knowledge/raw/`

dbt runs are **not automated** — run `dbt run` manually or add a step to the workflow. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Dashboard Architecture

`streamlit_app.py` connects directly to Snowflake using:
- `@st.cache_resource` for the connection object — persists for the lifetime of the Streamlit process, so the connection is not re-opened on every interaction.
- `@st.cache_data(ttl=300)` for query results — 5-minute cache. This means the dashboard may show data up to 5 minutes stale; refresh the page to force a cache bust.

All SQL runs against `CPG_ANALYTICS.DBT_CANDRADE.*` (the dbt mart schema).

`detect_columns()` queries `information_schema` at startup to check whether `loaded_at` exists in `fct_products`. This allows the dashboard to conditionally show the date filter without hard-coding schema assumptions — a guard against schema evolution.

## dbt Docs

To generate and serve the dbt documentation site locally:

```bash
cd dbt
dbt docs generate
dbt docs serve
```

This opens a browser with the full lineage graph, column descriptions, and test results.
