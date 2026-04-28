# Synthesis — Key Themes and Insights

**Sources:** All 22 files in knowledge/raw/

---

## Theme 1: ZURU Edge Is the Strategic Focal Point

All CPG-relevant activity in this project traces back to ZURU Edge. The Toys and Tech divisions have no connection to the data analytics work — the Data Analyst intern role sits squarely within the Edge consumer goods operation. ZURU Edge is described as "arguably the fastest-growing consumer goods company in the world" and its five verticals (pet care, baby care, personal care/beauty, home care, health & wellness) are the analytical categories this pipeline models. Everything in the dashboard and dbt schema should be framed in terms of these five verticals.

---

## Theme 2: The LA Data Analyst Role Is Narrowly Defined

The North America internship page is the only place on zuru.com that mentions "Data Analyst." The exact quote is: *"Our Los Angeles office hires Data Analyst interns."* No further job description is given on this page — it refers applicants to a separate expression-of-interest form. This means the job posting PDF (in `docs/job-posting.pdf`) is the definitive source of required skills, not the website. The website confirms the role exists in LA and is tied to the North America commercial operation (alongside retail sales hubs in Minneapolis and Bentonville/Walmart territory).

---

## Theme 3: Disruption as Core Strategy

ZURU's positioning is explicitly about entering "stale" categories and redefining them. This appears in every major page: "Where categories are stagnant and the next generation of consumers demand more, we are there." For the CPG Analytics project, this means the most valuable analysis is *category intelligence* — identifying where market stagnation exists (high product counts with low brand diversity, or categories dominated by a few brands) vs. where disruption is happening (brand proliferation, new entrants). The dashboard's brand-by-category view directly supports this framing.

---

## Theme 4: Auckland Is the Strategic Brain, LA Is Commercial Execution

ZURU's organisational structure is clearly two-tiered across the internship pages:
- **Auckland** leads global commercial strategy, brand development, marketing, product, and creative (both Business Summer and Creative Summer internships are Auckland-only)
- **Los Angeles** executes North America commercial and data work — the DA intern role is here alongside in-market sales staff

For the portfolio project, this matters: the LA Data Analyst role is closer to *commercial analytics* (supporting sales, category performance, retail execution) than to engineering or brand strategy. The dashboard should emphasise actionable commercial insights — which brands are winning in which categories — rather than infrastructure or methodology.

---

## Theme 5: The ZURU DNA Is a Hiring Filter

The six DNA pillars (Good Humans Only, Collaboration, Radical Candour, Overprepare and Win, Shift the Needle, Compounding Improvement) appear verbatim across every single internship program page. They are not aspirational values — they are explicit screening criteria. Specifically:
- **Overprepare and Win**: the pipeline being fully automated (GitHub Actions), tested, and documented before being "shown" demonstrates this pillar
- **Shift the Needle**: the fail-fast ETL approach (TRUNCATE + INSERT full refresh) and iteration speed (dbt transformations added on top of raw data) embodies this
- **Compounding Improvement**: the project is structured in milestones with incremental delivery — exactly the "2% improvement per week" framing

Interview and cover letter preparation for this role should map project decisions back to these pillars explicitly.

---

## Theme 6: The French Site Adds No New Information

All 11 French-language pages (zuru_fr_*.md) are direct translations of their English counterparts with no additional content, brand names, or data. The knowledge base can treat the French pages as confirmed duplicates.

---

## Insight for the Dashboard

The Streamlit dashboard should answer questions that matter to a CPG commercial team:

1. **Which brands have the most product coverage across verticals?** — supports ranging and assortment decisions
2. **Which categories are over-indexed on a single brand?** — signals vulnerability to disruption (ZURU's core thesis)
3. **How does product density vary by vertical?** — surfaces where Open Food Facts coverage is strong vs. thin (data quality signal)

The current dashboard (product count by brand + product count by category with brand filter) directly addresses questions 1 and 3. A future enhancement could add a brand-by-vertical heatmap for question 2.
