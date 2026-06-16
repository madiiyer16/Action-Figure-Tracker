"""
BigBadToyStore scraper — uses Playwright (site blocks plain HTTP requests).
"""

import time
import logging
from decimal import Decimal, InvalidOperation

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from db import get_conn, upsert_figure, upsert_listing, record_price

log = logging.getLogger(__name__)

RETAILER = "bbts"
BASE_URL = "https://www.bigbadtoystore.com"
SEARCH_URL = f"{BASE_URL}/Search"

SEARCH_TERMS = [
    "nendoroid",
    "figma",
    "scale figure",
    "gunpla",
    "good smile",
    "bandai",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def parse_price(text: str) -> Decimal | None:
    cleaned = text.strip().replace("$", "").replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _guess_category(name: str) -> str:
    n = name.lower()
    if "nendoroid" in n:
        return "Nendoroid"
    if "figma" in n:
        return "Figma"
    if "funko" in n or "pop!" in n:
        return "Funko Pop"
    if any(k in n for k in ["hg ", "mg ", "rg ", "pg ", "gunpla", "gundam"]):
        return "Gunpla"
    if any(k in n for k in ["1/7", "1/8", "1/6", "1/4", "scale"]):
        return "Scale Figure"
    return "Action Figure"


def scrape_keyword(page, keyword: str) -> list[dict]:
    url = f"{SEARCH_URL}?SearchText={keyword}&PageSize=50"
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except PWTimeout:
        log.warning("BBTS timeout for '%s'", keyword)
        return []
    except Exception as e:
        log.error("BBTS navigation error for '%s': %s", keyword, e)
        return []

    items = page.query_selector_all("li.search-results-item")
    log.info("BBTS '%s': found %d raw items", keyword, len(items))
    results = []

    for item in items:
        try:
            name_el = item.query_selector("h3.product-card-title")
            brand_el = item.query_selector(".product-company")
            price_el = item.query_selector(".product-card-price")
            link_el = item.query_selector("a.product-card[href]")
            img_el = item.query_selector(".product-card-img img")

            if not name_el or not price_el or not link_el:
                continue

            name = name_el.inner_text().strip()
            price = parse_price(price_el.inner_text().strip())
            if not name or price is None or price <= 0:
                continue

            # brand text is "By: Good Smile Company" — strip the prefix
            raw_brand = brand_el.inner_text().strip() if brand_el else ""
            brand = raw_brand.removeprefix("By: ").strip() or "Unknown"

            href = link_el.get_attribute("href") or ""
            url_full = href if href.startswith("http") else BASE_URL + href

            img_src = img_el.get_attribute("src") if img_el else None

            # check for out-of-stock tag
            tags = item.query_selector_all(".product-card-tag")
            tag_texts = [t.inner_text().strip().lower() for t in tags]
            in_stock = "out of stock" not in tag_texts

            results.append({
                "name": name,
                "brand": brand,
                "category": _guess_category(name),
                "price_usd": price,
                "in_stock": in_stock,
                "url": url_full,
                "image_url": img_src or None,
            })
        except Exception as e:
            log.debug("Skipping BBTS item: %s", e)

    return results


def run() -> int:
    total = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        try:
            for term in SEARCH_TERMS:
                # Fresh context per keyword — avoids session-based rate limiting
                ctx = browser.new_context(user_agent=USER_AGENT, locale="en-US")
                page = ctx.new_page()
                try:
                    items = scrape_keyword(page, term)
                finally:
                    ctx.close()

                if not items:
                    time.sleep(10)
                    continue

                # Open a fresh connection per keyword batch so it's never idle
                # long enough for Neon to drop it during scraping timeouts.
                conn = get_conn()
                try:
                    for item in items:
                        try:
                            figure_id = upsert_figure(
                                conn, item["name"], item["brand"], item["category"], item.get("image_url")
                            )
                            listing_id = upsert_listing(
                                conn, figure_id, RETAILER, item["url"], item["price_usd"], item["in_stock"]
                            )
                            record_price(conn, listing_id, item["price_usd"], item["in_stock"])
                            conn.commit()
                            total += 1
                        except Exception as e:
                            conn.rollback()
                            log.error("DB error for '%s': %s", item["name"], e)
                finally:
                    conn.close()

                time.sleep(10)  # longer delay between keywords to avoid rate limiting
        finally:
            browser.close()

    return total
