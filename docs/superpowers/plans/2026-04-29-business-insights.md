# Market Concentration Business Insights Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `streamlit_app.py` to show CPG market concentration analysis across ZURU's five verticals instead of plain aggregations.

**Architecture:** Pull brand-level product counts from `RAW.OPEN_FOOD_FACTS` using Snowflake JSON path syntax, compute top-3 brand share per vertical in Python, and surface a scorecard + faceted bar chart in Streamlit. Single-file change to `streamlit_app.py` and its test file.

**Tech Stack:** Streamlit, Plotly (`make_subplots`, `graph_objects`), Pandas, Snowflake Python connector

---

## File Map

| File | Change |
|---|---|
| `streamlit_app.py` | Add `compute_concentration`, `brand_concentration`, `top_brands_chart`, `ALL_VERTICALS`; rebuild `main()`; remove `brand_options`, `trends_time`, `trends_vertical`, `category_counts`, `product_detail` |
| `tests/test_streamlit_app.py` | Add tests for `compute_concentration` and `brand_concentration`; remove tests for deleted functions |

---

### Task 1: `compute_concentration` — pure Python function (TDD)

**Files:**
- Modify: `tests/test_streamlit_app.py`
- Modify: `streamlit_app.py`

- [ ] **Step 1: Write failing tests**

Add to the bottom of `tests/test_streamlit_app.py`:

```python
def test_compute_concentration_low_opportunity():
    import streamlit_app
    df = pd.DataFrame({
        "VERTICAL": ["pet_care"] * 4,
        "BRAND_NAME": ["A", "B", "C", "D"],
        "PRODUCT_COUNT": [80, 10, 5, 5],
    })
    result = streamlit_app.compute_concentration(df)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["vertical"] == "pet_care"
    assert row["top3_share_pct"] == 95.0    # (80+10+5)/100
    assert row["opportunity_tier"] == "Low Opportunity"
    assert row["unique_brands"] == 4
    assert row["total_products"] == 100


def test_compute_concentration_high_opportunity():
    import streamlit_app
    df = pd.DataFrame({
        "VERTICAL": ["home_care"] * 10,
        "BRAND_NAME": [f"brand{i}" for i in range(10)],
        "PRODUCT_COUNT": [10] * 10,
    })
    result = streamlit_app.compute_concentration(df)
    row = result.iloc[0]
    assert row["top3_share_pct"] == 30.0    # 30/100
    assert row["opportunity_tier"] == "High Opportunity"


def test_compute_concentration_medium():
    import streamlit_app
    # sorted desc: 40, 15, 15, 10, 10, 10 → top3 = 70/100 = 70% → Medium (≤ 70)
    df = pd.DataFrame({
        "VERTICAL": ["health_wellness"] * 6,
        "BRAND_NAME": ["A", "B", "C", "D", "E", "F"],
        "PRODUCT_COUNT": [40, 15, 10, 15, 10, 10],
    })
    result = streamlit_app.compute_concentration(df)
    row = result.iloc[0]
    assert row["top3_share_pct"] == 70.0
    assert row["opportunity_tier"] == "Medium"


def test_compute_concentration_two_verticals():
    import streamlit_app
    df = pd.DataFrame({
        "VERTICAL": ["pet_care"] * 4 + ["home_care"] * 10,
        "BRAND_NAME": ["A", "B", "C", "D"] + [f"hb{i}" for i in range(10)],
        "PRODUCT_COUNT": [80, 10, 5, 5] + [10] * 10,
    })
    result = streamlit_app.compute_concentration(df)
    assert len(result) == 2
    pet = result[result["vertical"] == "pet_care"].iloc[0]
    home = result[result["vertical"] == "home_care"].iloc[0]
    assert pet["opportunity_tier"] == "Low Opportunity"
    assert home["opportunity_tier"] == "High Opportunity"
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_streamlit_app.py::test_compute_concentration_low_opportunity tests/test_streamlit_app.py::test_compute_concentration_high_opportunity tests/test_streamlit_app.py::test_compute_concentration_medium tests/test_streamlit_app.py::test_compute_concentration_two_verticals -v
```

Expected: FAILED with `AttributeError: module 'streamlit_app' has no attribute 'compute_concentration'`

- [ ] **Step 3: Implement `compute_concentration` in `streamlit_app.py`**

Add this function after `detect_columns` (after line 53) and before `_where`:

