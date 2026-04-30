# Proposal Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and commit the ISBA-4715 project proposal for the ZURU Data Analyst Intern role, initialize the repo structure, and have `docs/proposal.pdf` and `docs/job-posting.pdf` ready to submit by Apr 13.

**Architecture:** All files live in the existing repo at `clkandrade-star/internship` (to be renamed `cpg-analytics-zuru`). No code — this plan is repo scaffolding + document creation. The proposal is written as Markdown, then exported to PDF manually.

**Tech Stack:** Git, GitHub CLI (`gh`), Markdown

---

## File Map

| File | Action |
|---|---|
| `.gitignore` | Modify — add dbt, Snowflake, OS entries |
| `CLAUDE.md` | Create — project context |
| `docs/job-posting.pdf` | Copy from existing PDF in repo root |
| `docs/proposal.md` | Create — filled-in proposal template |
| `docs/proposal.pdf` | Manual export step (browser print-to-PDF) |

---

## Task 1: Rename GitHub Repo

**Files:** none (GitHub settings change)

- [ ] **Step 1: Rename repo via GitHub CLI**

```bash
gh repo rename cpg-analytics-zuru --repo clkandrade-star/internship
```

Expected output:
```
✓ Renamed repository clkandrade-star/cpg-analytics-zuru
```

- [ ] **Step 2: Verify the new remote URL is correct**

```bash
git remote get-url origin
```

Expected: `https://github.com/clkandrade-star/internship` — GitHub auto-redirects, so the old URL still works. Optionally update it:

```bash
git remote set-url origin https://github.com/clkandrade-star/cpg-analytics-zuru
git remote get-url origin
```

Expected: `https://github.com/clkandrade-star/cpg-analytics-zuru`

---

## Task 2: Update .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add dbt, Snowflake, and OS entries to .gitignore**

Append the following block to the bottom of `.gitignore`:

```gitignore
# dbt
target/
dbt_packages/
logs/

# Snowflake / secrets
*.env
profiles.yml

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Verify .gitignore has no conflicts**

```bash
git check-ignore -v target/ .env .DS_Store
```

Expected: each path matched with a rule from `.gitignore`

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add dbt, Snowflake, and OS entries to gitignore"
```

---

## Task 3: Create CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md with project context**

Create `CLAUDE.md` in the repo root with this exact content:

```markdown
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
```

- [ ] **Step 2: Verify file exists and looks correct**

```bash
cat CLAUDE.md
```

Expected: full content printed without errors

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "chore: add CLAUDE.md with project context"
```

---

## Task 4: Set Up docs/ Directory and Copy Job Posting

**Files:**
- Create: `docs/` directory
- Copy: `docs/job-posting.pdf` from `"Data Analyst Intern - Los Angeles, CA - Indeed.com.pdf"`

- [ ] **Step 1: Create docs directory**

```bash
mkdir -p docs
```

- [ ] **Step 2: Copy job posting PDF to docs/**

```bash
cp "Data Analyst Intern - Los Angeles, CA - Indeed.com.pdf" docs/job-posting.pdf
```

- [ ] **Step 3: Verify the file is in place**

```bash
ls docs/
```

Expected: `job-posting.pdf`

- [ ] **Step 4: Commit**

```bash
git add docs/job-posting.pdf
git commit -m "docs: add job posting PDF"
```

---

## Task 5: Create Proposal Markdown

**Files:**
- Create: `docs/proposal.md`

- [ ] **Step 1: Create docs/proposal.md with completed template**

Create `docs/proposal.md` with this exact content:

```markdown
# Project Proposal

**Name:** Che Andrade

**Project Name:** CPG Analytics - ZURU

**GitHub Repo:** https://github.com/clkandrade-star/cpg-analytics-zuru

## Job Posting

- **Role:** Data Analyst Intern
- **Company:** ZURU
- **Link:** https://www.indeed.com/viewjob?jk=8eddb4431727dc39

