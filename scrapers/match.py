#!/usr/bin/env python3
"""
Cross-retailer figure matcher.

Pipeline:
  1. Block by normalizedBrand (Gunpla as separate hard block)
  2. Score each cross-retailer pair:
       - Edition veto: editionTokens conflict → score 0 (no-match)
       - Item-number gate: itemNumber match + Jaccard >= 0.35 → auto-match
       - Jaccard on core title tokens is the sole auto-match gate
       - Scale/price bonuses only widen the review band, never push to auto-match
  3. Apply threshold:
       - score >= AUTO_THRESH   → write canonicalFigureId, mark 'matched'
       - score >= REVIEW_THRESH → write to match_candidates as 'pending'
       - below REVIEW_THRESH   → discard

Usage:
  python match.py [--dry-run] [--auto-thresh 0.75] [--review-thresh 0.40]
"""

import argparse
import logging
from decimal import Decimal

from db import get_conn
from normalize import core_title_tokens, extract_scale

log = logging.getLogger(__name__)

DEFAULT_AUTO_THRESH   = 0.75
DEFAULT_REVIEW_THRESH = 0.40

ITEM_NUMBER_JACCARD_GATE = 0.35  # secondary Jaccard gate for item-number auto-match
ITEM_NUMBER_CONFIDENCE   = Decimal("0.9500")

SCALE_BONUS  = Decimal("0.10")
PRICE_BONUS  = Decimal("0.05")
PRICE_WINDOW = 0.30   # ±30% price proximity window

