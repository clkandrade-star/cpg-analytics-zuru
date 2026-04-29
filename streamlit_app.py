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
