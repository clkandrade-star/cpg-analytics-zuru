# Dashboard Redesign: ZURU CPG Competitive Intelligence Dashboard

**Date:** 2026-04-29
**Author:** Che Andrade
**Status:** Approved

---

## Overview

Redesign `streamlit_app.py` from a basic two-chart prototype into a professional merchandising dashboard named **"ZURU CPG Competitive Intelligence Dashboard"**. The redesign targets the visual language of modern SaaS BI tools (clean light theme, blue accent `#2563EB`) and surfaces competitive CPG intelligence across ZURU's five product verticals.

---

## Architecture

Single file `streamlit_app.py` — no helper modules added. Extends the existing pattern:

```
streamlit_app.py
├── load_dotenv()
├── @st.cache_resource  get_conn()
├── @st.cache_data(ttl=300)  run_query()
├── detect_columns()           — queries INFORMATION_SCHEMA at startup
├── Sidebar: brand filter + optional date range
├── KPI row: 4 st.metric cards
├── Chart 1: Product Trends (adaptive — line or bar)
├── Chart 2: Top Categories horizontal bar
└── Table: Product Details dataframe
```

---

## Theme

- **Style:** Clean Light SaaS
- **Background:** White main canvas, light grey sidebar (`#F8F9FA` via CSS)
- **Accent color:** Blue `#2563EB` (Plotly chart fills, metric highlights)
- **Layout:** `st.set_page_config(layout="wide")`
- **Page title:** `"ZURU CPG Competitive Intelligence Dashboard"`

---

## Layout

```
┌─ Sidebar ──────────────────────────────────┐
│  ZURU CPG Intelligence                     │
│  ─────────────────────────────────────     │
│  Brand Filter                              │
│  [All Brands ▼]                            │
│                                            │
│  Date Range  (hidden if no loaded_at col)  │
│  [start date] → [end date]                 │
└────────────────────────────────────────────┘

┌─ Main Canvas ──────────────────────────────────────────────────────┐
│  ZURU CPG Competitive Intelligence Dashboard                       │
│  Competitive product intelligence across ZURU's five CPG verticals │
│  ─────────────────────────────────────────────────────────────    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────┐ │
│  │ Total        │ │ Number of    │ │ Number of    │ │ ZURU     │ │
│  │ Products     │ │ Brands       │ │ Categories   │ │ Products │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Product Trends                                              │ │
│  │  (line over time if loaded_at exists; bar by vertical if not)│ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Top Categories by Product Count  (horizontal bar, top 15)   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Product Details  (dataframe, 500-row limit)                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

## Database

- **Snowflake database:** `CPG_ANALYTICS`
- **Schema:** `DBT_CANDRADE`
- **Primary table:** `fct_products`

### Columns referenced

| Column | Type | Notes |
|---|---|---|
| `brand_queried` | VARCHAR | Brand filter + KPI |
| `primary_category` | VARCHAR | Category chart + table |
| `vertical` | VARCHAR | Trends fallback chart |
| `loaded_at` | TIMESTAMP_NTZ | Trends line chart + date filter — optional, detected at runtime |

---

## SQL Queries

```sql
-- 0. Column detection (run once at startup)
SELECT column_name
FROM CPG_ANALYTICS.information_schema.columns
WHERE table_schema = 'DBT_CANDRADE'
  AND table_name   = 'FCT_PRODUCTS';

-- 1. Brand dropdown options
SELECT DISTINCT brand_queried
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
WHERE brand_queried IS NOT NULL
ORDER BY brand_queried;

-- 2. KPI summary (filtered by brand + date if applicable)
SELECT
    COUNT(*)                          AS total_products,
    COUNT(DISTINCT brand_queried)     AS num_brands,
    COUNT(DISTINCT primary_category)  AS num_categories
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
[WHERE brand_queried = '<selected>']
[AND loaded_at::DATE BETWEEN '<start>' AND '<end>'];

