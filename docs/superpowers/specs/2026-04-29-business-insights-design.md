# Business Insights — Market Concentration Dashboard

**Date:** 2026-04-29  
**Status:** Approved  
**Scope:** Rebuild `streamlit_app.py` around CPG market concentration analysis

---

## Goal

Replace the current aggregation-only dashboard with an insight-first view that answers: *which of ZURU Edge's five CPG verticals are dominated by a few big brands, and which are fragmented enough to disrupt?*

This is a portfolio piece targeting the ZURU Data Analyst Intern role (LA office). The primary reader is a ZURU hiring manager evaluating CPG category intelligence skills.

---

## Data Layer

### Removed queries
- `trends_vertical` — dropped
- `category_counts` — dropped
- `product_detail` — dropped

### Kept queries
- `kpi_summary` — unchanged
- `kpi_delta` — unchanged
- `brand_options` / `_where` helpers — removed (brand filter replaced by vertical filter)

### New query: `brand_concentration(_conn)`

Hits `CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS` directly using Snowflake JSON path syntax:

```sql
SELECT
    vertical,
    RAW_JSON:brands::string AS brand_name,
    COUNT(*) AS product_count
FROM CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS
WHERE RAW_JSON:brands::string IS NOT NULL
  AND RAW_JSON:brands::string != ''
GROUP BY vertical, brand_name
ORDER BY vertical, product_count DESC
```

Cached with `@st.cache_data(ttl=300)`.

### Python computation (`compute_concentration(df)`)

Takes the raw brand/vertical/product_count DataFrame and returns a summary DataFrame with one row per vertical:

| Column | Description |
|---|---|
| `vertical` | ZURU vertical name |
| `total_products` | total product count |
| `unique_brands` | distinct brand count |
| `top3_share_pct` | sum of top-3 brands' counts ÷ total × 100, rounded to 1 dp |
| `opportunity_tier` | "High Opportunity" if top3_share < 40%, "Medium" if 40–70%, "Low Opportunity" if > 70% |

---

## Page Layout

### Zone 1 — Header + KPI Cards (unchanged)
- Title: "ZURU CPG Competitive Intelligence Dashboard"
- Caption: "Competitive product intelligence across ZURU's five CPG verticals"
- Four `st.metric` cards: Total Products, Number of Brands, Number of Categories, ZURU Product Count (with day-over-day deltas)

### Zone 2 — Concentration Scorecard
Five `st.metric` cards in a single row (one per vertical):
- **Label:** vertical name
- **Value:** top-3 brand share % (e.g. "67%")
- **Delta:** opportunity tier string ("High Opportunity" / "Medium" / "Low Opportunity")
- Delta color: pass a signed float alongside the string — positive value for High Opportunity (renders green), negative for Low Opportunity (renders red), zero for Medium (renders gray). Use `delta_color="normal"`.

### Zone 3 — Top Brands by Vertical
Faceted horizontal bar chart using `plotly.make_subplots`:
- One subplot per vertical (2-col × 3-row grid, last cell empty)
- Each subplot: top 5 brands by product count, horizontal bars
- Consistent color palette across subplots
- Filtered by the vertical multi-select in the sidebar

---

## Sidebar

- **Vertical filter:** `st.multiselect` — all five verticals checked by default. Filters both Zone 2 and Zone 3.
- **Date filter:** kept as-is (guards `has_date` check)
- Brand filter: **removed**

---

## Error Handling

- If `brand_concentration` returns empty (RAW table empty or JSON field universally null): show `st.info("No brand data available.")` and skip Zones 2 and 3.
- KPI cards degrade gracefully as before (existing logic unchanged).

---

## Files Changed

- `streamlit_app.py` — only file modified. No new files.

---

## Out of Scope

- No dbt model changes
- No Snowflake schema changes
- No new Python dependencies (plotly.subplots is already available via plotly)
