# Setup Guide

## Prerequisites

- Python 3.11+
- A Snowflake account (free trial at snowflake.com)
- A Firecrawl API key (free tier at app.firecrawl.dev) — only needed to re-run the ZURU web scrape

## 1. Clone and create a virtual environment

```bash
git clone https://github.com/clkandrade-star/cpg-analytics-zuru.git
cd cpg-analytics-zuru
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r src/requirements.txt
```

## 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

| Variable | Where to find it |
|---|---|
| `SNOWFLAKE_ACCOUNT` | Your Snowflake URL: `<account>.snowflakecomputing.com` — use only `<account>` |
| `SNOWFLAKE_USER` | Your Snowflake username |
| `SNOWFLAKE_PASSWORD` | Your Snowflake password |
| `SNOWFLAKE_WAREHOUSE` | Name of your warehouse (default: `COMPUTE_WH`) |
| `SNOWFLAKE_ROLE` | Role with CREATE DATABASE privileges (default: `SYSADMIN`) |
| `FIRECRAWL_API_KEY` | From app.firecrawl.dev — only needed for `extract_zuru.py` |

## 3. Snowflake prerequisites

The extraction script auto-creates the database and schema on first run. Your Snowflake role must have:

```sql
-- Run once in Snowflake as ACCOUNTADMIN if SYSADMIN lacks these grants
GRANT CREATE DATABASE ON ACCOUNT TO ROLE SYSADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE SYSADMIN;
```

## 4. Run the extraction

```bash
python src/extract_off.py     # loads ~2,500 rows from Open Food Facts
python src/extract_zuru.py    # scrapes zuru.com (requires FIRECRAWL_API_KEY)
```

This creates `CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS` in Snowflake.

## 5. Set up dbt

```bash
pip install dbt-snowflake
cp dbt/profiles.yml.example ~/.dbt/profiles.yml
```

The example profile reads from the same environment variables as the extraction scripts, so no additional config is needed if your `.env` is already sourced.

```bash
cd dbt
dbt debug       # verify connection to Snowflake
dbt run         # build staging + mart models
dbt test        # run schema tests
```

This creates `CPG_ANALYTICS.DBT_CANDRADE.{fct_products, dim_brands, dim_categories}`.

## 6. Run the dashboard locally

```bash
cd ..           # back to repo root
streamlit run streamlit_app.py
```

Open http://localhost:8501 in your browser.

## 7. Run the test suite

```bash
pytest tests/ -v
```

No Snowflake connection required — all Snowflake calls are mocked in the test suite. See [TESTING.md](TESTING.md) for details.
