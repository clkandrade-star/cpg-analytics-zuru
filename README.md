# CPG Analytics — ZURU

End-to-end CPG analytics pipeline built to demonstrate Data Analyst Intern skills at ZURU. Ingests Open Food Facts product data into Snowflake, transforms via a dbt star schema across ZURU Edge's five verticals, and surfaces category intelligence through a Streamlit dashboard.

## Pipeline

```mermaid
flowchart LR
    OFF["Open Food Facts API"]
    GHA["GitHub Actions\n(daily schedule)"]
    RAW["Snowflake\nCPG_ANALYTICS.PUBLIC\nOPEN_FOOD_FACTS"]
    STG["dbt Staging\nstg_products"]
    MART["dbt Mart\nfct_products\ndim_category"]
    DASH["Streamlit\nDashboard"]

    OFF --> GHA --> RAW --> STG --> MART --> DASH
```

```mermaid
flowchart LR
    FC["Firecrawl\nzuru.com crawl"]
    KRAW["knowledge/raw/\nmarkdown files"]
    CC["Claude Code"]
    KWIKI["knowledge/wiki/\nsynthesized pages"]

    FC --> KRAW --> CC --> KWIKI
```

## Star Schema

```mermaid
erDiagram
    fct_products {
        string product_id PK
        string barcode
        string brand_queried FK
        string primary_category FK
        timestamp extracted_at
    }
    dim_brands {
        string brand_id PK
        string brand_name
    }
    dim_categories {
        string category_id PK
        string category_name
    }

    fct_products }o--|| dim_brands : "brand_queried = brand_name"
    fct_products }o--|| dim_categories : "primary_category = category_name"
```

## Stack

| Layer | Tool |
|---|---|
| Extraction | Python (`src/extract_off.py`, `src/extract_zuru.py`) |
| Orchestration | GitHub Actions |
| Data Warehouse | Snowflake (AWS US East 1) |
| Transformation | dbt |
| Dashboard | Streamlit Community Cloud |
| Knowledge Base | Firecrawl + Claude Code |

## Verticals

ZURU Edge's five CPG categories: pet care · baby care · personal care/beauty · home care · health & wellness

## Setup

```bash
pip install -r src/requirements.txt
cp .env.example .env  # fill in Snowflake + Firecrawl credentials
python src/extract_off.py
python src/extract_zuru.py
```

See `.env.example` for required environment variables.
