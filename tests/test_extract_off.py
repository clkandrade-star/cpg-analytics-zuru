import json
from datetime import datetime

from src.extract_off import VERTICALS, build_row


def test_verticals_covers_all_five_zuru_categories():
    expected = {"pet_care", "baby_care", "personal_care", "home_care", "health_wellness"}
    assert set(VERTICALS.keys()) == expected


def test_verticals_values_are_off_category_tags():
    for tag in VERTICALS.values():
        assert tag.startswith("en:"), f"Expected OFF tag starting with 'en:', got {tag!r}"


def test_build_row_extracts_product_code():
    product = {"code": "0123456789", "product_name": "Test Product"}
    loaded_at = datetime(2026, 4, 26, 0, 0, 0)

    row = build_row(product, "pet_care", "en:pet-food", loaded_at)

    assert row[0] == "0123456789"


def test_build_row_sets_vertical_and_tag():
    product = {"code": "abc"}
    loaded_at = datetime(2026, 4, 26)

    row = build_row(product, "baby_care", "en:baby-foods", loaded_at)

    assert row[1] == "baby_care"
    assert row[2] == "en:baby-foods"


def test_build_row_raw_json_is_serialized_product():
    product = {"code": "xyz", "brands": "Acme", "categories": "en:pet-food"}
    loaded_at = datetime(2026, 4, 26)

    row = build_row(product, "pet_care", "en:pet-food", loaded_at)

    assert json.loads(row[3]) == product


def test_build_row_loaded_at_matches_input():
    product = {"code": "1"}
    loaded_at = datetime(2026, 4, 26, 12, 30, 0)

    row = build_row(product, "home_care", "en:household-cleaning", loaded_at)

    assert row[4] == loaded_at


def test_build_row_missing_code_defaults_to_empty_string():
    product = {"product_name": "No Code Product"}
    row = build_row(product, "health_wellness", "en:dietary-supplements", datetime(2026, 4, 26))

    assert row[0] == ""
