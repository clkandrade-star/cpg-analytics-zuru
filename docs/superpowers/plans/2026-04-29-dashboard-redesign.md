# Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `streamlit_app.py` as a professional SaaS-style competitive intelligence dashboard with 4 KPI cards, adaptive product trends chart, top-categories horizontal bar, and product details table.

**Architecture:** Single-file rewrite of `streamlit_app.py`. All data functions (query helpers) live at the top of the file; all Streamlit UI code lives inside `main()`. `main()` is called via `if __name__ == "__main__"` so the module is importable in tests without side effects. Column detection at startup controls whether date-based features are shown.

**Tech Stack:** Streamlit, Plotly Express, pandas, snowflake-connector-python, pytest, unittest.mock

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `streamlit_app.py` | Rewrite | All query helpers + full UI in `main()` |
| `tests/conftest.py` | Create | Mock streamlit so module is importable in tests |
| `tests/test_streamlit_app.py` | Create | Unit tests for all data helper functions |

---

### Task 1: Test Infrastructure

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create conftest.py that mocks streamlit before any import**

```python
# tests/conftest.py
import sys
from unittest.mock import MagicMock

def _passthrough(func=None, **kw):
    # handles both @st.cache_resource (no parens) and @st.cache_data(ttl=300)
    if func is not None:
        return func
    return lambda f: f

st_mock = MagicMock()
st_mock.cache_data = _passthrough
st_mock.cache_resource = _passthrough
sys.modules.setdefault("streamlit", st_mock)
```

- [ ] **Step 2: Verify conftest loads without error**

Run: `pytest tests/ --collect-only -q`
Expected: no import errors; existing tests discovered

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add conftest to mock streamlit for unit tests"
```

---

### Task 2: Restructure streamlit_app.py and add detect_columns

**Files:**
- Modify: `streamlit_app.py`
- Create: `tests/test_streamlit_app.py`

The current file runs UI code at module level. Move everything into `main()` so tests can import data helpers without side effects. Add `detect_columns` as the first new function.

- [ ] **Step 1: Write the failing test for detect_columns**

```python
# tests/test_streamlit_app.py
from unittest.mock import MagicMock, patch
import pandas as pd


def make_conn():
    return MagicMock()


def test_detect_columns_returns_lowercase_set():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({"COLUMN_NAME": ["BRAND_QUERIED", "PRIMARY_CATEGORY", "LOADED_AT", "VERTICAL"]})
    with patch("streamlit_app.run_query", return_value=df):
        cols = streamlit_app.detect_columns(conn)
    assert cols == {"brand_queried", "primary_category", "loaded_at", "vertical"}


def test_detect_columns_without_loaded_at():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({"COLUMN_NAME": ["BRAND_QUERIED", "PRIMARY_CATEGORY", "VERTICAL"]})
    with patch("streamlit_app.run_query", return_value=df):
        cols = streamlit_app.detect_columns(conn)
    assert "loaded_at" not in cols
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_streamlit_app.py -v`
Expected: ImportError or AttributeError — `detect_columns` does not exist yet

- [ ] **Step 3: Rewrite streamlit_app.py with new structure and detect_columns**

Replace the full file with:

```python
import os
from datetime import date

import pandas as pd
import plotly.express as px
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DB = "CPG_ANALYTICS"
SCHEMA = "DBT_CANDRADE"


# ── Connection & base query ────────────────────────────────────────────────

@st.cache_resource
def get_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        role=os.environ.get("SNOWFLAKE_ROLE", "SYSADMIN"),
        database=DB,
        schema=SCHEMA,
    )


@st.cache_data(ttl=300)
def run_query(_conn, sql: str, params: tuple = ()) -> pd.DataFrame:
    cur = _conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        cur.close()


# ── Data helpers ───────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def detect_columns(_conn) -> set:
    df = run_query(
        _conn,
        f"SELECT column_name FROM {DB}.information_schema.columns "
        f"WHERE table_schema = %s AND table_name = %s",
        (SCHEMA, "FCT_PRODUCTS"),
    )
    return {c.lower() for c in df["COLUMN_NAME"].tolist()}


