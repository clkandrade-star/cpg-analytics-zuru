# CPG Analytics - ZURU

## Project Overview
End-to-end CPG analytics pipeline targeting Data Analyst Intern skills at ZURU.
Ingests Open Food Facts API data into Snowflake, transforms via dbt star schema,
surfaces category intelligence via Streamlit dashboard.

## Job Posting
Role: Data Analyst Intern at ZURU (Los Angeles, CA)
Key skills: SQL, ETL, Python, Data Visualization, Statistical Analysis

## Domain
ZURU Edge's five CPG verticals: pet care, baby care, personal care/beauty,
home care, health & wellness.

## Tech Stack
- Data Warehouse: Snowflake (AWS US East 1)
- Transformation: dbt
- Orchestration: GitHub Actions (scheduled)
- Dashboard: Streamlit Community Cloud
- AI: Claude Code + Superpowers

## Directory Structure
- docs/         proposal, job posting, resume, pipeline diagram
- src/          Python extraction scripts
- dbt/          dbt project (staging + mart models)
- streamlit/    dashboard app
- knowledge/    raw scraped sources + wiki pages

## Credentials
All secrets via environment variables. Never commit .env files, profiles.yml,
or any file containing API keys, Snowflake credentials, or tokens.

## Knowledge Base (added in Milestone 02)
To query the knowledge base, ask Claude Code to read files in knowledge/wiki/
and knowledge/raw/. Wiki pages synthesize insights across sources. Raw files
are the original scraped content. Reference knowledge/index.md for the full list.