```python
def compute_concentration(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for vertical, group in df.groupby("VERTICAL"):
        group_sorted = group.sort_values("PRODUCT_COUNT", ascending=False)
        total = int(group_sorted["PRODUCT_COUNT"].sum())
        unique = len(group_sorted)
        top3 = int(group_sorted.head(3)["PRODUCT_COUNT"].sum())
        top3_share = round(top3 / total * 100, 1) if total > 0 else 0.0
        if top3_share < 40:
            tier = "High Opportunity"
        elif top3_share <= 70:
            tier = "Medium"
        else:
            tier = "Low Opportunity"
        rows.append({
            "vertical": vertical,
            "total_products": total,
            "unique_brands": unique,
            "top3_share_pct": top3_share,
            "opportunity_tier": tier,
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_streamlit_app.py::test_compute_concentration_low_opportunity tests/test_streamlit_app.py::test_compute_concentration_high_opportunity tests/test_streamlit_app.py::test_compute_concentration_medium tests/test_streamlit_app.py::test_compute_concentration_two_verticals -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: add compute_concentration for vertical market analysis"
```

---

### Task 2: `brand_concentration` query function (TDD)

**Files:**
- Modify: `tests/test_streamlit_app.py`
- Modify: `streamlit_app.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_streamlit_app.py`:

```python
def test_brand_concentration_queries_raw_json():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({
        "VERTICAL": ["pet_care"],
        "BRAND_NAME": ["Purina"],
        "PRODUCT_COUNT": [100],
    })
    captured = {}
    def fake_query(_conn, sql, params=()):
        captured["sql"] = sql
        return df
    with patch("streamlit_app.run_query", side_effect=fake_query):
        result = streamlit_app.brand_concentration(conn)
    assert "RAW_JSON:brands" in captured["sql"]
    assert "OPEN_FOOD_FACTS" in captured["sql"]
    assert "VERTICAL" in result.columns
    assert "BRAND_NAME" in result.columns
    assert "PRODUCT_COUNT" in result.columns
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/test_streamlit_app.py::test_brand_concentration_queries_raw_json -v
```

Expected: FAILED with `AttributeError: module 'streamlit_app' has no attribute 'brand_concentration'`

- [ ] **Step 3: Implement `brand_concentration` in `streamlit_app.py`**

Add after `compute_concentration` and before `_where`:

```python
@st.cache_data(ttl=300)
def brand_concentration(_conn) -> pd.DataFrame:
    return run_query(
        _conn,
        "SELECT vertical, RAW_JSON:brands::string AS brand_name, COUNT(*) AS product_count "
        "FROM CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS "
        "WHERE RAW_JSON:brands::string IS NOT NULL "
        "  AND RAW_JSON:brands::string != '' "
        "GROUP BY vertical, brand_name "
        "ORDER BY vertical, product_count DESC",
    )
```

- [ ] **Step 4: Run test to verify it passes**

```
pytest tests/test_streamlit_app.py::test_brand_concentration_queries_raw_json -v
```

Expected: 1 passed

- [ ] **Step 5: Run full test suite to check for regressions**

```
pytest tests/test_streamlit_app.py -v
```

Expected: all previously passing tests still pass

- [ ] **Step 6: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: add brand_concentration query from RAW_JSON"
```

---

### Task 3: Add `top_brands_chart` helper and plotly imports

**Files:**
- Modify: `streamlit_app.py`

- [ ] **Step 1: Add plotly subplots imports**

Replace the import block at the top of `streamlit_app.py` (lines 1–8) with:

```python
import os
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv
```

- [ ] **Step 2: Add `top_brands_chart` function**

Add after `brand_concentration` and before `_where`:

```python
def top_brands_chart(df: pd.DataFrame, selected_verticals: list) -> go.Figure | None:
    verticals = [v for v in selected_verticals if v in df["VERTICAL"].values]
    if not verticals:
        return None
    cols = min(2, len(verticals))
    rows = (len(verticals) + cols - 1) // cols
    titles = [v.replace("_", " ").title() for v in verticals]
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=titles)
    for i, vertical in enumerate(verticals):
        row_idx = i // cols + 1
        col_idx = i % cols + 1
        df_v = df[df["VERTICAL"] == vertical].nlargest(5, "PRODUCT_COUNT")
        fig.add_trace(
            go.Bar(
                x=df_v["PRODUCT_COUNT"],
                y=df_v["BRAND_NAME"],
                orientation="h",
                showlegend=False,
                marker_color="#2563EB",
            ),
            row=row_idx,
            col=col_idx,
        )
    fig.update_layout(height=300 * rows, title_text="Top 5 Brands by Vertical")
    return fig
```

- [ ] **Step 3: Run full test suite to verify no regressions**

```
pytest tests/test_streamlit_app.py -v
```

Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add top_brands_chart faceted bar chart helper"
```

---

### Task 4: Rebuild `main()` with new sidebar and all three zones

**Files:**
- Modify: `streamlit_app.py`

- [ ] **Step 1: Add `ALL_VERTICALS` constant just above `main()`**

Insert this line immediately before `def main():`:

```python
ALL_VERTICALS = ["pet_care", "baby_care", "personal_care", "home_care", "health_wellness"]
```

- [ ] **Step 2: Replace the entire `main()` function body**

Replace everything from `def main():` to the end of the file (keeping `if __name__ == "__main__": main()`) with:

