# Statistical Analysis Trend Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Product Trend Analysis section to the Streamlit dashboard with a 5-line time-series chart and a numpy linear regression summary table (slope, R², growth %) per vertical.

**Architecture:** Three new functions added to `streamlit_app.py` (`load_trend_data`, `compute_trend_stats`, `trend_chart`) and a new UI block appended to `main()`. All computation is tested offline via two new test functions in `tests/test_streamlit_app.py`. numpy is a transitive dependency of pandas — no new packages needed.

**Tech Stack:** Python, numpy (polyfit), Plotly (go.Scatter), Streamlit, pandas

---

## File Structure

| File | Change |
|---|---|
| `streamlit_app.py` | Add 3 functions; extend `main()` with trend section |
| `tests/test_streamlit_app.py` | Add 4 new test functions |

---

## Task 1: `compute_trend_stats` — regression computation

**Files:**
- Modify: `streamlit_app.py` (add function after `compute_concentration`)
- Modify: `tests/test_streamlit_app.py` (add 2 tests)

- [ ] **Step 1: Write the two failing tests**

Open `tests/test_streamlit_app.py` and append at the end:

```python
def test_compute_trend_stats_returns_correct_slope():
    from datetime import date
    import streamlit_app
    df = pd.DataFrame({
        "VERTICAL": ["pet_care", "pet_care", "pet_care"],
        "LOAD_DATE": [date(2026, 4, 1), date(2026, 4, 2), date(2026, 4, 3)],
        "PRODUCT_COUNT": [100, 200, 300],
    })
    result = streamlit_app.compute_trend_stats(df)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["Vertical"] == "pet_care"
    assert abs(row["Slope (products/day)"] - 100.0) < 0.1
    assert abs(row["R²"] - 1.0) < 0.001


def test_compute_trend_stats_skips_single_point_verticals():
    from datetime import date
    import streamlit_app
    df = pd.DataFrame({
        "VERTICAL": ["pet_care", "home_care", "home_care", "home_care"],
        "LOAD_DATE": [date(2026, 4, 1), date(2026, 4, 1), date(2026, 4, 2), date(2026, 4, 3)],
        "PRODUCT_COUNT": [100, 50, 100, 150],
    })
    result = streamlit_app.compute_trend_stats(df)
    assert len(result) == 1
    assert result.iloc[0]["Vertical"] == "home_care"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_streamlit_app.py::test_compute_trend_stats_returns_correct_slope tests/test_streamlit_app.py::test_compute_trend_stats_skips_single_point_verticals -v
```

Expected: FAIL with `AttributeError: module 'streamlit_app' has no attribute 'compute_trend_stats'`

- [ ] **Step 3: Implement `compute_trend_stats` in `streamlit_app.py`**

Add `import numpy as np` at the top of `streamlit_app.py` with the other imports.

Then add this function after `compute_concentration` (around line 80):

```python
def compute_trend_stats(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for vertical, group in df.groupby("VERTICAL"):
        group = group.sort_values("LOAD_DATE")
        if len(group) < 2:
            continue
        x = list(range(len(group)))
        y = group["PRODUCT_COUNT"].tolist()
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        y_pred = np.polyval(coeffs, x)
        ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
        ss_tot = sum((yi - sum(y) / len(y)) ** 2 for yi in y)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 1.0
        growth = (y[-1] - y[0]) / y[0] * 100 if y[0] != 0 else 0.0
        rows.append({
            "Vertical": vertical,
            "Slope (products/day)": round(slope, 1),
            "R²": round(r2, 3),
            "Growth %": round(growth, 1),
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_streamlit_app.py::test_compute_trend_stats_returns_correct_slope tests/test_streamlit_app.py::test_compute_trend_stats_skips_single_point_verticals -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: add compute_trend_stats with numpy linear regression"
```

---

## Task 2: `load_trend_data` — Snowflake query

