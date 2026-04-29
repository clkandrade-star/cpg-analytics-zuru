import json
import os
import sys
import time
from datetime import datetime, timezone

import requests
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

VERTICALS = {
    "pet_care": "en:pet-food",
    "baby_care": "en:baby-foods",
    "personal_care": "en:cosmetics",
    "home_care": "en:household-cleaning",
    "health_wellness": "en:dietary-supplements",
}

OFF_URL = "https://world.openfoodfacts.org/api/v2/search"
PAGE_SIZE = 500
HEADERS = {"User-Agent": "cpg-analytics-zuru/1.0 (clkandrade2005@gmail.com)"}


def fetch_products(category_tag: str) -> list:
    params = {
        "categories_tags": category_tag,
        "page_size": PAGE_SIZE,
        "page": 1,
    }
    for attempt in range(3):
        resp = requests.get(OFF_URL, params=params, headers=HEADERS, timeout=30)
        if resp.status_code == 503:
            wait = 10 * (attempt + 1)
            print(f"  503 on attempt {attempt + 1}, retrying in {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json().get("products", [])
    resp.raise_for_status()
    return []


def build_row(product: dict, vertical: str, category_tag: str, loaded_at: datetime) -> tuple:
    return (
        product.get("code", ""),
        vertical,
        category_tag,
        json.dumps(product),
        loaded_at,
    )


def get_snowflake_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        role=os.environ.get("SNOWFLAKE_ROLE", "SYSADMIN"),
    )


def setup_table(cur):
    cur.execute("CREATE DATABASE IF NOT EXISTS CPG_ANALYTICS")
    cur.execute("USE DATABASE CPG_ANALYTICS")
    cur.execute("CREATE SCHEMA IF NOT EXISTS RAW")
    cur.execute("USE SCHEMA RAW")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS OPEN_FOOD_FACTS (
            PRODUCT_CODE   VARCHAR(50),
            VERTICAL       VARCHAR(50),
            CATEGORY_TAG   VARCHAR(100),
            RAW_JSON       VARIANT,
            LOADED_AT      TIMESTAMP_NTZ
        )
    """)
    if os.environ.get("TRUNCATE_BEFORE_LOAD", "").lower() == "true":
        cur.execute("TRUNCATE TABLE OPEN_FOOD_FACTS")


def main():
    try:
        conn = get_snowflake_conn()
    except Exception as e:
        print(f"ERROR: Snowflake connection failed: {e}")
        sys.exit(1)

    try:
        cur = conn.cursor()
        setup_table(cur)
    except Exception as e:
        print(f"ERROR: Snowflake setup failed: {e}")
        sys.exit(1)

    loaded_at = datetime.now(timezone.utc).replace(tzinfo=None)
    insert_sql = (
        "INSERT INTO OPEN_FOOD_FACTS "
        "(PRODUCT_CODE, VERTICAL, CATEGORY_TAG, RAW_JSON, LOADED_AT) "
        "SELECT %s, %s, %s, PARSE_JSON(%s), %s"
    )
    total = 0

    for vertical, category_tag in VERTICALS.items():
        print(f"Fetching {vertical} ({category_tag})...")
        try:
            products = fetch_products(category_tag)
        except Exception as e:
            print(f"  WARNING: skipping {vertical}: {e}")
            continue

        for product in products:
            row = build_row(product, vertical, category_tag, loaded_at)
            cur.execute(insert_sql, row)

        print(f"  Loaded {len(products)} rows")
        total += len(products)
        time.sleep(2)

    cur.close()
    conn.close()
    print(f"Done. {total} total rows loaded into CPG_ANALYTICS.RAW.OPEN_FOOD_FACTS")


if __name__ == "__main__":
    main()
