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


def kpi_delta(_conn) -> dict:
    """Day-over-day deltas from the raw table (has LOADED_AT). Returns None per
    key when fewer than two distinct dates exist."""
    df = run_query(
        _conn,
        "SELECT loaded_at::DATE AS load_date, "
        "COUNT(*) AS total_products, "
        "COUNT(DISTINCT category_tag) AS num_categories "
        "FROM CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS "
        "WHERE loaded_at::DATE IN ("
        "  SELECT DISTINCT loaded_at::DATE "
        "  FROM CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS "
        "  ORDER BY loaded_at::DATE DESC LIMIT 2"
        ") "
        "GROUP BY loaded_at::DATE "
        "ORDER BY load_date DESC",
    )
    if len(df) < 2:
        return {"total_products": None, "num_categories": None}
    current, prior = df.iloc[0], df.iloc[1]
    return {
        "total_products": int(current["TOTAL_PRODUCTS"]) - int(prior["TOTAL_PRODUCTS"]),
        "num_categories": int(current["NUM_CATEGORIES"]) - int(prior["NUM_CATEGORIES"]),
    }


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
    has_vertical: bool = False,
) -> pd.DataFrame:
    where, params = _where(brand, start, end, has_date)
    extra = ""
    if has_vertical:
        extra += ", vertical"
    if has_date:
        extra += ", loaded_at"
    return run_query(
        _conn,
        f"SELECT brand_queried, primary_category{extra} "
        f"FROM {DB}.{SCHEMA}.fct_products {where} LIMIT 500",
        params,
    )


# ── UI ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="ZURU CPG Competitive Intelligence Dashboard",
        layout="wide",
    )

    # ── Connect ───────────────────────────────────────────────────────────
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

    # ── Header ────────────────────────────────────────────────────────────
    st.title("ZURU CPG Competitive Intelligence Dashboard")
    st.caption("Competitive product intelligence across ZURU's five CPG verticals")
    st.divider()

    # ── KPI Cards ─────────────────────────────────────────────────────────
    kpis = kpi_summary(conn, selected_brand, start_date, end_date, has_date)
    zuru_count = zuru_product_count(conn)
    deltas = kpi_delta(conn)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Products", f"{kpis['total_products']:,}", delta=deltas["total_products"])
    c2.metric("Number of Brands", f"{kpis['num_brands']:,}")
    c3.metric("Number of Categories", f"{kpis['num_categories']:,}", delta=deltas["num_categories"])
    c4.metric("ZURU Product Count", f"{zuru_count:,}", delta=deltas["total_products"])

    st.divider()

    has_vertical = "vertical" in cols_available

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
    elif has_vertical:
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
    else:
        st.info("No date or vertical column available for trend chart.")

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
    df_detail = product_detail(conn, selected_brand, start_date, end_date, has_date, has_vertical)
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


if __name__ == "__main__":
    main()
