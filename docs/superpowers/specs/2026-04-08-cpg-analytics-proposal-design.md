# CPG Analytics Proposal Design

**Date:** 2026-04-08
**Author:** Che Andrade
**Status:** Approved

---

## Overview

Build and submit the ISBA-4715 portfolio project proposal for a Data Analyst Intern role at ZURU (Los Angeles, CA). The proposal locks in the job posting, project framing, and initializes the public GitHub repo.

**Proposal due:** Mon, Apr 13 at 9:55 AM

---

## Job Posting

- **Role:** Data Analyst Intern
- **Company:** ZURU (toy and consumer goods, 5K–10K employees, $1B–$5B revenue)
- **Location:** Los Angeles, CA (in-person)
- **Pay:** $20–$25/hr
- **SQL quote:** "Write and execute SQL queries to retrieve information from databases for specific analysis projects, ensuring data integrity and efficiency."
- **Key skills listed:** SQL, Data Visualization, Statistical Analysis, Python Programming, ETL practices

---

## Project Framing

**Project name:** `cpg-analytics-zuru`

**One-sentence pitch:** An end-to-end CPG analytics pipeline that ingests Open Food Facts product data into Snowflake, models it through a dbt star schema, and surfaces category intelligence through a Streamlit dashboard — built to demonstrate the skills required for a data analyst role at a consumer goods company.

**Domain focus:** ZURU Edge's five CPG verticals — pet care, baby care, personal care/beauty, home care, health & wellness.

**Primary data source (API):** Open Food Facts API — 3M+ products, free, no auth required, rich category/brand/ingredient data mapping directly to ZURU Edge's verticals.

**Secondary data source (web scrape):** ZURU Edge brand pages, competitor press releases, CPG industry reports — feeds the knowledge base.

**Transferable to:**
1. CPG data analyst roles (P&G, Unilever, Nestlé, Colgate)
2. Retail/category analytics roles (Target, Whole Foods, CVS)
3. Brand analytics / market research roles (Nielsen, Circana, Kantar)

---

## Reflection Paragraph

> This posting is directly relevant to ISBA-4715 because it requires the exact stack the course teaches: SQL queries for database retrieval, ETL practices for moving data across sources, Python for analysis, and data visualization for delivering insights. The role calls for writing SQL to retrieve and analyze data from databases — skills practiced in every module — and asks for familiarity with ETL, which maps to the GitHub Actions pipeline, Snowflake loading, and dbt transformation layers built in this course. To demonstrate I can do this work, I'll build a CPG category intelligence pipeline that pulls product data from the Open Food Facts API into Snowflake, models it through a dbt star schema across ZURU Edge's five verticals (pet care, baby care, personal care, home care, health & wellness), and surfaces trends through a Streamlit dashboard. This same project transfers directly to CPG analyst roles at companies like P&G, Unilever, or Nestlé, retail category analyst roles at Target or CVS, and market intelligence roles at firms like Nielsen or Circana — any employer where understanding consumer goods category performance is the core job.

---

## Repo Structure (Proposal Milestone)

```
cpg-analytics-zuru/
├── docs/
│   ├── job-posting.pdf
│   └── proposal.pdf
├── .gitignore
└── CLAUDE.md
```

Future milestones will add: `src/`, `dbt/`, `knowledge/`, `streamlit/`

---

## CLAUDE.md Content

```markdown
# CPG Analytics - ZURU

## Project Overview
End-to-end CPG analytics pipeline targeting Data Analyst Intern skills at ZURU.
Ingests Open Food Facts API data into Snowflake, transforms via dbt star schema,
surfaces category intelligence via Streamlit dashboard.

## Tech Stack
- Data Warehouse: Snowflake (AWS US East 1)
- Transformation: dbt
- Orchestration: GitHub Actions
- Dashboard: Streamlit Community Cloud
- AI: Claude Code + Superpowers

## Domain
ZURU Edge's five CPG verticals: pet care, baby care, personal care/beauty,
home care, health & wellness.

## Credentials
All secrets via environment variables. Never commit .env files.
```

---

## Deliverables for Proposal (Due Apr 13)

| # | Deliverable | Details |
|---|---|---|
| 1 | `docs/job-posting.pdf` | ZURU Data Analyst Intern PDF |
| 2 | `docs/proposal.pdf` | 1-page proposal using template, exported as PDF |
| 3 | GitHub repo initialized | Public repo `cpg-analytics-zuru`, `.gitignore`, CLAUDE.md |

---

## .gitignore Requirements

- Python: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`
- dbt: `target/`, `dbt_packages/`, `logs/`
- Secrets: `.env`, `*.env`
- OS: `.DS_Store`, `Thumbs.db`
