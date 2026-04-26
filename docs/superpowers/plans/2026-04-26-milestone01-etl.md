# Milestone 01 — ETL Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two Python ETL scripts that extract raw data from the Open Food Facts API and Firecrawl and load it into Snowflake tables `RAW.PUBLIC.OPEN_FOOD_FACTS` and `RAW.PUBLIC.ZURU_SCRAPE`.

**Architecture:** Two fully standalone scripts in `src/` — no shared modules. Each script loads `.env` credentials, connects to Snowflake, creates the database/schema/table if needed, truncates, and inserts fresh rows (TRUNCATE + INSERT full refresh). Raw data lands as a `VARIANT` column; dbt handles transformation downstream.

**Tech Stack:** Python 3.11+, `snowflake-connector-python`, `requests`, `python-dotenv`, `firecrawl-py`, `pytest`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/__init__.py` | Create (empty) | Makes `src` importable for tests |
| `src/requirements.txt` | Create | Python dependencies |
| `src/extract_off.py` | Create | Open Food Facts → Snowflake |
| `src/extract_zuru.py` | Create | Firecrawl → Snowflake |
| `.env.example` | Create (repo root) | Credential template, safe to commit |
| `tests/__init__.py` | Create (empty) | Makes `tests` a package |
| `tests/test_extract_off.py` | Create | Unit tests for extract_off pure functions |
| `tests/test_extract_zuru.py` | Create | Unit tests for extract_zuru pure functions |

---

## Task 0: Project setup

**Files:**
- Create: `src/__init__.py`
- Create: `src/requirements.txt`
- Create: `.env.example`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create the src/ and tests/ directories with init files**

```bash
mkdir -p src tests
```

Create `src/__init__.py` — empty file:
```python
```

Create `tests/__init__.py` — empty file:
```python
```

- [ ] **Step 2: Create src/requirements.txt**

```
snowflake-connector-python==3.12.2
requests==2.32.3
python-dotenv==1.0.1
firecrawl-py==1.9.0
pytest==8.3.5
```

- [ ] **Step 3: Create .env.example in the repo root**

```
# Snowflake — find your account identifier in your Snowflake URL:
# https://<account>.snowflakecomputing.com
SNOWFLAKE_ACCOUNT=yourorg-youraccount
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=SYSADMIN

# Firecrawl — get your key at app.firecrawl.dev
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxx
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r src/requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 5: Copy .env.example to .env and fill in your real values**

```bash
cp .env.example .env
```

Then open `.env` and set your actual Snowflake credentials and Firecrawl API key. Never commit `.env` — it is already covered by `.gitignore`.

- [ ] **Step 6: Commit**

```bash
git add src/__init__.py src/requirements.txt tests/__init__.py .env.example
git commit -m "chore: add src/ and tests/ scaffolding for Milestone 01"
```

---

## Task 1: extract_off.py — unit tests first

**Files:**
- Create: `tests/test_extract_off.py`
- Create: `src/extract_off.py`

### Tests

- [ ] **Step 1: Write the failing tests**

Create `tests/test_extract_off.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_extract_off.py -v
```

Expected: `ERROR` — `ModuleNotFoundError: No module named 'src.extract_off'`

### Implementation

- [ ] **Step 3: Create src/extract_off.py**

```python
import json
import os
import sys
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

OFF_URL = "https://world.openfoodfacts.org/cgi/search.pl"
PAGE_SIZE = 500


def fetch_products(category_tag: str) -> list:
    params = {
        "action": "process",
        "tagtype_0": "categories",
        "tag_contains_0": "contains",
        "tag_0": category_tag,
        "page_size": PAGE_SIZE,
        "page": 1,
        "json": 1,
    }
    resp = requests.get(OFF_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("products", [])


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
    cur.execute("CREATE DATABASE IF NOT EXISTS RAW")
    cur.execute("USE DATABASE RAW")
    cur.execute("CREATE SCHEMA IF NOT EXISTS PUBLIC")
    cur.execute("USE SCHEMA PUBLIC")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS OPEN_FOOD_FACTS (
            PRODUCT_CODE   VARCHAR(50),
            VERTICAL       VARCHAR(50),
            CATEGORY_TAG   VARCHAR(100),
            RAW_JSON       VARIANT,
            LOADED_AT      TIMESTAMP_NTZ
        )
    """)
    cur.execute("TRUNCATE TABLE OPEN_FOOD_FACTS")


def main():
    try:
        conn = get_snowflake_conn()
    except Exception as e:
        print(f"ERROR: Snowflake connection failed: {e}")
        sys.exit(1)

    cur = conn.cursor()
    setup_table(cur)

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

    cur.close()
    conn.close()
    print(f"Done. {total} total rows loaded into RAW.PUBLIC.OPEN_FOOD_FACTS")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_extract_off.py -v
```

Expected output:
```
tests/test_extract_off.py::test_verticals_covers_all_five_zuru_categories PASSED
tests/test_extract_off.py::test_verticals_values_are_off_category_tags PASSED
tests/test_extract_off.py::test_build_row_extracts_product_code PASSED
tests/test_extract_off.py::test_build_row_sets_vertical_and_tag PASSED
tests/test_extract_off.py::test_build_row_raw_json_is_serialized_product PASSED
tests/test_extract_off.py::test_build_row_loaded_at_matches_input PASSED
tests/test_extract_off.py::test_build_row_missing_code_defaults_to_empty_string PASSED
7 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/extract_off.py tests/test_extract_off.py
git commit -m "feat: add extract_off.py with OFF API → Snowflake loader"
```

