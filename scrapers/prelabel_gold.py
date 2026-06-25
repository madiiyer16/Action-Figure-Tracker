#!/usr/bin/env python3
"""
Pre-label gold candidates using name-comparison heuristics.

Decision rules (applied in order):
  1. If characters clearly differ (different names after stripping series) → 0
  2. If edition tokens differ between A and B → 0  (hard negative)
  3. If both titles reference the same character + same edition → 1
  4. If scale agrees and titles are highly similar after stripping series → 1
  5. Otherwise → "" (leave for human review)

Output: gold_set.csv  (fill in any remaining "" rows before running split_gold.py)
"""

import csv
import re

INPUT  = "gold_candidates.csv"
OUTPUT = "gold_set.csv"

# Characters/tokens that mark distinct editions when they appear in one
# side only (not the other)
EDITION_MARKERS = [
    r"\bswimsuit\b",
    r"\bbikini\b",
    r"\bupdated\b",
    r"\bzero suit\b",
    r"\bdx\b",
    r"\breissue\b",
    r"\bcasual\b",
    r"\bjsy\b",
    r"\bjapanese\b",
    r"\beng\b",
    r"\bultimate\b",
    r"ver\s*\.\s*\d+",
    r"\bv\d+\b",
    r"\bsymphony\b",
    r"\bhmo\b",
    r"\bracing\b",
    r"\bworld mine\b",
    r"\bsakura\b",
    r"\bhirohako\b",
    r"\bhakodate\b",
    r"\bhirosaki\b",
    r"\btenor\b",
    r"\bsuit\b",
    r"\barmor\b",
    r"\bwarrior\b",
    r"\bjubilee\b",
    r"\banniversary\b",
]

SERIES_NOISE = re.compile(r"\b(tv anime|manga|game|movie|ova|the|a|an|of|and|"
                          r"figure|complete|scale|model|action|kit|set|box|"
                          r"no\s*\.\s*\d+|sp-\d+|#\d+|\d+/\d+)\b", re.I)


def strip_noise(s: str) -> str:
    s = SERIES_NOISE.sub(" ", s.lower())
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def edition_tokens_in(text: str) -> set[str]:
    found = set()
    for pat in EDITION_MARKERS:
        if re.search(pat, text, re.I):
            found.add(pat)
    return found


def decide(a_name: str, b_name: str) -> tuple[str, str]:
    """Return (is_match, note)."""
    a = a_name.lower()
    b = b_name.lower()

    a_ed = edition_tokens_in(a)
    b_ed = edition_tokens_in(b)

    # Edition conflict: tokens present in one but not the other → 0
    only_a = a_ed - b_ed
    only_b = b_ed - a_ed
    # Reissue alone doesn't conflict (a reissue is still the same product)
    only_a.discard(r"\breissue\b")
    only_b.discard(r"\breissue\b")
    if only_a or only_b:
        return "0", f"edition conflict: A-only={sorted(only_a)} B-only={sorted(only_b)}"

    # Token-overlap on stripped names (exclude series filler)
    a_toks = set(strip_noise(a).split()) - {""}
    b_toks = set(strip_noise(b).split()) - {""}
    if not a_toks or not b_toks:
        return "", "empty token sets after stripping"

    overlap = len(a_toks & b_toks) / len(a_toks | b_toks)

    if overlap >= 0.45:
        return "1", f"token overlap={overlap:.2f}"
    if overlap >= 0.20:
        return "", f"borderline overlap={overlap:.2f} — review"
    return "0", f"low overlap={overlap:.2f}"


def main() -> None:
    with open(INPUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    counts = {"0": 0, "1": 0, "": 0}
    for row in rows:
        label, note = decide(row["figure_a_name"], row["figure_b_name"])
        row["is_match"] = label
        row["notes"] = note
        counts[label] += 1

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT}")
    print(f"  is_match=1  : {counts['1']}")
    print(f"  is_match=0  : {counts['0']}")
    print(f"  needs review: {counts['']}")
    print()
    print("Pairs needing manual review:")
    for r in rows:
        if r["is_match"] == "":
            print(f"  [{float(r['jaccard']):.3f}] {r['figure_a_name']!r}")
            print(f"         vs {r['figure_b_name']!r}")
            print(f"         ({r['notes']})")
            print()


if __name__ == "__main__":
    main()
