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