**Files:**
- Modify: `streamlit_app.py` (add function after `brand_concentration`)
- Modify: `tests/test_streamlit_app.py` (add 1 test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_streamlit_app.py`:

```python
def test_load_trend_data_queries_raw_table():
    from datetime import date
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({
        "LOAD_DATE": [date(2026, 4, 1)],
        "VERTICAL": ["pet_care"],
        "PRODUCT_COUNT": [500],
    })
    captured = {}
    def fake_query(_conn, sql, params=()):
        captured["sql"] = sql
        return df
    with patch("streamlit_app.run_query", side_effect=fake_query):
        result = streamlit_app.load_trend_data(conn)
    assert "OPEN_FOOD_FACTS" in captured["sql"]
    assert "vertical" in captured["sql"]
    assert not result.empty
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_streamlit_app.py::test_load_trend_data_queries_raw_table -v
```

Expected: FAIL with `AttributeError: module 'streamlit_app' has no attribute 'load_trend_data'`

- [ ] **Step 3: Implement `load_trend_data` in `streamlit_app.py`**

Add this function after `brand_concentration` in the "Data helpers" section:

```python
@st.cache_data(ttl=300)
def load_trend_data(_conn) -> pd.DataFrame:
    return run_query(
        _conn,
        "SELECT loaded_at::DATE AS load_date, "
        "vertical, "
        "COUNT(*) AS product_count "
        "FROM CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS "
        "GROUP BY load_date, vertical "
        "ORDER BY load_date",
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_streamlit_app.py::test_load_trend_data_queries_raw_table -v
```

Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: add load_trend_data query"
```

---

## Task 3: `trend_chart` — Plotly line chart

**Files:**
- Modify: `streamlit_app.py` (add function after `top_brands_chart`)
- Modify: `tests/test_streamlit_app.py` (add 2 tests)

- [ ] **Step 1: Write the two failing tests**

Append to `tests/test_streamlit_app.py`:

```python
def test_trend_chart_returns_none_for_empty_df():
    import streamlit_app
    result = streamlit_app.trend_chart(pd.DataFrame())
    assert result is None


def test_trend_chart_returns_none_for_single_date():
    from datetime import date
    import streamlit_app
    df = pd.DataFrame({
        "LOAD_DATE": [date(2026, 4, 1), date(2026, 4, 1)],
        "VERTICAL": ["pet_care", "home_care"],
        "PRODUCT_COUNT": [500, 300],
    })
    result = streamlit_app.trend_chart(df)
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_streamlit_app.py::test_trend_chart_returns_none_for_empty_df tests/test_streamlit_app.py::test_trend_chart_returns_none_for_single_date -v
```

Expected: FAIL with `AttributeError: module 'streamlit_app' has no attribute 'trend_chart'`

- [ ] **Step 3: Implement `trend_chart` in `streamlit_app.py`**

Add this function after `top_brands_chart` in the "Data helpers" section:

```python
def trend_chart(df: pd.DataFrame) -> go.Figure | None:
    if df.empty:
        return None
    load_date_col = "LOAD_DATE" if "LOAD_DATE" in df.columns else "load_date"
    vertical_col = "VERTICAL" if "VERTICAL" in df.columns else "vertical"
    count_col = "PRODUCT_COUNT" if "PRODUCT_COUNT" in df.columns else "product_count"
    if df[load_date_col].nunique() < 2:
        return None
    fig = go.Figure()
    for vertical in df[vertical_col].unique():
        df_v = df[df[vertical_col] == vertical].sort_values(load_date_col)
        fig.add_trace(go.Scatter(
            x=df_v[load_date_col],
            y=df_v[count_col],
            mode="lines+markers",
            name=vertical.replace("_", " ").title(),
        ))
    fig.update_layout(
        title="Product Count Trend by Vertical",
        xaxis_title="Load Date",
        yaxis_title="Product Count",
    )
    return fig
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_streamlit_app.py::test_trend_chart_returns_none_for_empty_df tests/test_streamlit_app.py::test_trend_chart_returns_none_for_single_date -v
```

Expected: 2 passed

- [ ] **Step 5: Run full test suite to confirm nothing broken**

```bash
pytest tests/ -v
```

Expected: all tests pass (31 total)

- [ ] **Step 6: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: add trend_chart Plotly line chart"
```

---

## Task 4: Wire trend section into `main()`

**Files:**
- Modify: `streamlit_app.py` (extend `main()`)

- [ ] **Step 1: Add the trend section to `main()`**

In `streamlit_app.py`, locate the end of `main()` — after the `st.plotly_chart(fig, ...)` call for Top 5 Brands. Append this block:

```python
    st.divider()
    st.subheader("Product Trend Analysis")
    df_trend = load_trend_data(conn)
    if df_trend.empty:
        st.info("No trend data available yet. Run the extraction pipeline first.")
    else:
        fig_trend = trend_chart(df_trend)
        if fig_trend is not None:
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Not enough load dates for trend analysis. Run the extraction on at least 2 separate days.")
        df_stats = compute_trend_stats(df_trend)
        if not df_stats.empty:
            st.dataframe(
                df_stats.style.format({
                    "Slope (products/day)": "{:.1f}",
                    "R²": "{:.3f}",
                    "Growth %": "{:.1f}%",
                }),
                use_container_width=True,
                hide_index=True,
            )
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 3: Run the dashboard locally and verify the section appears**

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501. Scroll to the bottom — you should see:
- "Product Trend Analysis" subheader
- Either the 5-line chart (if 2+ load dates exist in Snowflake) or the info message
- The regression summary table below the chart

- [ ] **Step 4: Commit and push**

```bash
git add streamlit_app.py
git commit -m "feat: wire trend analysis section into dashboard"
git push
```

---

## Self-Review

**Spec coverage:**
- `load_trend_data` ✓ Task 2
- `compute_trend_stats` with polyfit, R², growth % ✓ Task 1
- `trend_chart` returning None for <2 dates ✓ Task 3
- UI section appended after Top 5 Brands ✓ Task 4
- 2 tests for `compute_trend_stats` ✓ Task 1 (2 tests written)
- 2 tests for `trend_chart` ✓ Task 3 (added as Steps 1-2)
- Formatting (slope 1dp, R² 3dp, growth 1dp) ✓ Task 4 Step 1

**Placeholder scan:** None found — all code is complete.

**Type consistency:** `compute_trend_stats(df)` receives `pd.DataFrame`, returns `pd.DataFrame` — consistent across Tasks 1 and 4. `trend_chart(df)` receives `pd.DataFrame`, returns `go.Figure | None` — consistent across Tasks 3 and 4. `load_trend_data(_conn)` returns `pd.DataFrame` — consistent across Tasks 2 and 4.
