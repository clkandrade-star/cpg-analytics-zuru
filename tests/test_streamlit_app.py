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
