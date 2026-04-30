import os
from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        authenticator="snowflake",
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


# ── UI ─────────────────────────────────────────────────────────────────────

ALL_VERTICALS = ["pet_care", "baby_care", "personal_care", "home_care", "health_wellness"]


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

    try:
        cols_available = detect_columns(conn)
    except Exception as e:
        st.error(f"Snowflake query error: {e}")
        st.stop()
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
