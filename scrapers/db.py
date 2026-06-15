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


def upsert_figure(conn, name: str, brand: str, category: str, image_url: str | None = None) -> int:
    """Return existing figure id or insert and return new id."""
    with conn.cursor() as cur:
        # Check first to avoid duplicates (figures has no unique constraint on name+brand yet)
        cur.execute(
            'SELECT id FROM figures WHERE name = %s AND brand = %s',
            (name, brand),
        )
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            '''
            INSERT INTO figures (name, brand, category, "imageUrl")
            VALUES (%s, %s, %s, %s)
            RETURNING id
            ''',
            (name, brand, category, image_url),
        )
        return cur.fetchone()[0]


def upsert_listing(conn, figure_id: int, retailer: str, url: str, price_usd: Decimal, in_stock: bool) -> int:
    """Insert or update listing, return its id."""
    with conn.cursor() as cur:
        cur.execute(
            '''
            INSERT INTO listings ("figureId", retailer, "retailerUrl", "currentPriceUsd", "inStock", "lastScrapedAt")
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT ("figureId", retailer) DO UPDATE
              SET "currentPriceUsd" = EXCLUDED."currentPriceUsd",
                  "inStock"         = EXCLUDED."inStock",
                  "lastScrapedAt"   = EXCLUDED."lastScrapedAt"
            RETURNING id
            ''',
            (figure_id, retailer, url, price_usd, in_stock, datetime.now(timezone.utc)),
        )
        return cur.fetchone()[0]


def record_price(conn, listing_id: int, price_usd: Decimal, in_stock: bool) -> None:
    """Append a price history row."""
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO price_history ("listingId", "priceUsd", "inStock") VALUES (%s, %s, %s)',
            (listing_id, price_usd, in_stock),
        )
