import json
from datetime import datetime

from src.extract_zuru import build_row


def test_build_row_extracts_url_from_metadata():
    page = {
        "metadata": {"url": "https://zuru.com/edge"},
        "markdown": "# ZURU Edge",
    }
    row = build_row(page, "crawl-abc123", datetime(2026, 4, 26))

    assert row[0] == "https://zuru.com/edge"
    assert row[1] == "crawl-abc123"


def test_build_row_falls_back_to_top_level_url():
    page = {
        "url": "https://zuru.com/about",
        "markdown": "# About",
    }
    row = build_row(page, "crawl-xyz", datetime(2026, 4, 26))

    assert row[0] == "https://zuru.com/about"


def test_build_row_raw_json_is_serialized_page():
    page = {"url": "https://zuru.com", "markdown": "# Home"}
    loaded_at = datetime(2026, 4, 26, 10, 0, 0)

    row = build_row(page, "crawl-001", loaded_at)

    assert json.loads(row[2]) == page


def test_build_row_loaded_at_matches_input():
    page = {"url": "https://zuru.com"}
    loaded_at = datetime(2026, 4, 26, 8, 0, 0)

    row = build_row(page, "crawl-002", loaded_at)

    assert row[3] == loaded_at


def test_build_row_empty_page_returns_empty_url():
    row = build_row({}, "crawl-000", datetime(2026, 4, 26))

    assert row[0] == ""
