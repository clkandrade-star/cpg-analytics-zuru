# Statistical Analysis — Trend Section Design

## Goal

Add a Product Trend Analysis section to the Streamlit dashboard that demonstrates statistical analysis skills directly mapped to the ZURU Data Analyst Intern job posting requirement.

## What We're Building

A new section at the bottom of `streamlit_app.py` containing:
1. A Plotly line chart — product count per vertical per load date (5 lines, one per vertical)
2. A regression summary table — slope (products/day), R², and growth % per vertical computed via numpy linear regression

## Architecture

All code lives in `streamlit_app.py`. Three additions:

### `load_trend_data(conn) -> pd.DataFrame`
- Decorated with `@st.cache_data(ttl=300)`
- Queries `CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS`
- Returns columns: `LOAD_DATE`, `VERTICAL`, `PRODUCT_COUNT`

```sql
SELECT loaded_at::DATE AS load_date,
       vertical,
       COUNT(*) AS product_count
FROM CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS
GROUP BY load_date, vertical
ORDER BY load_date
```

### `compute_trend_stats(df) -> pd.DataFrame`
- Pure Python, no Snowflake dependency — testable offline
- Runs `numpy.polyfit(degree=1)` on each vertical's (day_index, product_count) pairs
- Skips verticals with fewer than 2 data points silently
- Returns DataFrame with columns: `Vertical`, `Slope (products/day)`, `R²`, `Growth %`

| Column | Computation |
|---|---|
| Slope (products/day) | polyfit coefficient |
| R² | 1 − SS_res / SS_tot |
| Growth % | (last − first) / first × 100 |

### `trend_chart(df) -> go.Figure | None`
- One `go.Scatter` trace per vertical, mode `lines+markers`
- Plotly default discrete color sequence
- Returns `None` if df is empty or has fewer than 2 distinct dates

## Dashboard Placement

New section appended to `main()` after the existing Top 5 Brands chart:

```
st.divider()
st.subheader("Product Trend Analysis")
[line chart]
[regression summary table]
```

Nothing existing moves or changes.

## Data Formatting

- Slope: 1 decimal place
- R²: 3 decimal places
- Growth %: 1 decimal place with `%` suffix

## Testing

Two new tests in `tests/test_streamlit_app.py`:

**`test_compute_trend_stats_returns_correct_slope`**
Feed 3 data points with a known linear relationship (e.g., day 0 → 100, day 1 → 200, day 2 → 300). Assert slope ≈ 100.0 and R² ≈ 1.0.

**`test_compute_trend_stats_skips_single_point_verticals`**
Feed one vertical with 1 data point and one with 3. Assert only the 3-point vertical appears in the output DataFrame.

## Files Changed

| File | Change |
|---|---|
| `streamlit_app.py` | Add `load_trend_data`, `compute_trend_stats`, `trend_chart`; extend `main()` |
| `tests/test_streamlit_app.py` | Add 2 new test functions |
