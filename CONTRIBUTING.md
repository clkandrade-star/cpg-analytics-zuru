# Contributing

## Branch Strategy

- `main` — always deployable. Protected; merge via PR only.
- Feature branches: `feat/<short-description>` (e.g., `feat/add-nutrition-chart`)
- Bug fixes: `fix/<short-description>`
- dbt model changes: `dbt/<short-description>`

## Making Changes

1. Create a branch from `main`
2. Make your changes (see domain-specific sections below)
3. Run tests locally: `pytest tests/ -v && cd dbt && dbt test`
4. Open a PR against `main` with a description of what changed and why

## Adding or Modifying dbt Models

- Place staging models in `dbt/models/staging/`
- Place mart models in `dbt/models/marts/`
- Every new model needs an entry in the corresponding `schema.yml` with at least one column test
- Run `dbt run && dbt test` before committing
- If you add a new ZURU vertical, also add it to the `accepted_values` test in `dbt/models/marts/schema.yml`

## Modifying the Extraction Scripts

- `src/extract_off.py` — Open Food Facts pipeline. The `VERTICALS` dict at the top of the file maps ZURU vertical names to OFF category tags. Add a new vertical by appending a new key-value pair there.
- `src/extract_zuru.py` — ZURU website scrape via Firecrawl. Requires `FIRECRAWL_API_KEY`.
- Update `tests/test_extract_off.py` or `tests/test_extract_zuru.py` for any logic changes.

## Modifying the Dashboard

- `streamlit_app.py` contains all UI code.
- Query functions use `@st.cache_data(ttl=300)` — 5-minute cache. Adjust `ttl` for freshness vs. performance tradeoffs.
- Test dashboard query logic in `tests/test_streamlit_app.py`.

## SQL Style

- Uppercase SQL keywords (`SELECT`, `FROM`, `WHERE`, `GROUP BY`)
- Lowercase table and column names in dbt models
- One clause per line for multi-condition queries

## Python Style

- Follow PEP 8
- Use type hints for all function signatures
- Functions should do one thing

## Commit Messages

```
type: short description (50 chars max)

Optional longer explanation of why, not what.
```

Types: `feat`, `fix`, `dbt`, `docs`, `test`, `chore`

Examples:
```
feat: add nutrition score chart to dashboard
dbt: add stg_products freshness test
fix: retry on 503 from Open Food Facts API
docs: add SETUP.md
```