### Smoke test

- [ ] **Step 6: Run the script against Snowflake**

```bash
python src/extract_off.py
```

Expected output (takes ~30–60 seconds — the OFF API is slow):
```
Fetching pet_care (en:pet-food)...
  Loaded 500 rows
Fetching baby_care (en:baby-foods)...
  Loaded 500 rows
Fetching personal_care (en:cosmetics)...
  Loaded 500 rows
Fetching home_care (en:household-cleaning)...
  Loaded 500 rows
Fetching health_wellness (en:dietary-supplements)...
  Loaded 500 rows
Done. 2500 total rows loaded into RAW.PUBLIC.OPEN_FOOD_FACTS
```

Row counts may vary by category — fewer than 500 is normal if OFF has limited coverage for that tag.

- [ ] **Step 7: Verify rows landed in Snowflake**

In your Snowflake worksheet, run:
```sql
SELECT VERTICAL, COUNT(*) AS row_count
FROM RAW.PUBLIC.OPEN_FOOD_FACTS
GROUP BY VERTICAL
ORDER BY VERTICAL;
```

Expected: five rows in the result, one per vertical, each with > 0 count.

---

## Task 2: extract_zuru.py — unit tests first

**Files:**
- Create: `tests/test_extract_zuru.py`
- Create: `src/extract_zuru.py`

### Tests

- [ ] **Step 1: Write the failing tests**

Create `tests/test_extract_zuru.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_extract_zuru.py -v
```

Expected: `ERROR` — `ModuleNotFoundError: No module named 'src.extract_zuru'`

### Implementation

- [ ] **Step 3: Create src/extract_zuru.py**

```python
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
    cur.execute("CREATE DATABASE IF NOT EXISTS RAW")
    cur.execute("USE DATABASE RAW")
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

    try:
        conn = get_snowflake_conn()
    except Exception as e:
        print(f"ERROR: Snowflake connection failed: {e}")
        sys.exit(1)

    print(f"Crawling {ZURU_URL} (limit={CRAWL_LIMIT} pages)...")
    try:
        crawl_id, pages = crawl_zuru(api_key)
    except Exception as e:
        print(f"ERROR: Firecrawl failed: {e}")
        sys.exit(1)

    print(f"  Got {len(pages)} pages (crawl_id={crawl_id})")

    cur = conn.cursor()
    setup_table(cur)

    loaded_at = datetime.now(timezone.utc).replace(tzinfo=None)
    insert_sql = (
        "INSERT INTO ZURU_SCRAPE (PAGE_URL, CRAWL_ID, RAW_JSON, LOADED_AT) "
        "SELECT %s, %s, PARSE_JSON(%s), %s"
    )

    for page in pages:
        row = build_row(page, crawl_id, loaded_at)
        cur.execute(insert_sql, row)

    cur.close()
    conn.close()
    print(f"Done. {len(pages)} pages loaded into RAW.PUBLIC.ZURU_SCRAPE")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_extract_zuru.py -v
```

Expected output:
```
tests/test_extract_zuru.py::test_build_row_extracts_url_from_metadata PASSED
tests/test_extract_zuru.py::test_build_row_falls_back_to_top_level_url PASSED
tests/test_extract_zuru.py::test_build_row_raw_json_is_serialized_page PASSED
tests/test_extract_zuru.py::test_build_row_loaded_at_matches_input PASSED
tests/test_extract_zuru.py::test_build_row_empty_page_returns_empty_url PASSED
5 passed
```

- [ ] **Step 5: Run all tests together to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: 12 passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add src/extract_zuru.py tests/test_extract_zuru.py
git commit -m "feat: add extract_zuru.py with Firecrawl → Snowflake loader"
```

### Smoke test

- [ ] **Step 7: Run the script against Snowflake**

```bash
python src/extract_zuru.py
```

Expected output (Firecrawl crawls are async and may take 30–120 seconds):
```
Crawling https://zuru.com (limit=25 pages)...
  Got 25 pages (crawl_id=<some-id>)
Done. 25 pages loaded into RAW.PUBLIC.ZURU_SCRAPE
```

Page count may be fewer than 25 if Firecrawl finds fewer crawlable pages.

- [ ] **Step 8: Verify rows landed in Snowflake**

In your Snowflake worksheet, run:
```sql
SELECT
    PAGE_URL,
    RAW_JSON:metadata:title::STRING AS page_title,
    LOADED_AT
FROM RAW.PUBLIC.ZURU_SCRAPE
ORDER BY LOADED_AT DESC
LIMIT 10;
```

Expected: up to 10 rows, each with a `zuru.com` URL and a page title.

---

## Final Checklist

- [ ] `pytest tests/ -v` — 12 passed, 0 failed
- [ ] `RAW.PUBLIC.OPEN_FOOD_FACTS` has rows for all 5 verticals
- [ ] `RAW.PUBLIC.ZURU_SCRAPE` has rows with valid `zuru.com` URLs
- [ ] `.env` is NOT committed (verify with `git status`)
- [ ] `.env.example` IS committed
- [ ] All code lives in `src/`, no hardcoded credentials anywhere
