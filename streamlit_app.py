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
