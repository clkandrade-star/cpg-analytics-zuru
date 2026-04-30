# Testing

## Running the Test Suite

```bash
# From repo root, with .venv active
pytest tests/ -v
```

No Snowflake connection required — all Snowflake calls are mocked in `tests/conftest.py`.

## Test Files

| File | What it covers |
|---|---|
| `tests/test_extract_off.py` | `fetch_products()`, `build_row()`, `setup_table()` in `src/extract_off.py` |
| `tests/test_extract_zuru.py` | ZURU Firecrawl extraction logic in `src/extract_zuru.py` |
| `tests/test_streamlit_app.py` | Dashboard query functions and UI computation logic |

`tests/conftest.py` mocks the Streamlit session state and Snowflake connector so tests run offline without credentials.

## Running a Single Test File

```bash
pytest tests/test_extract_off.py -v
```

## Running dbt Tests

dbt schema tests live in `dbt/models/marts/schema.yml` and `dbt/models/sources.yml`. They run against the live Snowflake schema, so credentials must be configured and `dbt run` must have completed first.

```bash
cd dbt
dbt test
```

To test a single model:

```bash
dbt test --select fct_products
```

## dbt Test Coverage

| Model | Tests |
|---|---|
| `fct_products` | `unique` + `not_null` on `product_id`; `not_null` on `barcode`, `brand_queried`, `primary_category`, `loaded_at`; `accepted_values` on `vertical` |
| `dim_brands` | `unique` + `not_null` on `brand_id` and `brand_name` |
| `dim_categories` | `unique` + `not_null` on `category_id` and `category_name` |

## CI

GitHub Actions currently runs only the extraction pipeline — there is no automated pytest or dbt test step. To add tests to CI, append to `.github/workflows/extract.yml`:

```yaml
- name: Run unit tests
  run: pytest tests/ -v
```

dbt tests require live Snowflake credentials and a populated schema, so they are best run manually or in a separate scheduled workflow.
