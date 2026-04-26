# Milestone 01 — ETL Pipeline Design

**Date:** 2026-04-26
**Author:** Che Andrade
**Status:** Approved

---

## Overview

Build two Python extraction scripts that load raw data into Snowflake for the CPG Analytics pipeline. This is Milestone 01 of the ISBA-4715 project targeting a Data Analyst Intern role at ZURU.

**Deliverables:**
- `src/extract_off.py` — Open Food Facts API → `RAW.PUBLIC.OPEN_FOOD_FACTS`
- `src/extract_zuru.py` — Firecrawl crawl of zuru.com → `RAW.PUBLIC.ZURU_SCRAPE`
- `src/requirements.txt` — Python dependencies
- `.env.example` — credential template (safe to commit)

---

## Architecture

Two fully standalone scripts in `src/`. No shared modules or imports between them. Each script:

1. Loads credentials from `.env` via `python-dotenv`
2. Connects to Snowflake via `snowflake-connector-python`
3. Creates `DATABASE`, `SCHEMA`, and `TABLE` if they don't exist
4. Truncates the target table
5. Inserts fresh rows (full refresh per run)

**Load strategy:** TRUNCATE + INSERT on every run. Raw layer is a full refresh; no deduplication or SCD logic — that's dbt's job downstream.

**Pattern:** ELT — raw data lands as-is in Snowflake, transformations happen later in dbt.

```
src/
├── extract_off.py       # Script 1: Open Food Facts
├── extract_zuru.py      # Script 2: Firecrawl / ZURU
└── requirements.txt
.env.example             # repo root
```

---

## Script 1: extract_off.py

**Source:** Open Food Facts API (free, no auth required)
**Target:** `RAW.PUBLIC.OPEN_FOOD_FACTS`

### Data scope

Queries five category tags aligned to ZURU Edge's five verticals. ~500 products per vertical, ~2,500 rows per run.

| Vertical | OFF Category Tag |
|---|---|
| `pet_care` | `en:pet-food` |
| `baby_care` | `en:baby-foods` |
| `personal_care` | `en:cosmetics` |
| `home_care` | `en:household-cleaning` |
| `health_wellness` | `en:dietary-supplements` |

### Table schema

```sql
CREATE TABLE IF NOT EXISTS RAW.PUBLIC.OPEN_FOOD_FACTS (
    PRODUCT_CODE   VARCHAR(50),
    VERTICAL       VARCHAR(50),
    CATEGORY_TAG   VARCHAR(100),
    RAW_JSON       VARIANT,
    LOADED_AT      TIMESTAMP_NTZ
);
```

- `PRODUCT_CODE` — OFF barcode (the `code` field)
- `VERTICAL` — which ZURU vertical this row belongs to
- `CATEGORY_TAG` — exact OFF tag used in the query
- `RAW_JSON` — full OFF product JSON blob, unparsed
- `LOADED_AT` — UTC timestamp of this load run

### API call

```
GET https://world.openfoodfacts.org/cgi/search.pl
  ?action=process
  &tagtype_0=categories
  &tag_contains_0=contains
  &tag_0=<category_tag>
  &page_size=500
  &page=1
  &json=1
```

---

## Script 2: extract_zuru.py

**Source:** Firecrawl crawl of `https://zuru.com`
**Target:** `RAW.PUBLIC.ZURU_SCRAPE`

### Data scope

Crawl `zuru.com` starting from the homepage, following links up to 25 pages. Returns markdown content + metadata per page via the Firecrawl Python SDK.

### Table schema

```sql
CREATE TABLE IF NOT EXISTS RAW.PUBLIC.ZURU_SCRAPE (
    PAGE_URL       VARCHAR(2000),
    CRAWL_ID       VARCHAR(100),
    RAW_JSON       VARIANT,
    LOADED_AT      TIMESTAMP_NTZ
);
```

- `PAGE_URL` — URL of each crawled page
- `CRAWL_ID` — Firecrawl job ID (ties all pages from one run together)
- `RAW_JSON` — full Firecrawl page response object (includes `markdown`, `metadata`, `statusCode`)
- `LOADED_AT` — UTC timestamp of this load run

---

## Error Handling

- **Snowflake connection failure** → print error, `sys.exit(1)`
- **OFF API page failure** → print warning, skip that vertical, continue with remaining verticals
- **Firecrawl failures** → handled internally by the SDK; bad pages are skipped automatically
- No retry logic — re-run the script on failure

---

## Credentials (.env.example)

```
# Snowflake
SNOWFLAKE_ACCOUNT=yourorg-youraccount
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=SYSADMIN

# Firecrawl
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxx
```

`SNOWFLAKE_ACCOUNT` is the account identifier from the Snowflake URL — the part before `.snowflakecomputing.com`. The OFF script requires no API key.

---

## Dependencies (requirements.txt)

```
snowflake-connector-python
python-dotenv
requests
firecrawl-py
```

---

## Security

- `.env` is covered by `.gitignore` — never committed
- `profiles.yml` is also covered by `.gitignore`
- `.env.example` contains no real values — safe to commit
- No credentials hardcoded anywhere in scripts
