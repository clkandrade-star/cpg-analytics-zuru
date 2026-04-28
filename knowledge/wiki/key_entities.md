# Key Entities — Products, Brands, Categories

**Sources:** zuru_homepage.md, zuru_internships.md, zuru_internship_beauty_internship_program.md, zuru_internship_internship_program_north_america.md

---

## ZURU Edge Verticals (Categories)

The five CPG verticals that define ZURU Edge's scope. These map directly to the `primary_category` / `VERTICAL` fields in the CPG Analytics pipeline.

| Vertical | Description |
|---|---|
| Pet Care | Products for pet health, nutrition, and care |
| Baby Care | Products for infant and toddler care |
| Personal Care & Beauty | Skincare, haircare, cosmetics, personal hygiene |
| Home Care | Household cleaning, laundry, surface care |
| Health & Wellness | Dietary supplements, vitamins, wellness products |

ZURU Edge's strategy is to enter categories that are "stale" — dominated by legacy incumbents — and disrupt them with new-generation brands that better serve modern consumers.

---

## ZURU Edge Brands

ZURU Edge explicitly describes Personal Care & Beauty as its "largest Beauty brands" vertical (referenced in the Sydney Beauty Internship). No individual brand names are disclosed on the public-facing careers/internships pages — brand names are managed at zuruedge.com. The Auckland team leads brand development and marketing strategy for all Edge verticals globally.

---

## ZURU Toys Brands

Public brand names mentioned directly on zuru.com:
- **Mini Brands™** — miniature collectible consumer goods brands
- **Bunch O Balloons™** — water balloon products
- **XSHOT™** — foam blasters
- **Rainbocorns™** — collectible plush
- **Robo Alive™** — robotic toy animals
- **Smashers™** — collectible smash-open toys
- **5 Surprise™** — mystery capsule collectibles
- **Pets Alive™** — motorized pet toys
- **Fuggler™** — plush toy brand

Entertainment partnerships: Nickelodeon, Disney, Universal Studios, DreamWorks.

---

## Data Entities in the CPG Analytics Pipeline

The Open Food Facts API is the primary data source. It maps to ZURU Edge verticals via category tags:

| ZURU Vertical | OFF Category Tag |
|---|---|
| Pet Care | `en:pet-food` |
| Baby Care | `en:baby-foods` |
| Personal Care | `en:cosmetics` |
| Home Care | `en:household-cleaning` |
| Health & Wellness | `en:dietary-supplements` |

### Snowflake Schema

**RAW layer** (`RAW.PUBLIC.OPEN_FOOD_FACTS`):
- `PRODUCT_CODE` — OFF barcode
- `VERTICAL` — ZURU vertical
- `CATEGORY_TAG` — OFF API tag
- `RAW_JSON` — full product JSON
- `LOADED_AT` — load timestamp

**Mart layer** (`CPG_ANALYTICS.DBT_CANDRADE`):

| Table | Key columns |
|---|---|
| `fct_products` | product_id, barcode, brand_queried, primary_category, extracted_at |
| `dim_brands` | brand_id, brand_name |
| `dim_categories` | category_id, category_name |

---

## North America Data Analyst Role

The target role for this portfolio project. From the North America internship page:
> "Our Los Angeles office hires Data Analyst interns."

This is the only explicit mention of "Data Analyst" on the entire careers site. The role sits within the North America program alongside in-market sales graduates in Minneapolis and Bentonville (Walmart HQ). The LA Data Analyst intern focuses on CPG category intelligence — i.e., exactly what this pipeline produces.
