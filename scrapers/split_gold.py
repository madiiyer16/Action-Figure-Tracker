#!/usr/bin/env python3
"""
Split gold_set.csv into gold_tuning.csv and gold_test.csv.

Stratified 50/50 split preserving positive/negative ratio.
Run once; re-running overwrites the halves.

Checkpoint C: gold_test.csv must not be read by the threshold-tuning
code. Run eval_match.py against gold_tuning.csv only, finalize
threshold, then run once against gold_test.csv and report as-is.
"""

import csv
import random

INPUT   = "gold_set.csv"
TUNING  = "gold_tuning.csv"
TEST    = "gold_test.csv"
SEED    = 42


def main() -> None:
    random.seed(SEED)

    with open(INPUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    positives = [r for r in rows if r["is_match"] == "1"]
    negatives = [r for r in rows if r["is_match"] == "0"]
    unlabeled = [r for r in rows if r["is_match"] == ""]
    if unlabeled:
        raise SystemExit(f"ERROR: {len(unlabeled)} rows have no is_match label. Label them first.")

    random.shuffle(positives)
    random.shuffle(negatives)

    # 50/50 stratified split
    pos_split = len(positives) // 2
    neg_split = len(negatives) // 2

    tuning = positives[:pos_split] + negatives[:neg_split]
    test   = positives[pos_split:] + negatives[neg_split:]

    random.shuffle(tuning)
    random.shuffle(test)

    fields = list(rows[0].keys())
    for path, subset in [(TUNING, tuning), (TEST, test)]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(subset)

    print(f"Split {len(rows)} rows (seed={SEED})")
    print(f"  Tuning : {len(tuning)} rows ({sum(1 for r in tuning if r['is_match']=='1')} pos / {sum(1 for r in tuning if r['is_match']=='0')} neg)")
    print(f"  Test   : {len(test)} rows ({sum(1 for r in test if r['is_match']=='1')} pos / {sum(1 for r in test if r['is_match']=='0')} neg)")
    print(f"\nCheckpoint C: do NOT read {TEST} until threshold is finalized.")


if __name__ == "__main__":
    main()
