# Streamlit Dashboard Design

**Date:** 2026-04-27
**Author:** Che Andrade
**Status:** Approved

---

## Overview

Build a Streamlit dashboard at `streamlit_app.py` (repo root) that connects to Snowflake and surfaces CPG category intelligence from the dbt mart layer. This is the visualization milestone of the CPG Analytics — ZURU portfolio project.

---

## Architecture

Single file `streamlit_app.py`. No helper modules.

```
streamlit_app.py
├── load_dotenv()                          # reads SNOWFLAKE_* from .env
├── @st.cache_resource  get_conn()         # one Snowflake connection per session
├── @st.cache_data(ttl=300)  run_query()   # parameterized query → DataFrame
├── Sidebar: brand dropdown                # "All Brands" + distinct brand_queried values
├── Chart 1: product count by brand        # filtered by selection
└── Chart 2: product count by category     # filtered by selection
```

---

## Database

- **Snowflake database:** `CPG_ANALYTICS`
- **Schema:** `DBT_CANDRADE`
- **Tables used:** `fct_products` only (brand and category are readable strings in-column)

### Table columns referenced

| Table | Columns used |
|---|---|
| `fct_products` | `brand_queried`, `primary_category` |
| `dim_brands` | not used (brand_queried is already readable) |
| `dim_categories` | not used (primary_category is already readable) |

---

## SQL Queries

```sql
-- 1. Brand dropdown options
SELECT DISTINCT brand_queried
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
ORDER BY brand_queried;

-- 2. Product count by brand (optionally filtered)
SELECT brand_queried AS brand, COUNT(*) AS product_count
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
[WHERE brand_queried = '<selected>']
GROUP BY brand_queried
ORDER BY product_count DESC
LIMIT 30;

-- 3. Product count by category (same filter)
SELECT primary_category AS category, COUNT(*) AS product_count
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
[WHERE brand_queried = '<selected>']
GROUP BY primary_category
ORDER BY product_count DESC;
```

The `WHERE` clause is included only when a specific brand is selected; omitted for "All Brands".

---

## Layout

```
┌─ Sidebar ───────────────────────────────┐
│  Brand: [All Brands ▼]                  │
└─────────────────────────────────────────┘

┌─ Main ──────────────────────────────────┐
│  CPG Analytics — ZURU                   │
│  ─────────────────────────────────────  │
│  ┌──────────────────────────────────┐   │
│  │  Products by Brand (bar chart)   │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  Products by Category (bar chart)│   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

- Charts are full-width and stacked vertically
- Sidebar holds the brand filter dropdown
- "All Brands" shows aggregate counts across all brands
- Selecting a specific brand filters both charts to that brand's products

---

## Connection

- Library: `snowflake-connector-python`
- Credentials: loaded from `.env` via `python-dotenv`
- Connection cached with `@st.cache_resource` (one connection per session)
- Query results cached with `@st.cache_data(ttl=300)` (5-minute refresh)

### Environment variables required

```
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PASSWORD
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_ROLE      (optional, defaults to SYSADMIN)
```

---

## Dependencies

Add to `src/requirements.txt`:

```
streamlit
plotly
pandas
```

---

## Files Changed

| File | Action |
|---|---|
| `streamlit_app.py` | Create (repo root) |
| `src/requirements.txt` | Update — add streamlit, plotly, pandas |
