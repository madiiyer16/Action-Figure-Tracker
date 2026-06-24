#!/usr/bin/env python3
"""
Backfill retailerSku for existing listings.

Modes:
  --dry-run   Read retailerUrl values, parse SKUs, report results. No DB writes.
  (default)   Write extracted SKUs to listings."retailerSku". Requires the column
              to exist (migration add_retailer_sku must be applied first).

Usage:
  python backfill_sku.py --dry-run    # safe — no writes
  python backfill_sku.py              # writes SKUs to DB
"""

import argparse
import sys

from db import get_conn
from normalize import extract_retailer_sku


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Report parse results without writing to DB")
    args = parser.parse_args()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, retailer, "retailerUrl" FROM listings ORDER BY id')
            rows = cur.fetchall()
    finally:
        conn.close()

    total = len(rows)
    parsed: list[tuple[int, str, str, str]] = []
    failed: list[tuple[int, str, str]] = []

    for row_id, retailer, url in rows:
        sku = extract_retailer_sku(retailer, url)
        if sku:
            parsed.append((row_id, retailer, url, sku))
        else:
            failed.append((row_id, retailer, url))

    print(f"\n=== SKU Backfill Report ===")
    print(f"Total listings : {total}")
    print(f"Parsed OK      : {len(parsed)}  ({len(parsed)/total*100:.1f}%)")
    print(f"Failed to parse: {len(failed)}")

    if failed:
        print(f"\nURLs that could not be parsed ({len(failed)}):")
        for row_id, retailer, url in failed:
            print(f"  id={row_id:>5}  retailer={retailer!r:<8}  url={url!r}")
    else:
        print("\nAll URLs parsed successfully.")

    if args.dry_run:
        print("\n[Dry run — no changes written to DB]")
        return

    # Write mode: column must exist
    conn2 = get_conn()
    try:
        with conn2.cursor() as cur:
            updated = 0
            for row_id, _retailer, _url, sku in parsed:
                cur.execute(
                    'UPDATE listings SET "retailerSku" = %s WHERE id = %s AND "retailerSku" IS NULL',
                    (sku, row_id),
                )
                updated += cur.rowcount
        conn2.commit()
        print(f"\nWritten {updated} SKUs to DB ({len(parsed) - updated} rows already had a SKU)")
    except Exception as e:
        conn2.rollback()
        print(f"\nError writing to DB: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn2.close()


if __name__ == "__main__":
    main()
