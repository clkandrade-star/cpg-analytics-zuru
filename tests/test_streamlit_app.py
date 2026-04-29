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