-- 2b. ZURU Product Count (always unfiltered)
SELECT COUNT(*) AS zuru_product_count
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products;

-- 3a. Product Trends — time-based (only if loaded_at detected)
SELECT DATE_TRUNC('week', loaded_at)::DATE AS week, COUNT(*) AS product_count
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
[WHERE brand_queried = '<selected>']
[AND loaded_at::DATE BETWEEN '<start>' AND '<end>']
GROUP BY 1 ORDER BY 1;

-- 3b. Product Trends — vertical fallback (if no loaded_at)
SELECT vertical, COUNT(*) AS product_count
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
[WHERE brand_queried = '<selected>']
GROUP BY vertical ORDER BY product_count DESC;

-- 4. Top categories horizontal bar (top 15)
SELECT primary_category AS category, COUNT(*) AS product_count
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
[WHERE brand_queried = '<selected>']
[AND loaded_at::DATE BETWEEN '<start>' AND '<end>']
GROUP BY primary_category
ORDER BY product_count ASC  -- ascending so Plotly renders largest at top of horizontal bar
LIMIT 15;

-- 5. Product details table (500-row limit)
SELECT brand_queried, primary_category, vertical [, loaded_at]
FROM CPG_ANALYTICS.DBT_CANDRADE.fct_products
[WHERE brand_queried = '<selected>']
[AND loaded_at::DATE BETWEEN '<start>' AND '<end>']
LIMIT 500;
```

`WHERE` clauses in brackets are conditional on filter state.

---

## Components

### Sidebar

- Bold label: "ZURU CPG Intelligence"
- `st.selectbox("Brand Filter", ["All Brands"] + brands)`
- `st.date_input("Date Range", value=(min_date, max_date))` — shown only if `loaded_at` is detected
- `st.divider()` between controls

### KPI Cards — `st.columns(4)`

| Card | Value | Filter behavior |
|---|---|---|
| Total Products | `COUNT(*)` | Filtered by brand + date |
| Number of Brands | `COUNT(DISTINCT brand_queried)` | Filtered by brand + date |
| Number of Categories | `COUNT(DISTINCT primary_category)` | Filtered by brand + date |
| ZURU Product Count | `COUNT(*)` full table | Always unfiltered |

Values formatted with `f"{n:,}"` (comma thousands separator).

### Product Trends Chart

- **With `loaded_at`:** `px.line`, x = week, y = product_count. Title: "Product Trends Over Time".
- **Without `loaded_at`:** `px.bar`, x = vertical, y = product_count. Title: "Products by ZURU Vertical".
- Color: `#2563EB`. `use_container_width=True`.

### Top Categories Horizontal Bar

- `px.bar(..., orientation='h')`
- Top 15 categories; SQL sorts ascending so Plotly's natural bottom-to-top y-axis renders the largest bar at the top
- Fill: `#2563EB`
- Title: "Top Categories by Product Count"
- Labels: `{"category": "Category", "product_count": "Product Count"}`

### Product Details Table

- `st.dataframe(df, use_container_width=True)`
- Columns displayed (title-cased): Brand, Category, Vertical, (Date if available)
- 500-row hard limit on the SQL query

---

## Adaptive Date Logic

At startup, `detect_columns()` queries `INFORMATION_SCHEMA` and returns the set of column names in `fct_products`. The result is cached with `@st.cache_data(ttl=300)`.

- If `loaded_at` in detected columns: show date range picker, run time-based trends query, include date filter in all WHERE clauses.
- If not: hide date range picker entirely, run vertical-based trends query, omit date filter.

This makes the app forward-compatible — once dbt propagates `loaded_at` into fct_products, the date features activate automatically with no code change.

---

## Files Changed

| File | Action |
|---|---|
| `streamlit_app.py` | Rewrite (same file, full redesign) |

No new files, no new dependencies beyond what is already installed (`streamlit`, `plotly`, `pandas`, `snowflake-connector-python`).