GUNPLA_CATEGORIES = {"Gunpla"}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def fetch_unresolved_figures(conn) -> list[dict]:
    """
    Return all figures that are not yet resolved:
      - canonicalFigureId IS NULL  (not already merged)
      - no accepted/rejected match_candidate row exists for this figure
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT f.id, f.name, f.brand, f.category,
                   f."normalizedBrand", f."canonicalFigureId",
                   l.retailer, l."retailerSku",
                   l."normalizedTitle", l."editionTokens",
                   l."itemNumber", l."scaleParsed",
                   l."currentPriceUsd"
            FROM figures f
            JOIN listings l ON l."figureId" = f.id
            WHERE f."canonicalFigureId" IS NULL
              AND f.id NOT IN (
                SELECT "figureAId" FROM match_candidates
                WHERE status IN ('matched', 'rejected')
                UNION
                SELECT "figureBId" FROM match_candidates
                WHERE status IN ('matched', 'rejected')
              )
            ORDER BY f."normalizedBrand", l.retailer, f.id
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def score_pair(a: dict, b: dict) -> tuple[float, str, bool, bool]:
    """
    Score a candidate pair.
    Returns (score, method, scale_match, price_match).

    score == 0.0 means vetoed (no-match).
    method is 'item_number_v1' | 'jaccard_v1' | 'vetoed'.
    """
    # Edition veto: if either side has edition tokens and they differ → 0
    ed_a = set(a.get("editionTokens") or [])
    ed_b = set(b.get("editionTokens") or [])
    if ed_a and ed_b and ed_a != ed_b:
        return 0.0, "vetoed", False, False

    # Core title tokens for Jaccard
    toks_a = core_title_tokens(a.get("normalizedTitle") or "", a.get("brand"))
    toks_b = core_title_tokens(b.get("normalizedTitle") or "", b.get("brand"))
    j = jaccard(toks_a, toks_b)

    # Item-number auto-match (requires secondary Jaccard gate)
    inum_a = a.get("itemNumber")
    inum_b = b.get("itemNumber")
    if inum_a and inum_b and inum_a == inum_b and j >= ITEM_NUMBER_JACCARD_GATE:
        return float(ITEM_NUMBER_CONFIDENCE), "item_number_v1", False, False

    # Scale agreement (metadata for reviewer; hard veto on mismatch when both present)
    scale_a = a.get("scaleParsed") or extract_scale(a.get("normalizedTitle") or "")
    scale_b = b.get("scaleParsed") or extract_scale(b.get("normalizedTitle") or "")
    scale_match = False
    if scale_a and scale_b:
        if scale_a != scale_b:
            return 0.0, "vetoed", False, False  # hard veto on scale conflict
        scale_match = True

    # Price proximity (metadata only — cannot push score over auto-match line)
    price_match = False
    price_a = float(a.get("currentPriceUsd") or 0)
    price_b = float(b.get("currentPriceUsd") or 0)
    if price_a > 0 and price_b > 0:
        ratio = abs(price_a - price_b) / max(price_a, price_b)
        price_match = ratio <= PRICE_WINDOW

    return j, "jaccard_v1", scale_match, price_match


def compute_effective_score(raw_score: float, scale_match: bool, price_match: bool,
                            auto_thresh: float, review_thresh: float) -> float:
    """
    Apply bonuses — but bonuses can only raise a below-review-floor pair
    into the review band; they cannot push a pair over the auto-match line.
    """
    if raw_score <= 0.0:
        return 0.0

    bonus = 0.0
    if scale_match:
        bonus += float(SCALE_BONUS)
    if price_match:
        bonus += float(PRICE_BONUS)

    effective = raw_score + bonus

    # Cap: bonuses cannot cross the auto-match line
    if raw_score < auto_thresh:
        effective = min(effective, auto_thresh - 0.001)

    return effective


def run(auto_thresh: float, review_thresh: float, dry_run: bool = False) -> None:
    conn = get_conn()
    try:
        figures = fetch_unresolved_figures(conn)
    finally:
        conn.close()

    log.info("Unresolved figures: %d", len(figures))

    # Group by normalizedBrand × retailer
    from collections import defaultdict
    by_brand: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for fig in figures:
        nb = fig.get("normalizedBrand") or "__unknown"
        # Gunpla is a hard block boundary — keep in its own block
        if fig.get("category") in GUNPLA_CATEGORIES:
            nb = "__gunpla"
        by_brand[nb][fig["retailer"]].append(fig)

    auto_matches: list[tuple[dict, dict, float, str]] = []
    review_candidates: list[tuple[dict, dict, float, str, bool, bool]] = []

    for brand, retailers in by_brand.items():
        amiami = retailers.get("amiami", [])
        bbts   = retailers.get("bbts", [])
        if not amiami or not bbts:
            continue

        for a in amiami:
            for b in bbts:
                raw, method, scale_match, price_match = score_pair(a, b)
                if raw <= 0.0:
                    continue

                eff = compute_effective_score(raw, scale_match, price_match,
                                             auto_thresh, review_thresh)

                if eff >= auto_thresh:
                    auto_matches.append((a, b, eff, method))
                elif eff >= review_thresh:
                    review_candidates.append((a, b, eff, method, scale_match, price_match))

    log.info("Auto-matches: %d", len(auto_matches))
    log.info("Review candidates: %d", len(review_candidates))

    if dry_run:
        print(f"\n=== DRY RUN (auto_thresh={auto_thresh}, review_thresh={review_thresh}) ===")
        print(f"Auto-matches   : {len(auto_matches)}")
        print(f"Review queue   : {len(review_candidates)}")
        print("\nAuto-matches:")
        for a, b, score, method in sorted(auto_matches, key=lambda x: -x[2]):
            print(f"  [{score:.4f}] [{method}]")
            print(f"    A (amiami): {a['name']!r}")
            print(f"    B (bbts):   {b['name']!r}")
        print("\nReview queue (top 20):")
        for a, b, score, method, sm, pm in sorted(review_candidates, key=lambda x: -x[2])[:20]:
            flags = []
            if sm: flags.append("scale_match")
            if pm: flags.append("price_match")
            print(f"  [{score:.4f}] [{method}] {', '.join(flags)}")
            print(f"    A (amiami): {a['name']!r}")
            print(f"    B (bbts):   {b['name']!r}")
        return

    # Write results
    conn = get_conn()
    try:
        applied_autos = 0
        for a, b, score, method in auto_matches:
            with conn.cursor() as cur:
                # A (amiami) becomes canonical; B (bbts) points to A
                cur.execute(
                    'UPDATE figures SET "canonicalFigureId" = %s WHERE id = %s AND "canonicalFigureId" IS NULL',
                    (a["id"], b["id"]),
                )
                if cur.rowcount:
                    # Record in match_candidates so reviewers can audit auto-merges
                    cur.execute(
                        """
                        INSERT INTO match_candidates
                          ("figureAId", "figureBId", score, method, status)
                        VALUES (%s, %s, %s, %s, 'matched')
                        ON CONFLICT ("figureAId", "figureBId") DO NOTHING
                        """,
                        (a["id"], b["id"], str(round(score, 4)), method),
                    )
                    applied_autos += 1
            conn.commit()

        inserted_reviews = 0
        for a, b, score, method, sm, pm in review_candidates:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO match_candidates
                      ("figureAId", "figureBId", score, method, status,
                       "scaleMatch", "priceMatch")
                    VALUES (%s, %s, %s, %s, 'pending', %s, %s)
                    ON CONFLICT ("figureAId", "figureBId") DO NOTHING
                    """,
                    (a["id"], b["id"], str(round(score, 4)), method, sm, pm),
                )
                inserted_reviews += cur.rowcount
            conn.commit()

        log.info("Applied auto-matches: %d", applied_autos)
        log.info("Inserted review rows: %d", inserted_reviews)
    finally:
        conn.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--auto-thresh",   type=float, default=DEFAULT_AUTO_THRESH)
    parser.add_argument("--review-thresh", type=float, default=DEFAULT_REVIEW_THRESH)
    args = parser.parse_args()

    run(args.auto_thresh, args.review_thresh, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
