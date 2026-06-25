#!/usr/bin/env python3
"""
Evaluate the matcher against the gold set.

Usage:
  # Tune threshold against the tuning half only:
  python eval_match.py --gold gold_tuning.csv --sweep

  # Report final numbers on the held-out test half (run ONCE, after threshold is set):
  python eval_match.py --gold gold_test.csv --thresh 0.75

Checkpoint C: do not pass gold_test.csv until the threshold is finalized.
"""

import argparse
import csv
import logging
from collections import defaultdict

from db import get_conn
from normalize import core_title_tokens, extract_scale
from match import score_pair, compute_effective_score, DEFAULT_AUTO_THRESH

log = logging.getLogger(__name__)


def load_gold(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = [r for r in rows if r["is_match"] not in ("0", "1")]
    if missing:
        raise SystemExit(f"ERROR: {len(missing)} rows have no is_match label in {path}")
    return rows


def fetch_figure(conn, fig_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT f.id, f.name, f.brand, f.category,
                   f."normalizedBrand",
                   l.retailer, l."normalizedTitle", l."editionTokens",
                   l."itemNumber", l."scaleParsed", l."currentPriceUsd"
            FROM figures f
            JOIN listings l ON l."figureId" = f.id
            WHERE f.id = %s
        """, (fig_id,))
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None


def precision_recall(tp: int, fp: int, fn: int) -> tuple[float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return p, r


def evaluate_at_thresh(scored_pairs: list[tuple[dict, float]], threshold: float) -> dict:
    """
    Given (gold_row, effective_score) pairs, compute P/R/F1 at a threshold.
    A pair is predicted positive if effective_score >= threshold.
    """
    tp = fp = fn = tn = 0
    for row, eff in scored_pairs:
        label = int(row["is_match"])
        pred  = 1 if eff >= threshold else 0
        if label == 1 and pred == 1: tp += 1
        elif label == 0 and pred == 1: fp += 1
        elif label == 1 and pred == 0: fn += 1
        else: tn += 1

    p, r = precision_recall(tp, fp, fn)
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": p, "recall": r, "f1": f1}


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold",   required=True, help="CSV path (gold_tuning.csv or gold_test.csv)")
    parser.add_argument("--thresh", type=float, default=None,
                        help="Evaluate at this threshold only (for final test-half report)")
    parser.add_argument("--sweep",  action="store_true",
                        help="Sweep thresholds 0.30–0.90 to find the best (tuning only)")
    args = parser.parse_args()

    if not args.thresh and not args.sweep:
        parser.error("Provide --thresh or --sweep")

    rows = load_gold(args.gold)
    log.info("Loaded %d gold pairs from %s", len(rows), args.gold)

    conn = get_conn()
    try:
        figures: dict[int, dict] = {}
        for row in rows:
            for key in ("figure_a_id", "figure_b_id"):
                fid = int(row[key])
                if fid not in figures:
                    fig = fetch_figure(conn, fid)
                    if fig:
                        figures[fid] = fig
                    else:
                        log.warning("Figure %d not found in DB — will score as empty", fid)
                        figures[fid] = {"id": fid, "name": "", "brand": "", "category": "",
                                        "normalizedBrand": None, "retailer": "unknown",
                                        "normalizedTitle": "", "editionTokens": [],
                                        "itemNumber": None, "scaleParsed": None,
                                        "currentPriceUsd": 0}
    finally:
        conn.close()

    # Score all pairs
    auto_thresh = DEFAULT_AUTO_THRESH
    scored: list[tuple[dict, float]] = []
    for row in rows:
        a = figures[int(row["figure_a_id"])]
        b = figures[int(row["figure_b_id"])]
        raw, method, scale_match, price_match = score_pair(a, b)
        eff = compute_effective_score(raw, scale_match, price_match,
                                      auto_thresh, review_thresh=0.0)
        scored.append((row, eff))

    n_pos = sum(1 for r, _ in scored if r["is_match"] == "1")
    n_neg = sum(1 for r, _ in scored if r["is_match"] == "0")
    n_total = len(scored)
    per_call_swing = round(100 / n_pos, 1) if n_pos else float("inf")

    print(f"\nGold set: {n_total} pairs ({n_pos} pos / {n_neg} neg)")
    print(f"Note: with {n_pos} positives, each wrong call ≈ ±{per_call_swing}pp precision/recall\n")

    if args.sweep:
        print(f"{'Thresh':>8} {'Precision':>10} {'Recall':>8} {'F1':>8} {'TP':>5} {'FP':>5} {'FN':>5}")
        print("-" * 60)
        best_f1, best_thresh = 0.0, DEFAULT_AUTO_THRESH
        for t_int in range(25, 96, 5):
            t = t_int / 100
            m = evaluate_at_thresh(scored, t)
            marker = " <--" if m["f1"] > best_f1 else ""
            print(f"{t:8.2f} {m['precision']:10.3f} {m['recall']:8.3f} {m['f1']:8.3f}"
                  f" {m['tp']:5d} {m['fp']:5d} {m['fn']:5d}{marker}")
            if m["f1"] > best_f1:
                best_f1, best_thresh = m["f1"], t
        print(f"\nBest threshold on tuning half: {best_thresh:.2f} (F1={best_f1:.3f})")
        print("Set --thresh to this value when running against gold_test.csv")

    if args.thresh:
        m = evaluate_at_thresh(scored, args.thresh)
        print(f"Results at threshold={args.thresh:.2f}")
        print(f"  Precision : {m['precision']:.3f}  ({m['tp']} TP / {m['tp']+m['fp']} predicted positive)")
        print(f"  Recall    : {m['recall']:.3f}  ({m['tp']} TP / {n_pos} actual positive)")
        print(f"  F1        : {m['f1']:.3f}")
        print(f"  TP={m['tp']} FP={m['fp']} FN={m['fn']} TN={m['tn']}")
        print(f"\n  Sample size caveat: {n_pos} positives → ±{per_call_swing}pp per wrong call")

        if "test" in args.gold:
            print("\n  [Checkpoint C: this is the held-out test report. Do not re-tune after seeing this.]")


if __name__ == "__main__":
    main()
