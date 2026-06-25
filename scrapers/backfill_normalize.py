#!/usr/bin/env python3
"""
Backfill normalizedBrand on figures and normalizedTitle/editionTokens/
itemNumber/scaleParsed on listings for all existing rows.

Run once after migration matching_schema is applied.
Safe to re-run: uses COALESCE-style updates so rows already populated
(from the new ingest path) are skipped.

Usage:
  python backfill_normalize.py --dry-run
  python backfill_normalize.py
"""

import argparse
import sys

from db import get_conn
from normalize import (
    normalize_brand,
    normalize_title,
    extract_edition_tokens,
    extract_item_number,
    extract_scale,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even for rows that already have values (use after normalize.py changes)")
    args = parser.parse_args()

    conn = get_conn()
    try:
        # --- Figures: normalizedBrand ---
        with conn.cursor() as cur:
            if args.force:
                cur.execute('SELECT id, brand FROM figures')
            else:
                cur.execute('SELECT id, brand FROM figures WHERE "normalizedBrand" IS NULL')
            figures = cur.fetchall()

        print(f"Figures needing normalizedBrand: {len(figures)}")
        if not args.dry_run:
            with conn.cursor() as cur:
                for fig_id, brand in figures:
                    nb = normalize_brand(brand)
                    cur.execute(
                        'UPDATE figures SET "normalizedBrand" = %s WHERE id = %s',
                        (nb, fig_id),
                    )
            conn.commit()
            print(f"  Written {len(figures)} normalizedBrand values")

        # --- Listings: normalizedTitle, editionTokens, itemNumber, scaleParsed ---
        with conn.cursor() as cur:
            if args.force:
                cur.execute('SELECT id, "retailerUrl", retailer FROM listings')
            else:
                cur.execute(
                    '''SELECT id, "retailerUrl", retailer
                       FROM listings
                       WHERE "normalizedTitle" IS NULL'''
                )
            listings = cur.fetchall()

        print(f"Listings needing normalization: {len(listings)}")
        if not args.dry_run:
            with conn.cursor() as cur:
                for lst_id, url, _retailer in listings:
                    # Use the URL path as a title proxy for existing rows since
                    # we don't re-have the original scraped name; the URL slug
                    # contains the product name in human-readable form for BBTS,
                    # and gcode for AmiAmi. Future scrapes will use the real title.
                    # For AmiAmi, the gcode is not useful as a normalized title —
                    # leave it NULL so the matcher skips Jaccard for those rows
                    # and relies on item_number or human review instead.
                    cur.execute(
                        '''SELECT f.name, f.brand
                           FROM figures f
                           JOIN listings l ON l."figureId" = f.id
                           WHERE l.id = %s''',
                        (lst_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        continue
                    name, brand = row
                    nt = normalize_title(name)
                    et = extract_edition_tokens(nt)
                    inum = extract_item_number(nt)
                    sp = extract_scale(nt)
                    cur.execute(
                        '''UPDATE listings
                           SET "normalizedTitle" = %s,
                               "editionTokens"   = %s,
                               "itemNumber"      = %s,
                               "scaleParsed"     = %s
                           WHERE id = %s''',
                        (nt, et, inum, sp, lst_id),
                    )
            conn.commit()
            print(f"  Written normalization for {len(listings)} listings")

        if args.dry_run:
            print("\n[Dry run — no changes written]")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