```python
def main():
    st.set_page_config(
        page_title="ZURU CPG Competitive Intelligence Dashboard",
        layout="wide",
    )

    try:
        conn = get_conn()
    except Exception as e:
        st.error(f"Could not connect to Snowflake: {e}")
        st.stop()

    cols_available = detect_columns(conn)
    has_date = "loaded_at" in cols_available

    # ── Sidebar ───────────────────────────────────────────────────────────
    st.sidebar.title("ZURU CPG Intelligence")
    st.sidebar.divider()

    selected_verticals = st.sidebar.multiselect(
        "Vertical Filter",
        options=ALL_VERTICALS,
        default=ALL_VERTICALS,
    )

    start_date, end_date = None, None
    if has_date:
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(date(2026, 1, 1), date.today()),
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_date, end_date = date_range

    # ── Header ────────────────────────────────────────────────────────────
    st.title("ZURU CPG Competitive Intelligence Dashboard")
    st.caption("Competitive product intelligence across ZURU's five CPG verticals")
    st.divider()

    # ── Zone 1: KPI Cards ─────────────────────────────────────────────────
    kpis = kpi_summary(conn, None, start_date, end_date, has_date)
    zuru_count = zuru_product_count(conn)
    deltas = kpi_delta(conn)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Products", f"{kpis['total_products']:,}", delta=deltas["total_products"])
    c2.metric("Number of Brands", f"{kpis['num_brands']:,}")
    c3.metric("Number of Categories", f"{kpis['num_categories']:,}", delta=deltas["num_categories"])
    c4.metric("ZURU Product Count", f"{zuru_count:,}", delta=deltas["total_products"])

    st.divider()

    # ── Zones 2 + 3: Concentration ────────────────────────────────────────
    df_brands = brand_concentration(conn)
    if df_brands.empty:
        st.info("No brand data available.")
    else:
        active = selected_verticals if selected_verticals else ALL_VERTICALS
        df_filtered = df_brands[df_brands["VERTICAL"].isin(active)]
        df_conc = compute_concentration(df_filtered)

        st.subheader("Market Concentration by Vertical")
        if df_conc.empty:
            st.info("No data for selected verticals.")
        else:
            score_cols = st.columns(len(df_conc))
            for col, (_, row) in zip(score_cols, df_conc.iterrows()):
                col.metric(
                    label=row["vertical"].replace("_", " ").title(),
                    value=f"{row['top3_share_pct']:.1f}%",
                    delta=row["opportunity_tier"],
                    delta_color="off",
                )
            st.caption(
                "Top-3 brand share of products per vertical. "
                "Lower % = more fragmented market = higher disruption opportunity for ZURU."
            )

        st.divider()

        st.subheader("Top 5 Brands by Vertical")
        fig = top_brands_chart(df_filtered, active)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run full test suite**

```
pytest tests/test_streamlit_app.py -v
```

Expected: all tests pass

- [ ] **Step 4: Start the app and verify it renders correctly**

```
streamlit run streamlit_app.py
```

Open http://localhost:8501. Verify:
- KPI cards appear at top with day-over-day deltas
- "Market Concentration by Vertical" section shows up to 5 metric cards each displaying a `%` value and tier label ("High Opportunity" / "Medium" / "Low Opportunity")
- "Top 5 Brands by Vertical" section shows a faceted horizontal bar chart
- Unchecking a vertical in the sidebar removes it from both sections

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: rebuild dashboard with market concentration zones 2 and 3"
```

---

### Task 5: Remove old functions and stale tests

**Files:**
- Modify: `streamlit_app.py`
- Modify: `tests/test_streamlit_app.py`

- [ ] **Step 1: Delete these five functions from `streamlit_app.py`**

Remove each function body and its `def` line:
- `brand_options` (~lines 73–79)
- `trends_time` (~lines 134–141)
- `trends_vertical` (~lines 144–151)
- `category_counts` (~lines 154–164)
- `product_detail` (~lines 167–186)

Keep everything else: `get_conn`, `run_query`, `detect_columns`, `compute_concentration`, `brand_concentration`, `top_brands_chart`, `_where`, `kpi_summary`, `zuru_product_count`, `kpi_delta`, `ALL_VERTICALS`, `main`.

- [ ] **Step 2: Delete these five test functions from `tests/test_streamlit_app.py`**

Remove each function body and its `def` line:
- `test_trends_time_passes_date_filter`
- `test_trends_vertical_no_brand_filter`
- `test_category_counts_returns_top15_ascending`
- `test_product_detail_selects_loaded_at_when_available`
- `test_product_detail_omits_loaded_at_when_unavailable`

- [ ] **Step 3: Run full test suite**

```
pytest tests/test_streamlit_app.py -v
```

Expected: all remaining tests pass, no `AttributeError` for deleted functions

- [ ] **Step 4: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "refactor: remove old aggregation functions replaced by concentration analysis"
```
