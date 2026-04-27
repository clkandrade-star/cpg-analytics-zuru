import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

ZURU_URL = "https://zuru.com"
CRAWL_LIMIT = 25
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge" / "raw"


def slug(url: str) -> str:
    path = re.sub(r"https?://[^/]+", "", url).strip("/")
    slug = re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_")
    return f"zuru_{slug}" if slug else "zuru_homepage"


def main():
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not set in .env")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Crawling {ZURU_URL} (limit={CRAWL_LIMIT} pages)...")
    app = FirecrawlApp(api_key=api_key)
    result = app.crawl_url(
        ZURU_URL,
        params={"limit": CRAWL_LIMIT, "scrapeOptions": {"formats": ["markdown"]}},
    )

    pages_raw = result.data if hasattr(result, "data") else result.get("data", [])
    pages = []
    for page in pages_raw:
        if hasattr(page, "model_dump"):
            pages.append(page.model_dump())
        elif hasattr(page, "dict"):
            pages.append(page.dict())
        else:
            pages.append(dict(page))

    saved = []
    for page in pages:
        url = page.get("metadata", {}).get("url", "") or page.get("url", "")
        markdown = page.get("markdown", "") or ""
        if not markdown.strip():
            continue

        filename = slug(url) + ".md"
        filepath = OUTPUT_DIR / filename

        header = f"# Source: {url}\n\n"
        filepath.write_text(header + markdown, encoding="utf-8")
        saved.append(filename)
        print(f"  Saved {filename}")

    print(f"\nDone. {len(saved)} files written to knowledge/raw/")


if __name__ == "__main__":
    main()
