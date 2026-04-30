# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] — 2026-04-30

### Added
- Open Food Facts extraction pipeline (`src/extract_off.py`) covering five ZURU CPG verticals with retry logic on 503 errors
- ZURU website scrape via Firecrawl (`src/extract_zuru.py`) for competitive knowledge base
- Snowflake raw layer: `CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS` with VARIANT JSON column for schema-free ingestion
- dbt star schema: `fct_products`, `dim_brands`, `dim_categories` in `CPG_ANALYTICS.DBT_CANDRADE`
- dbt schema tests: `unique`, `not_null`, `accepted_values` across all mart models
- Streamlit dashboard with KPI cards (total products, brands, categories, ZURU count) and day-over-day deltas
- Market concentration scorecard — top-3 brand share % per vertical with opportunity tier classification
- Faceted top-5 brands bar chart filterable by vertical and date range
- Knowledge base: Firecrawl-scraped ZURU content synthesized into `knowledge/wiki/` pages
- GitHub Actions daily extraction workflow (6am UTC / 11pm PT)
- Streamlit Community Cloud deployment at https://cpg-analytics-zuru.streamlit.app/
- `TRUNCATE_BEFORE_LOAD` env var for optional table reset before extraction
- Devcontainer configuration for VS Code with Python 3.11 and Streamlit port forwarding
- Unit test suite: `tests/test_extract_off.py`, `tests/test_extract_zuru.py`, `tests/test_streamlit_app.py`