**SQL requirement (quote the posting):** "Write and execute SQL queries to retrieve
information from databases for specific analysis projects, ensuring data integrity
and efficiency."

## Reflection

This posting is directly relevant to ISBA-4715 because it requires the exact stack
the course teaches: SQL queries for database retrieval, ETL practices for moving data
across sources, Python for analysis, and data visualization for delivering insights.
The role calls for writing SQL to retrieve and analyze data from databases — skills
practiced in every module — and asks for familiarity with ETL, which maps to the
GitHub Actions pipeline, Snowflake loading, and dbt transformation layers built in
this course. To demonstrate I can do this work, I'll build a CPG category intelligence
pipeline that pulls product data from the Open Food Facts API into Snowflake, models
it through a dbt star schema across ZURU Edge's five verticals (pet care, baby care,
personal care, home care, health & wellness), and surfaces trends through a Streamlit
dashboard. This same project transfers directly to CPG analyst roles at companies like
P&G, Unilever, or Nestlé, retail category analyst roles at Target or CVS, and market
intelligence roles at firms like Nielsen or Circana — any employer where understanding
consumer goods category performance is the core job.
```

- [ ] **Step 2: Verify the file renders correctly**

```bash
cat docs/proposal.md
```

Expected: full proposal content printed without errors

- [ ] **Step 3: Commit**

```bash
git add docs/proposal.md
git commit -m "docs: add proposal markdown"
```

---

## Task 6: Export Proposal to PDF

**Files:**
- Create: `docs/proposal.pdf` (manual export)

This step requires manual action — the PDF must be exported from the Markdown.

- [ ] **Step 1: Export proposal.md to PDF**

**Option A (VS Code — recommended):**
1. Open `docs/proposal.md` in VS Code
2. Install the "Markdown PDF" extension if not already installed
3. Right-click in the editor → "Markdown PDF: Export (pdf)"
4. The PDF will be saved to `docs/proposal.pdf` automatically

**Option B (Browser print):**
1. Open `docs/proposal.md` in a Markdown preview tool or GitHub
2. Print to PDF using browser (Ctrl+P → Save as PDF)
3. Save to `docs/proposal.pdf`

- [ ] **Step 2: Verify the PDF exists**

```bash
ls -lh docs/proposal.pdf
```

Expected: file exists, size > 0

- [ ] **Step 3: Commit**

```bash
git add docs/proposal.pdf
git commit -m "docs: add proposal PDF"
```

---

## Task 7: Push and Verify Public Repo

**Files:** none (git push)

- [ ] **Step 1: Push all commits to GitHub**

```bash
git push origin main
```

Expected:
```
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

- [ ] **Step 2: Verify repo is public and all files are visible**

```bash
gh repo view clkandrade-star/cpg-analytics-zuru --web
```

Expected: browser opens to the repo. Confirm:
- Repo name is `cpg-analytics-zuru`
- `CLAUDE.md` is visible
- `docs/job-posting.pdf` is visible
- `docs/proposal.pdf` is visible
- `.gitignore` is committed
- No `.env` or credentials anywhere

- [ ] **Step 3: Confirm repo is public**

```bash
gh repo view clkandrade-star/cpg-analytics-zuru --json visibility --jq '.visibility'
```

Expected: `PUBLIC`

If private, make it public:
```bash
gh repo edit clkandrade-star/cpg-analytics-zuru --visibility public
```

---

## Submission Checklist

Before submitting the repo URL to Brightspace:

- [ ] `docs/job-posting.pdf` committed and visible on GitHub
- [ ] `docs/proposal.pdf` committed and visible on GitHub
- [ ] `CLAUDE.md` committed with project context
- [ ] `.gitignore` covers `.env`, `target/`, `dbt_packages/`, `profiles.yml`
- [ ] Repo name is `cpg-analytics-zuru` (professional, descriptive)
- [ ] Repo is **public**
- [ ] Submit repo URL to Brightspace by **Mon Apr 13 at 9:55 AM**
