import json
import os
import sys
from datetime import datetime, timezone

import snowflake.connector
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

ZURU_URL = "https://zuru.com"
CRAWL_LIMIT = 25


def crawl_zuru(api_key: str) -> tuple:
    app = FirecrawlApp(api_key=api_key)
    result = app.crawl_url(
        ZURU_URL,
        params={"limit": CRAWL_LIMIT, "scrapeOptions": {"formats": ["markdown"]}},
    )
    # SDK may return an object (Pydantic) or a dict depending on version
    if hasattr(result, "data"):
        pages_raw = result.data
        crawl_id = getattr(result, "id", "unknown")
    else:
        pages_raw = result.get("data", [])
        crawl_id = result.get("id", "unknown")

    pages = []
    for page in pages_raw:
        if hasattr(page, "model_dump"):
            pages.append(page.model_dump())
        elif hasattr(page, "dict"):
            pages.append(page.dict())
        else:
            pages.append(dict(page))

    return crawl_id, pages


def build_row(page: dict, crawl_id: str, loaded_at: datetime) -> tuple:
    url = page.get("metadata", {}).get("url", "") or page.get("url", "")
    return (
        url,
        crawl_id,
        json.dumps(page),
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
    cur.execute("CREATE SCHEMA IF NOT EXISTS PUBLIC")
    cur.execute("USE SCHEMA PUBLIC")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ZURU_SCRAPE (
            PAGE_URL       VARCHAR(2000),
            CRAWL_ID       VARCHAR(100),
            RAW_JSON       VARIANT,
            LOADED_AT      TIMESTAMP_NTZ
        )
    """)
    cur.execute("TRUNCATE TABLE ZURU_SCRAPE")


def main():
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not set in .env")
        sys.exit(1)

    print(f"Crawling {ZURU_URL} (limit={CRAWL_LIMIT} pages)...")
    try:
        crawl_id, pages = crawl_zuru(api_key)
    except Exception as e:
        print(f"ERROR: Firecrawl failed: {e}")
        sys.exit(1)

    print(f"  Got {len(pages)} pages (crawl_id={crawl_id})")

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
        "INSERT INTO ZURU_SCRAPE (PAGE_URL, CRAWL_ID, RAW_JSON, LOADED_AT) "
        "SELECT %s, %s, PARSE_JSON(%s), %s"
    )

    for page in pages:
        row = build_row(page, crawl_id, loaded_at)
        try:
            cur.execute(insert_sql, row)
        except Exception as e:
            print(f"  WARNING: skipping page {row[0]}: {e}")
            continue

    cur.close()
    conn.close()
    print(f"Done. {len(pages)} pages loaded into CPG_ANALYTICS.PUBLIC.ZURU_SCRAPE")


if __name__ == "__main__":
    main()
