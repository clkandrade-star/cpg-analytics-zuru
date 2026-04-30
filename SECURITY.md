# Security

## Secrets Management

All credentials are passed via environment variables. **Never commit secrets to git.**

Files that must never be committed (already covered by `.gitignore`):
- `.env`
- `dbt/profiles.yml`
- Any file containing API keys, passwords, or Snowflake account identifiers

Use `.env.example` and `dbt/profiles.yml.example` as templates — these contain only placeholder values and are safe to commit.

For GitHub Actions, secrets are stored under **Settings → Secrets and variables → Actions** and injected at runtime. They are never logged or exposed in workflow output.

For Streamlit Community Cloud, secrets are stored in **Advanced settings → Secrets** (TOML format) and are isolated per deployment.

## Data Sensitivity

This project processes only **publicly available product data** from Open Food Facts (openfoodfacts.org), released under the Open Database License (ODbL). No personally identifiable information (PII) is collected, stored, or processed.

The ZURU website scrape (`src/extract_zuru.py`) collects only publicly visible marketing and product content from zuru.com.

## If a Secret Is Accidentally Committed

Rotate the credential immediately — assume it is compromised:

1. Change the password or regenerate the API key in the originating service (Snowflake, Firecrawl)
2. Remove it from git history:
   ```bash
   # Install git-filter-repo (pip install git-filter-repo)
   git filter-repo --path .env --invert-paths
   ```
3. Force-push the cleaned history and notify any collaborators who may have pulled the compromised commit
4. Update the secret in GitHub Actions and Streamlit Community Cloud
