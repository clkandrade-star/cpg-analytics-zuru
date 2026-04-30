# Deployment

## Live Dashboard

The dashboard is live at **https://cpg-analytics-zuru.streamlit.app/** via Streamlit Community Cloud.

## GitHub Actions — Extraction Pipeline

The daily extraction runs automatically via `.github/workflows/extract.yml` at 6am UTC (11pm PT). It can also be triggered manually from the GitHub UI under **Actions → Daily Extract → Run workflow**.

The workflow requires these repository secrets, set under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `SNOWFLAKE_ACCOUNT` | e.g., `myorg-myaccount` (no `.snowflakecomputing.com`) |
| `SNOWFLAKE_USER` | Your Snowflake username |
| `SNOWFLAKE_PASSWORD` | Your Snowflake password |
| `SNOWFLAKE_WAREHOUSE` | e.g., `COMPUTE_WH` |
| `SNOWFLAKE_ROLE` | e.g., `SYSADMIN` |
| `FIRECRAWL_API_KEY` | From app.firecrawl.dev |

## Streamlit Community Cloud Deployment

1. Push this repo to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select the repo → set **Main file path** to `streamlit_app.py`
4. Under **Advanced settings → Secrets**, paste:

```toml
SNOWFLAKE_ACCOUNT = "yourorg-youraccount"
SNOWFLAKE_USER = "your_username"
SNOWFLAKE_PASSWORD = "your_password"
SNOWFLAKE_WAREHOUSE = "COMPUTE_WH"
SNOWFLAKE_ROLE = "SYSADMIN"
```

5. Click **Deploy**. Streamlit installs `requirements.txt` from the repo root automatically.

## Promoting dbt to a Separate Production Schema

The current setup uses `DBT_CANDRADE` as the single schema for both dev and production. To separate them:

1. Add a `prod` output to `~/.dbt/profiles.yml`:

```yaml
cpg_analytics:
  target: dev
  outputs:
    dev:
      schema: DBT_CANDRADE
      # ... rest of connection config
    prod:
      schema: DBT_PROD
      # ... rest of connection config
```

2. Run dbt against prod: `dbt run --target prod`
3. Update `streamlit_app.py:SCHEMA` to point to `DBT_PROD`

## Forcing a Data Refresh (Truncate Before Load)

To truncate the raw table before loading — useful after a schema change or to reset test data:

```bash
TRUNCATE_BEFORE_LOAD=true python src/extract_off.py
```

Or set `TRUNCATE_BEFORE_LOAD=true` as a GitHub Actions secret, then trigger the workflow manually.

## Adding dbt to GitHub Actions

To automate dbt runs after extraction, append to `.github/workflows/extract.yml`:

```yaml
- name: Install dbt
  run: pip install dbt-snowflake

- name: Copy dbt profile
  run: |
    mkdir -p ~/.dbt
    cp dbt/profiles.yml.example ~/.dbt/profiles.yml
  env:
    SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
    SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
    SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
    SNOWFLAKE_WAREHOUSE: ${{ secrets.SNOWFLAKE_WAREHOUSE }}
    SNOWFLAKE_ROLE: ${{ secrets.SNOWFLAKE_ROLE }}

- name: Run dbt
  run: cd dbt && dbt run && dbt test
```
