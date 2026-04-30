# Troubleshooting

## Snowflake Connection Errors

**`250001: Failed to connect to DB`** — Wrong `SNOWFLAKE_ACCOUNT`. Check your Snowflake URL: `https://<account>.snowflakecomputing.com`. Use only `<account>` without the `.snowflakecomputing.com` suffix.

**`390100: IP address not allowed`** — Your IP may be blocked by a Snowflake network policy. Log in to the Snowflake UI and check **Admin → Security → Network Policies**.

**`token has expired` on Streamlit Cloud** — The Streamlit app uses `authenticator="snowflake"` (native password auth). If you see this error, verify the password secret is correct in **Advanced settings → Secrets** and re-deploy the app.

**`250003: Your user login has been disabled`** — Too many failed login attempts. Log in to the Snowflake UI as ACCOUNTADMIN to re-enable the user.

## dbt Errors

**`Could not find profile named 'cpg_analytics'`** — The `~/.dbt/profiles.yml` file is missing or has the wrong profile name. Copy `dbt/profiles.yml.example` to `~/.dbt/profiles.yml`.

**`Database 'CPG_ANALYTICS' does not exist`** — Run `python src/extract_off.py` first. The extraction script creates the database and raw table on first run.

**`Relation "CPG_ANALYTICS.DBT_CANDRADE.STG_PRODUCTS" does not exist`** — Run `dbt run` before `dbt test`. Tests validate models that must already be built.

**dbt `accepted_values` test failing on `vertical`** — A new vertical was added to `src/extract_off.py:VERTICALS` but not to the `accepted_values` list in `dbt/models/marts/schema.yml`. Add the new value there.

**`dbt debug` fails with environment variable error** — The profile reads env vars (`SNOWFLAKE_ACCOUNT`, etc.). Make sure your `.env` is loaded: `source .env` (Linux/Mac) or set variables manually before running dbt.

## GitHub Actions Failures

**Workflow fails on `Run extract_off.py`** — Check that all five secrets are set under **Settings → Secrets and variables → Actions**. A missing secret silently becomes an empty string, producing an auth failure with no obvious error message.

**503 errors from Open Food Facts API** — The script retries up to 3 times with increasing delays (10s, 20s, 30s). If all retries fail, that vertical is skipped with a `WARNING` and the run continues. This is expected during OFF maintenance windows — the next scheduled run will catch it.

**Workflow not triggering on schedule** — GitHub disables scheduled workflows on forks and on repos with no recent activity. Trigger manually via **Actions → Daily Extract → Run workflow** to re-enable.

## Streamlit Dashboard

**Blank dashboard / "Could not connect to Snowflake"** — Secrets are missing or malformed in Streamlit Community Cloud. Re-check **Advanced settings → Secrets**. The TOML format requires string values in quotes.

**KPI deltas showing no delta arrow** — The raw table has fewer than two distinct load dates. Run the extraction at least twice on separate days.

**`st.cache_data` serving stale data** — Cache TTL is 300 seconds (5 minutes). Force a fresh query by pressing **R** in the browser or restarting the app from the Streamlit Cloud dashboard.

**`KeyError` on column name** — Column names from Snowflake are returned uppercase. The dashboard references them as `df["COLUMN_NAME"]` (uppercase). If you rename a column in a dbt model, update the corresponding reference in `streamlit_app.py`.

## Python / pytest

**`ModuleNotFoundError: No module named 'snowflake'`** — Virtual environment is not activated, or dependencies were not installed. Run:
```bash
source .venv/bin/activate
pip install -r src/requirements.txt
```

**Tests failing with `ImportError` on `streamlit`** — `streamlit` is in `src/requirements.txt`. Run `pip install -r src/requirements.txt` to install it.

**`conftest.py` fixture not found** — Run pytest from the repo root, not from inside `tests/`:
```bash
# Correct
pytest tests/ -v

# Wrong
cd tests && pytest -v
```
