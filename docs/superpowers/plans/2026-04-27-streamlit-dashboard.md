# Streamlit Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `streamlit_app.py` at the repo root — a Streamlit dashboard that connects to Snowflake and shows two bar charts (product count by brand, product count by category) with a sidebar brand filter dropdown.

**Architecture:** Single-file app. Loads `.env` via `python-dotenv`, connects to `CPG_ANALYTICS.DBT_CANDRADE` via `snowflake-connector-python`. Connection cached with `@st.cache_resource`; query results cached with `@st.cache_data(ttl=300)` keyed only on the SQL string (connection passed as `_conn` to exclude it from hashing). Sidebar brand dropdown populates from `fct_products.brand_queried`; both Plotly bar charts re-query using the selected filter.

**Tech Stack:** Python 3.11+, `streamlit`, `snowflake-connector-python`, `plotly`, `pandas`, `python-dotenv`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `streamlit_app.py` | Create (repo root) | Full dashboard: connection, queries, layout, charts |
| `src/requirements.txt` | Modify | Add streamlit, plotly, pandas |

---

## Task 0: Update requirements.txt

**Files:**
- Modify: `src/requirements.txt`

- [ ] **Step 1: Add streamlit, plotly, pandas**

Edit `src/requirements.txt` to append three lines — the file should look like this when done:

```
snowflake-connector-python==4.4.0
requests>=2.32.4
python-dotenv==1.0.1
firecrawl-py==1.9.0
pytest==8.3.5
streamlit
plotly
pandas
```

- [ ] **Step 2: Install the new dependencies**

```bash
pip install streamlit plotly pandas
```

Expected: all three packages install without errors.

- [ ] **Step 3: Commit**

```bash
git add src/requirements.txt
git commit -m "chore: add streamlit, plotly, pandas to requirements"
```

---

## Task 1: Create streamlit_app.py

**Files:**
- Create: `streamlit_app.py` (repo root)

- [ ] **Step 1: Create the file**

Create `streamlit_app.py` at the repo root with this exact content:

```python
import os

import pandas as pd
import plotly.express as px
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DB = "CPG_ANALYTICS"
SCHEMA = "DBT_CANDRADE"


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
def run_query(_conn, sql: str) -> pd.DataFrame:
    cur = _conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    return pd.DataFrame(rows, columns=cols)


def brand_options(conn) -> list[str]:
    df = run_query(
        conn,
        f"SELECT DISTINCT brand_queried FROM {DB}.{SCHEMA}.fct_products "
        "WHERE brand_queried IS NOT NULL ORDER BY brand_queried",
    )
    return df["BRAND_QUERIED"].tolist()


def brand_counts(conn, brand: str | None) -> pd.DataFrame:
    where = f"WHERE brand_queried = '{brand}'" if brand else ""
    return run_query(
        conn,
        f"SELECT brand_queried AS brand, COUNT(*) AS product_count "
        f"FROM {DB}.{SCHEMA}.fct_products {where} "
        "GROUP BY brand_queried ORDER BY product_count DESC LIMIT 30",
    )


def category_counts(conn, brand: str | None) -> pd.DataFrame:
    where = f"WHERE brand_queried = '{brand}'" if brand else ""
    return run_query(
        conn,
        f"SELECT primary_category AS category, COUNT(*) AS product_count "
        f"FROM {DB}.{SCHEMA}.fct_products {where} "
        "GROUP BY primary_category ORDER BY product_count DESC",
    )


st.set_page_config(page_title="CPG Analytics — ZURU", layout="wide")
st.title("CPG Analytics — ZURU")

conn = get_conn()
brands = brand_options(conn)
selection = st.sidebar.selectbox("Brand", ["All Brands"] + brands)
selected_brand = None if selection == "All Brands" else selection

df_brands = brand_counts(conn, selected_brand)
df_cats = category_counts(conn, selected_brand)

st.subheader("Products by Brand")
if df_brands.empty:
    st.info("No data for selected brand.")
else:
    fig_brands = px.bar(
        df_brands,
        x="BRAND",
        y="PRODUCT_COUNT",
        labels={"BRAND": "Brand", "PRODUCT_COUNT": "Product Count"},
    )
    st.plotly_chart(fig_brands, use_container_width=True)

st.subheader("Products by Category")
if df_cats.empty:
    st.info("No data for selected brand.")
else:
    fig_cats = px.bar(
        df_cats,
        x="CATEGORY",
        y="PRODUCT_COUNT",
        labels={"CATEGORY": "Category", "PRODUCT_COUNT": "Product Count"},
    )
    st.plotly_chart(fig_cats, use_container_width=True)
```

**Why `_conn` with underscore:** `@st.cache_data` hashes all arguments to build the cache key. Snowflake connection objects aren't hashable, so prefixing with `_` tells Streamlit to exclude it from hashing. The cache key is then just the SQL string, which is correct — same query string = same cached result.

- [ ] **Step 2: Run the dashboard**

```bash
streamlit run streamlit_app.py
```

Expected: browser opens at `http://localhost:8501`. Page title is "CPG Analytics — ZURU". Sidebar shows a "Brand" dropdown defaulting to "All Brands". Two bar charts appear below with data from Snowflake.

- [ ] **Step 3: Verify the brand filter**

In the sidebar dropdown, select any specific brand. Expected: both charts update immediately — the brand chart shows a single bar for that brand, the category chart shows that brand's product distribution across categories.

- [ ] **Step 4: Verify "All Brands" resets correctly**

Switch the dropdown back to "All Brands". Expected: both charts return to showing aggregate counts across all brands.

- [ ] **Step 5: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add Streamlit CPG analytics dashboard"
```

---

## Final Checklist

- [ ] `streamlit run streamlit_app.py` — dashboard loads without errors
- [ ] Brand chart shows top 30 brands by product count when "All Brands" selected
- [ ] Category chart shows all categories when "All Brands" selected
- [ ] Selecting a specific brand filters both charts to that brand only
- [ ] Switching back to "All Brands" restores the aggregate view
- [ ] `.env` is NOT committed (`git status` shows no `.env` file)
