from datetime import date
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


def test_kpi_delta_returns_deltas_when_two_dates_exist():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({
        "LOAD_DATE": [date(2026, 4, 29), date(2026, 4, 28)],
        "TOTAL_PRODUCTS": [510, 500],
        "NUM_CATEGORIES": [40, 38],
    })
    with patch("streamlit_app.run_query", return_value=df):
        result = streamlit_app.kpi_delta(conn)
    assert result["total_products"] == 10
    assert result["num_categories"] == 2


def test_kpi_delta_returns_none_when_single_date():
    import streamlit_app
    conn = make_conn()
    df = pd.DataFrame({
        "LOAD_DATE": [date(2026, 4, 29)],
        "TOTAL_PRODUCTS": [500],
        "NUM_CATEGORIES": [38],
    })
    with patch("streamlit_app.run_query", return_value=df):
        result = streamlit_app.kpi_delta(conn)
    assert result["total_products"] is None
    assert result["num_categories"] is None


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
