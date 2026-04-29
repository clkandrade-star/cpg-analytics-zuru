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