# ── UI ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="ZURU CPG Competitive Intelligence Dashboard",
        layout="wide",
    )
    st.title("ZURU CPG Competitive Intelligence Dashboard")
    st.caption("Competitive product intelligence across ZURU's five CPG verticals")

    try:
        conn = get_conn()
    except Exception as e:
        st.error(f"Could not connect to Snowflake: {e}")
        st.stop()

    st.info("Connected — more features coming soon.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest tests/test_streamlit_app.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: restructure app for testability, add detect_columns"
```

---

### Task 3: KPI Query Functions

**Files:**
- Modify: `streamlit_app.py` (add `_where`, `brand_options`, `kpi_summary`, `zuru_product_count`)
- Modify: `tests/test_streamlit_app.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_streamlit_app.py`:

```python
def test_where_no_filters():
    import streamlit_app
    where, params = streamlit_app._where(None)
    assert where == ""
    assert params == ()


def test_where_brand_only():
    import streamlit_app
    where, params = streamlit_app._where("ZURU")
    assert "brand_queried = %s" in where
    assert params == ("ZURU",)


def test_where_brand_and_date():
    import streamlit_app
    where, params = streamlit_app._where("ZURU", date(2026, 1, 1), date(2026, 4, 29), has_date=True)
    assert "brand_queried = %s" in where
    assert "loaded_at::DATE BETWEEN %s AND %s" in where
    assert params == ("ZURU", date(2026, 1, 1), date(2026, 4, 29))


def test_kpi_summary_returns_dict():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({
        "TOTAL_PRODUCTS": [500],
        "NUM_BRANDS": [42],
        "NUM_CATEGORIES": [12],
    })
    with patch("streamlit_app.run_query", return_value=df):
        result = streamlit_app.kpi_summary(conn, None)
    assert result == {"total_products": 500, "num_brands": 42, "num_categories": 12}


def test_kpi_summary_with_brand_filter():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({
        "TOTAL_PRODUCTS": [50],
        "NUM_BRANDS": [1],
        "NUM_CATEGORIES": [5],
    })
    captured = {}
    def fake_query(_conn, sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return df
    with patch("streamlit_app.run_query", side_effect=fake_query):
        streamlit_app.kpi_summary(conn, "NUK")
    assert "brand_queried = %s" in captured["sql"]
    assert "NUK" in captured["params"]


def test_zuru_product_count_returns_int():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({"ZURU_PRODUCT_COUNT": [9999]})
    with patch("streamlit_app.run_query", return_value=df):
        result = streamlit_app.zuru_product_count(conn)
    assert result == 9999
    assert isinstance(result, int)
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_streamlit_app.py -v`
Expected: 6 new tests fail with AttributeError

- [ ] **Step 3: Add _where, brand_options, kpi_summary, zuru_product_count to streamlit_app.py**

Insert after `detect_columns` and before `def main()`:

```python
def _where(
    brand: str | None,
    start=None,
    end=None,
    has_date: bool = False,
) -> tuple[str, tuple]:
    clauses, params = [], []
    if brand:
        clauses.append("brand_queried = %s")
        params.append(brand)
    if has_date and start and end:
        clauses.append("loaded_at::DATE BETWEEN %s AND %s")
        params.extend([start, end])
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, tuple(params)


def brand_options(_conn) -> list:
    df = run_query(
        _conn,
        f"SELECT DISTINCT brand_queried FROM {DB}.{SCHEMA}.fct_products "
        "WHERE brand_queried IS NOT NULL ORDER BY brand_queried",
    )
    return df["BRAND_QUERIED"].tolist()


def kpi_summary(_conn, brand: str | None, start=None, end=None, has_date: bool = False) -> dict:
    where, params = _where(brand, start, end, has_date)
    df = run_query(
        _conn,
        f"SELECT COUNT(*) AS total_products, "
        f"COUNT(DISTINCT brand_queried) AS num_brands, "
        f"COUNT(DISTINCT primary_category) AS num_categories "
        f"FROM {DB}.{SCHEMA}.fct_products {where}",
        params,
    )
    row = df.iloc[0]
    return {
        "total_products": int(row["TOTAL_PRODUCTS"]),
        "num_brands": int(row["NUM_BRANDS"]),
        "num_categories": int(row["NUM_CATEGORIES"]),
    }


def zuru_product_count(_conn) -> int:
    df = run_query(
        _conn,
        f"SELECT COUNT(*) AS zuru_product_count FROM {DB}.{SCHEMA}.fct_products",
    )
    return int(df.iloc[0]["ZURU_PRODUCT_COUNT"])
```

- [ ] **Step 4: Run tests to confirm all pass**

Run: `pytest tests/test_streamlit_app.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: add KPI query helpers (_where, kpi_summary, zuru_product_count)"
```

---

### Task 4: Trends and Category Chart Functions

**Files:**
- Modify: `streamlit_app.py` (add `trends_time`, `trends_vertical`, `category_counts`)
- Modify: `tests/test_streamlit_app.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_streamlit_app.py`:

```python
def test_trends_time_passes_date_filter():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({"WEEK": ["2026-01-05"], "PRODUCT_COUNT": [10]})
    captured = {}
    def fake_query(_conn, sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return df
    with patch("streamlit_app.run_query", side_effect=fake_query):
        streamlit_app.trends_time(conn, None, date(2026, 1, 1), date(2026, 4, 29))
    assert "DATE_TRUNC" in captured["sql"]
    assert date(2026, 1, 1) in captured["params"]


def test_trends_vertical_no_brand_filter():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({"VERTICAL": ["pet_care", "baby_care"], "PRODUCT_COUNT": [300, 200]})
    captured = {}
    def fake_query(_conn, sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return df
    with patch("streamlit_app.run_query", side_effect=fake_query):
        result = streamlit_app.trends_vertical(conn, None)
    assert "vertical" in captured["sql"].lower()
    assert captured["params"] == ()
    assert len(result) == 2


def test_category_counts_returns_top15_ascending():
    import streamlit_app
    conn = make_conn()
    rows = [{"CATEGORY": f"cat{i}", "PRODUCT_COUNT": i} for i in range(1, 16)]
    df = pd.DataFrame(rows)
    captured = {}
    def fake_query(_conn, sql, params=()):
        captured["sql"] = sql
        return df
    with patch("streamlit_app.run_query", side_effect=fake_query):
        result = streamlit_app.category_counts(conn, None)
    assert "ASC" in captured["sql"]
    assert "LIMIT 15" in captured["sql"]
    assert len(result) == 15
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_streamlit_app.py -v`
Expected: 3 new tests fail with AttributeError

- [ ] **Step 3: Add trends_time, trends_vertical, category_counts to streamlit_app.py**

Insert after `zuru_product_count` and before `def main()`:

```python
def trends_time(_conn, brand: str | None, start=None, end=None) -> pd.DataFrame:
    where, params = _where(brand, start, end, has_date=True)
    return run_query(
        _conn,
        f"SELECT DATE_TRUNC('week', loaded_at)::DATE AS week, COUNT(*) AS product_count "
        f"FROM {DB}.{SCHEMA}.fct_products {where} GROUP BY 1 ORDER BY 1",
        params,
    )


def trends_vertical(_conn, brand: str | None) -> pd.DataFrame:
    where, params = _where(brand)
    return run_query(
        _conn,
        f"SELECT vertical, COUNT(*) AS product_count "
        f"FROM {DB}.{SCHEMA}.fct_products {where} GROUP BY vertical ORDER BY product_count DESC",
        params,
    )


def category_counts(_conn, brand: str | None, start=None, end=None, has_date: bool = False) -> pd.DataFrame:
    where, params = _where(brand, start, end, has_date)
    return run_query(
        _conn,
        f"SELECT category, product_count FROM ("
        f"  SELECT primary_category AS category, COUNT(*) AS product_count "
        f"  FROM {DB}.{SCHEMA}.fct_products {where} "
        f"  GROUP BY primary_category ORDER BY product_count DESC LIMIT 15"
        f") sub ORDER BY product_count ASC",
        params,
    )
```

- [ ] **Step 4: Run tests to confirm all pass**

Run: `pytest tests/test_streamlit_app.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: add trends and category chart query helpers"
```

---

### Task 5: Product Detail Function

**Files:**
- Modify: `streamlit_app.py` (add `product_detail`)
- Modify: `tests/test_streamlit_app.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_streamlit_app.py`:

```python
def test_product_detail_selects_loaded_at_when_available():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({
        "BRAND_QUERIED": ["ZURU"],
        "PRIMARY_CATEGORY": ["pet-food"],
        "VERTICAL": ["pet_care"],
        "LOADED_AT": ["2026-04-01"],
    })
    captured = {}
    def fake_query(_conn, sql, params=()):
        captured["sql"] = sql
        return df
    with patch("streamlit_app.run_query", side_effect=fake_query):
        streamlit_app.product_detail(conn, None, has_date=True)
    assert "loaded_at" in captured["sql"].lower()
    assert "LIMIT 500" in captured["sql"]


def test_product_detail_omits_loaded_at_when_unavailable():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({
        "BRAND_QUERIED": ["ZURU"],
        "PRIMARY_CATEGORY": ["pet-food"],
        "VERTICAL": ["pet_care"],
    })
    captured = {}
    def fake_query(_conn, sql, params=()):
        captured["sql"] = sql
        return df
    with patch("streamlit_app.run_query", side_effect=fake_query):
        streamlit_app.product_detail(conn, None, has_date=False)
    assert "loaded_at" not in captured["sql"].lower()
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_streamlit_app.py -v`
Expected: 2 new tests fail with AttributeError

- [ ] **Step 3: Add product_detail to streamlit_app.py**

Insert after `category_counts` and before `def main()`:

```python
def product_detail(
    _conn,
    brand: str | None,
    start=None,
    end=None,
    has_date: bool = False,
) -> pd.DataFrame:
    where, params = _where(brand, start, end, has_date)
    date_col = ", loaded_at" if has_date else ""
    return run_query(
        _conn,
        f"SELECT brand_queried, primary_category, vertical{date_col} "
        f"FROM {DB}.{SCHEMA}.fct_products {where} LIMIT 500",
        params,
    )
```

- [ ] **Step 4: Run all tests to confirm pass**

Run: `pytest tests/test_streamlit_app.py -v`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: add product_detail query helper"
```

---

### Task 6: Full UI Rewrite in main()

**Files:**
- Modify: `streamlit_app.py` (replace placeholder `main()` with full UI)

This task wires all data helpers into the Streamlit UI. No new tests — the data helpers are already tested. Verify visually by running the app.

- [ ] **Step 1: Replace the placeholder main() with the full implementation**

Replace the existing `main()` function (everything from `def main():` to `if __name__ == "__main__":`) with:

```python
def main():
    st.set_page_config(
        page_title="ZURU CPG Competitive Intelligence Dashboard",
        layout="wide",
    )

    # ── Connect ──────────────────────────────────────────────────────────
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

    brands = brand_options(conn)
    selection = st.sidebar.selectbox("Brand Filter", ["All Brands"] + brands)
    selected_brand = None if selection == "All Brands" else selection

    start_date, end_date = None, None
    if has_date:
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(date(2026, 1, 1), date.today()),
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_date, end_date = date_range

    # ── Header ───────────────────────────────────────────────────────────
    st.title("ZURU CPG Competitive Intelligence Dashboard")
    st.caption("Competitive product intelligence across ZURU's five CPG verticals")
    st.divider()

    # ── KPI Cards ─────────────────────────────────────────────────────────
    kpis = kpi_summary(conn, selected_brand, start_date, end_date, has_date)
    zuru_count = zuru_product_count(conn)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Products", f"{kpis['total_products']:,}")
    c2.metric("Number of Brands", f"{kpis['num_brands']:,}")
    c3.metric("Number of Categories", f"{kpis['num_categories']:,}")
    c4.metric("ZURU Product Count", f"{zuru_count:,}")

    st.divider()

    # ── Product Trends ────────────────────────────────────────────────────
    if has_date:
        df_trends = trends_time(conn, selected_brand, start_date, end_date)
        if df_trends.empty:
            st.info("No trend data for the selected filters.")
        else:
            fig_trends = px.line(
                df_trends,
                x="WEEK",
                y="PRODUCT_COUNT",
                title="Product Trends Over Time",
                labels={"WEEK": "Week", "PRODUCT_COUNT": "Product Count"},
                color_discrete_sequence=["#2563EB"],
            )
            st.plotly_chart(fig_trends, use_container_width=True)
    else:
        df_trends = trends_vertical(conn, selected_brand)
        if df_trends.empty:
            st.info("No vertical data available.")
        else:
            fig_trends = px.bar(
                df_trends,
                x="VERTICAL",
                y="PRODUCT_COUNT",
                title="Products by ZURU Vertical",
                labels={"VERTICAL": "Vertical", "PRODUCT_COUNT": "Product Count"},
                color_discrete_sequence=["#2563EB"],
            )
            st.plotly_chart(fig_trends, use_container_width=True)

    # ── Top Categories ────────────────────────────────────────────────────
    df_cats = category_counts(conn, selected_brand, start_date, end_date, has_date)
    if df_cats.empty:
        st.info("No category data for the selected filters.")
    else:
        fig_cats = px.bar(
            df_cats,
            x="PRODUCT_COUNT",
            y="CATEGORY",
            orientation="h",
            title="Top Categories by Product Count",
            labels={"CATEGORY": "Category", "PRODUCT_COUNT": "Product Count"},
            color_discrete_sequence=["#2563EB"],
        )
        st.plotly_chart(fig_cats, use_container_width=True)

    # ── Product Details Table ─────────────────────────────────────────────
    st.subheader("Product Details")
    df_detail = product_detail(conn, selected_brand, start_date, end_date, has_date)
    if df_detail.empty:
        st.info("No products match the selected filters.")
    else:
        rename_map = {
            "BRAND_QUERIED": "Brand",
            "PRIMARY_CATEGORY": "Category",
            "VERTICAL": "Vertical",
            "LOADED_AT": "Date",
        }
        df_display = df_detail.rename(columns={k: v for k, v in rename_map.items() if k in df_detail.columns})
        st.dataframe(df_display, use_container_width=True)
```

- [ ] **Step 2: Run the full test suite to confirm nothing broke**

Run: `pytest tests/ -v`
Expected: all tests pass

- [ ] **Step 3: Run the Streamlit app locally to verify the UI**

Run: `streamlit run streamlit_app.py`

Check in browser:
- Sidebar shows "ZURU CPG Intelligence" header, brand dropdown, and date picker (if loaded_at exists)
- 4 KPI cards appear with formatted numbers
- Trends chart appears (line or bar depending on schema)
- Horizontal bar chart shows top categories with largest bar at top
- Product details table shows at bottom with titled columns

- [ ] **Step 4: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: complete dashboard redesign — KPIs, trends, categories, detail table"
```

---

### Task 7: Final Test Run and Clean Up

**Files:**
- No changes

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: all tests pass, no warnings

- [ ] **Step 2: Verify existing extraction tests still pass**

Run: `pytest tests/test_extract_off.py tests/test_extract_zuru.py -v`
Expected: all pass (conftest mock must not break these)

- [ ] **Step 3: Final commit if any cleanup was needed**

```bash
git add -A
git commit -m "chore: final cleanup after dashboard redesign"
```

Only run Step 3 if there are uncommitted changes.
