#!/usr/bin/env python3
"""
Generate gold set candidates for manual labeling.

Scores all cross-retailer pairs within each normalizedBrand block using
preliminary Jaccard and item-number signals, then samples a mix of
high/medium/low-scoring pairs to give labelers a representative set.

Output: scrapers/gold_candidates.csv
  - Fill in the `is_match` column: 1 = same physical product, 0 = different
  - The `notes` column is optional (add edition flags, uncertainty, etc.)
  - When done, save as gold_set.csv (the split script reads that file)

Usage:
  python gen_gold_candidates.py
"""

import csv
import random
from collections import defaultdict
from db import get_conn
from normalize import core_title_tokens

OUTFILE = "gold_candidates.csv"

# Sampling targets per score bucket
SAMPLE_HIGH   = 999  # take ALL high-score pairs (caps naturally at ~49)
SAMPLE_MEDIUM = 30   # Jaccard 0.05–0.25
SAMPLE_LOW    = 21   # Jaccard < 0.05


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main() -> None:
    random.seed(42)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT f.id, f.name, f.brand, f."normalizedBrand", f.category,
                       l.retailer, l."retailerSku", l."normalizedTitle",
                       l."itemNumber", l."scaleParsed", l."currentPriceUsd"
                FROM figures f
                JOIN listings l ON l."figureId" = f.id
                WHERE f."canonicalFigureId" IS NULL
                ORDER BY f."normalizedBrand", l.retailer, f.id
            ''')
            rows = cur.fetchall()
    finally:
        conn.close()

    # Build per-brand retailer buckets
    by_brand: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for fig_id, name, brand, nb, cat, retailer, sku, nt, inum, scale, price in rows:
        by_brand[nb or "__unknown"][retailer].append({
            "id": fig_id, "name": name, "brand": brand, "category": cat,
            "retailer": retailer, "sku": sku, "normalized_title": nt or "",
            "item_number": inum, "scale": scale, "price": float(price),
        })

    # Score all cross-retailer pairs
    all_pairs: list[dict] = []
    for brand, retailers in by_brand.items():
        amiami = retailers.get("amiami", [])
        bbts = retailers.get("bbts", [])
        if not amiami or not bbts:
            continue

        for a in amiami:
            toks_a = core_title_tokens(a["normalized_title"], a["brand"])
            for b in bbts:
                toks_b = core_title_tokens(b["normalized_title"], b["brand"])
                j = jaccard(toks_a, toks_b)
                inum_match = (
                    bool(a["item_number"])
                    and a["item_number"] == b["item_number"]
                )
                all_pairs.append({
                    "figure_a_id":       a["id"],
                    "figure_a_name":     a["name"],
                    "figure_a_retailer": a["retailer"],
                    "figure_a_sku":      a["sku"] or "",
                    "figure_b_id":       b["id"],
                    "figure_b_name":     b["name"],
                    "figure_b_retailer": b["retailer"],
                    "figure_b_sku":      b["sku"] or "",
                    "brand_block":       brand,
                    "jaccard":           round(j, 4),
                    "item_number_match": 1 if inum_match else 0,
                    "is_match":          "",
                    "notes":             "",
                })

    all_pairs.sort(key=lambda p: (-p["item_number_match"], -p["jaccard"]))

    # Stratified sample
    high   = [p for p in all_pairs if p["item_number_match"] or p["jaccard"] >= 0.25]
    medium = [p for p in all_pairs if not p["item_number_match"] and 0.05 <= p["jaccard"] < 0.25]
    low    = [p for p in all_pairs if not p["item_number_match"] and p["jaccard"] < 0.05]

    sample_high   = high[:SAMPLE_HIGH]   # take top by score (most informative)
    sample_medium = random.sample(medium, min(SAMPLE_MEDIUM, len(medium)))
    sample_low    = random.sample(low,    min(SAMPLE_LOW,    len(low)))

    gold = sample_high + sample_medium + sample_low
    # Shuffle so labelers don't see score-ordered batches (avoids anchoring bias)
    random.shuffle(gold)

    fields = [
        "figure_a_id", "figure_a_name", "figure_a_retailer", "figure_a_sku",
        "figure_b_id", "figure_b_name", "figure_b_retailer", "figure_b_sku",
        "brand_block", "jaccard", "item_number_match",
        "is_match", "notes",
    ]
    with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(gold)

    print(f"Wrote {len(gold)} candidate pairs to {OUTFILE}")
    print(f"  High-score sample : {len(sample_high)}")
    print(f"  Medium-score sample: {len(sample_medium)}")
    print(f"  Low-score sample  : {len(sample_low)}")
    print(f"\nTotal scored pairs: {len(all_pairs)}")
    print(f"  Item-number matches in full set: {sum(1 for p in all_pairs if p['item_number_match'])}")
    print(f"  Jaccard >= 0.25 : {sum(1 for p in all_pairs if p['jaccard'] >= 0.25)}")
    print(f"  Jaccard 0.05–0.25: {sum(1 for p in all_pairs if 0.05 <= p['jaccard'] < 0.25)}")
    print(f"  Jaccard < 0.05  : {sum(1 for p in all_pairs if p['jaccard'] < 0.05)}")


if __name__ == "__main__":
    main()
