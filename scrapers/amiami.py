"""
AmiAmi scraper — uses Playwright (site is a Nuxt SPA, requests get 403).
Converts JPY prices to USD using the rate in .env.
"""

import os
import re
import time
import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from db import get_conn, upsert_figure, upsert_listing, record_price

log = logging.getLogger(__name__)

RETAILER = "amiami"
BASE_URL = "https://www.amiami.com"
SEARCH_URL = f"{BASE_URL}/eng/search/list/"

SEARCH_TERMS = [
    "nendoroid",
    "figma",
    "good smile",
    "gunpla",
]

JPY_TO_USD = Decimal(os.environ.get("JPY_TO_USD_RATE", "0.0067"))

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def jpy_to_usd(jpy_text: str) -> Decimal | None:
    cleaned = re.sub(r"[^\d]", "", jpy_text)
    try:
        result = (Decimal(cleaned) * JPY_TO_USD).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # Sanity cap: no collectible figure should cost more than $2000 USD
        if result > Decimal("2000"):
            log.warning("jpy_to_usd: suspicious value %s from %r — skipping", result, jpy_text)
            return None
        return result
    except InvalidOperation:
        return None


def _guess_category(name: str) -> str:
    n = name.lower()
    if "nendoroid" in n:
        return "Nendoroid"
    if "figma" in n:
        return "Figma"
    if any(k in n for k in ["hg ", "mg ", "rg ", "pg ", "gunpla", "gundam"]):
        return "Gunpla"
    if any(k in n for k in ["1/7", "1/8", "1/6", "1/4"]):
        return "Scale Figure"
    return "Action Figure"


def scrape_keyword(page, keyword: str) -> list[dict]:
    url = f"{SEARCH_URL}?s_keywords={keyword}&pagemax=40&s_st_list_preorder_available=1&s_st_list_newitem_available=1&s_st_list_backorder_available=1"
    try:
        page.goto(url, wait_until="networkidle", timeout=45000)
    except PWTimeout:
        log.warning("AmiAmi timeout for '%s'", keyword)
        return []
    except Exception as e:
        log.error("AmiAmi navigation error for '%s': %s", keyword, e)
        return []

    results = []
    items = page.query_selector_all("li.newly-added-items__item")
    log.info("AmiAmi '%s': found %d raw items", keyword, len(items))

    for item in items:
        try:
            name_el = item.query_selector(".newly-added-items__item__name")
            brand_el = item.query_selector(".newly-added-items__item__brand")
            price_el = item.query_selector(".newly-added-items__item__price")
            link_el = item.query_selector("a[href]")
            img_el = item.query_selector("img")

            if not name_el or not price_el or not link_el:
                continue

            name = name_el.inner_text().strip()
            brand = brand_el.inner_text().strip() if brand_el else "Unknown"

            # price text is like "6,750 JPY" — strip non-digits for jpy_to_usd
            price_text = price_el.inner_text().strip()
            price_usd = jpy_to_usd(price_text)
            if not name or price_usd is None or price_usd <= 0:
                continue

            href = link_el.get_attribute("href") or ""
            url_full = href if href.startswith("http") else BASE_URL + href

            img_src = img_el.get_attribute("src") if img_el else None
            if img_src and not img_src.startswith("http"):
                img_src = BASE_URL + img_src

            # "nomore" class = item no longer available / sold out
            classes = item.get_attribute("class") or ""
            in_stock = "nomore" not in classes

            results.append({
                "name": name,
                "brand": brand,
                "category": _guess_category(name),
                "price_usd": price_usd,
                "in_stock": in_stock,
                "url": url_full,
                "image_url": img_src or None,
            })
        except Exception as e:
            log.debug("Skipping item: %s", e)

    return results


def run() -> int:
    conn = get_conn()
    total = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=USER_AGENT, locale="en-US")
        page = ctx.new_page()

        try:
            for term in SEARCH_TERMS:
                items = scrape_keyword(page, term)
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
                time.sleep(3)
        finally:
            browser.close()
            conn.close()

    return total
