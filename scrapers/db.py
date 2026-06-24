import os
from decimal import Decimal
from datetime import datetime, timezone
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(
        DATABASE_URL,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )


def upsert_figure(conn, name: str, brand: str, category: str,
                  image_url: str | None = None,
                  normalized_brand: str | None = None) -> int:
    """Return existing figure id or insert and return new id."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT id FROM figures WHERE name = %s AND brand = %s',
            (name, brand),
        )
        row = cur.fetchone()
        if row:
            # Update normalizedBrand if it wasn't set on the first pass
            if normalized_brand:
                cur.execute(
                    'UPDATE figures SET "normalizedBrand" = %s WHERE id = %s AND "normalizedBrand" IS NULL',
                    (normalized_brand, row[0]),
                )
            return row[0]

        cur.execute(
            '''
            INSERT INTO figures (name, brand, category, "imageUrl", "normalizedBrand")
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            ''',
            (name, brand, category, image_url, normalized_brand),
        )
        return cur.fetchone()[0]


def upsert_listing(conn, figure_id: int, retailer: str, url: str,
                   price_usd: Decimal, in_stock: bool,
                   retailer_sku: str | None = None,
                   normalized_title: str | None = None,
                   edition_tokens: list[str] | None = None,
                   item_number: str | None = None,
                   scale_parsed: str | None = None) -> int:
    """
    Insert or update listing, return its id.

    When retailer_sku is provided and matches an existing row, the existing
    figureId is kept — SKU identity is authoritative; the current scrape's
    title parse does not overwrite it. (Checkpoint B)
    """
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        if retailer_sku:
            # Look up by stable SKU key first
            cur.execute(
                'SELECT id FROM listings WHERE retailer = %s AND "retailerSku" = %s',
                (retailer, retailer_sku),
            )
            row = cur.fetchone()
            if row:
                # SKU found — update price/stock/normalized fields only.
                # figureId is NOT updated: the SKU's existing figure identity wins.
                cur.execute(
                    '''
                    UPDATE listings
                    SET "currentPriceUsd" = %s,
                        "inStock"         = %s,
                        "lastScrapedAt"   = %s,
                        "normalizedTitle" = COALESCE(%s, "normalizedTitle"),
                        "editionTokens"   = COALESCE(%s, "editionTokens"),
                        "itemNumber"      = COALESCE(%s, "itemNumber"),
                        "scaleParsed"     = COALESCE(%s, "scaleParsed")
                    WHERE id = %s
                    ''',
                    (price_usd, in_stock, now,
                     normalized_title, edition_tokens, item_number, scale_parsed,
                     row[0]),
                )
                return row[0]

        # New SKU (or no SKU): insert
        cur.execute(
            '''
            INSERT INTO listings
              ("figureId", retailer, "retailerUrl", "retailerSku",
               "currentPriceUsd", "inStock", "lastScrapedAt",
               "normalizedTitle", "editionTokens", "itemNumber", "scaleParsed")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (retailer, "retailerSku") WHERE "retailerSku" IS NOT NULL
            DO UPDATE SET
              "currentPriceUsd" = EXCLUDED."currentPriceUsd",
              "inStock"         = EXCLUDED."inStock",
              "lastScrapedAt"   = EXCLUDED."lastScrapedAt",
              "normalizedTitle" = COALESCE(EXCLUDED."normalizedTitle", listings."normalizedTitle"),
              "editionTokens"   = COALESCE(EXCLUDED."editionTokens", listings."editionTokens"),
              "itemNumber"      = COALESCE(EXCLUDED."itemNumber", listings."itemNumber"),
              "scaleParsed"     = COALESCE(EXCLUDED."scaleParsed", listings."scaleParsed")
            RETURNING id
            ''',
            (figure_id, retailer, url, retailer_sku,
             price_usd, in_stock, now,
             normalized_title, edition_tokens, item_number, scale_parsed),
        )
        return cur.fetchone()[0]


def record_price(conn, listing_id: int, price_usd: Decimal, in_stock: bool) -> None:
    """Append a price history row."""
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO price_history ("listingId", "priceUsd", "inStock") VALUES (%s, %s, %s)',
            (listing_id, price_usd, in_stock),
        )
