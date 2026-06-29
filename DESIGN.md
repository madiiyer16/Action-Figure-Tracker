# Cross-Retailer Matching: Design & Evaluation

This document explains how FigureTrack matches the same physical action figure across
two retailers that describe it differently, why the matcher is built the way it is, and
— most importantly — what its evaluation can and cannot honestly claim. The matching
system is the intellectual core of the project; the scraping and the UI exist to serve
it.

## The problem

FigureTrack compares the **total landed cost** (item price + shipping) of a figure
across BigBadToyStore (BBTS, US) and AmiAmi (Japan). For that comparison to mean
anything, the system has to know that AmiAmi's `figma Fate/Grand Order Berserker/Morgan`
and BBTS's `Fate/Grand Order figma No.560 Berserker (...)` may or may not be the same
product — and decide which. This is an **entity-resolution** problem: reconcile records
that refer to the same real-world entity but were created independently, with no shared
identifier.

It is harder than typical product matching for reasons specific to this domain:

- **Bilingual and romanized titles.** The same figure appears under a Japanese
  romanization on one site and an English name on the other, sometimes sharing few
  tokens.
- **Edition variants are distinct products, not variants to merge.** A "DX Edition" and
  a standard edition of the same character are *different things*. Treating an edition
  token as a soft similarity penalty causes wrong merges; it has to act as a hard veto.
- **Franchise tokens are deceptive.** Two different characters from the same franchise
  (e.g. two *Girls' Frontline 2* figmas) share most of their tokens and look nearly
  identical to naive matching, while being unambiguously different products.
- **Catalog numbers exist on only one side.** BBTS embeds a catalog number ("No.1365")
  in its titles; AmiAmi does not put it in listing titles at all. The one
  language-invariant identifier is therefore unavailable from the data as scraped.
- **Listing-level noise.** Preorder vs in-stock status, scale notation, and bundle/set
  phrasing vary independently of product identity.

## The approach: rule-based, deliberately not ML

The matcher is a five-stage rule-based pipeline: **normalize → block → score → threshold
→ apply.**

**Normalize.** At ingest, each title is lowercased, Unicode-normalized, stripped of
boilerplate ("figure", "action figure", "collectible"), and decomposed into structured
fields: a core token set, an edition-token set (deluxe/exclusive/reissue/...), a parsed
scale, and any catalog number present. Edition tokens are extracted and stored
separately from the core title so they can act as a veto rather than as similarity
noise.

**Block.** To avoid scoring all pairs against all pairs, candidates are generated only
within blocks keyed on manufacturer (after brand-alias normalization — "Good Smile
Company" / "Good Smile" / "GSC" collapse to one token). This keeps comparison sets small
and is the standard blocking step of real entity-resolution systems.

**Score.** Within a block, pairs are scored by Jaccard similarity on the core token
sets, with a scale-agreement bonus and a small price-proximity bonus. An **edition
mismatch forces the score to zero** regardless of title similarity — the hard veto that
keeps DX and standard editions apart. Where a catalog number is present on both sides, an
exact number match is a high-precision shortcut, guarded by a secondary token-overlap
floor so a stray number collision cannot merge unrelated figures.

**Threshold.** Three bands: high scores auto-match; a middle band routes to a manual
review queue (`match_candidates`) rather than guessing; low scores are discarded. The
design deliberately favors **precision over recall** — a wrong merge shows a user two
different products as one, which is far worse than the same figure appearing twice.

**Apply.** Auto-matches set a self-referential `canonicalFigureId`; AmiAmi is preferred
as canonical because it carries the original JPY MSRP. A `canonicalPrisma` query
extension injects a canonical-only filter into every figure read — `findMany`,
`findFirst`, `count`, and `aggregate` — so merged duplicates are invisible everywhere,
including counts and aggregates, not just list pages. The figure detail page collects
listings across the whole cluster and sorts cheapest-first; the watchlist and the
price-alert cron price across the full cluster too.

ML was considered and **deliberately excluded from this component.** An earlier
resale-price predictor was cut because it was bolted on to satisfy an "add ML" goal,
needed secondary-market data the retailers don't provide, and didn't serve the product.
A learned matcher was likewise declined for v1: rule-based fuzzy matching is the correct,
auditable first version, and entity resolution with a learned similarity model only earns
its place once there is a labeled dataset and a failure mode that surface-token matching
genuinely cannot reach. That failure mode does exist (see *Where ML belongs* below) — but
building the learned matcher before establishing the rule-based baseline would have been
the same bolted-on mistake in a new place.

## The fact that reframes the evaluation: severe class imbalance

The single most important property of this problem is its prevalence. Across the labeled
data there are **19 true cross-retailer matches** out of **16,728 possible AmiAmi×BBTS
pairs (51 × 328)** — a positive rate of **0.11%**. At the figure level the picture is
less extreme (19 of 51 AmiAmi figures, ~37%, have a BBTS counterpart, because AmiAmi
stocks mostly popular titles BBTS also carries), but at the pair level the matcher
operates in a space that is 99.89% negative.

This dictates how the system should be evaluated and judged:

- **Precision is the metric that matters; recall is secondary.** In a space this
  imbalanced, a single false positive is a visible, embarrassing wrong-merge on the live
  site, while a missed match merely duplicates a listing. Optimizing for zero false
  positives is the correct objective, not a limitation.
- **A small held-out set cannot meaningfully measure precision here.** Demonstrating a
  very low false-positive rate requires being correct across far more than a few dozen
  negatives; a 40-row holdout is underpowered to distinguish a true zero-FP rate from a
  small nonzero one.
- **Held-out recall is not constructible from this dataset.** With only 19 positives
  total, none can be spared to seal away in a held-out set and still leave enough to
  develop against. This is a real constraint imposed by the problem, not an oversight.

## Evaluation, done honestly

**The precision claim rests on exhaustive inspection, not a sample.** Every one of the
157 candidate pairs that share at least one normalized token was inspected by hand;
all 19 true positives fall within this set, and there were **zero false positives**
across the entire inspected space. The remaining 1,871 zero-token-overlap pairs were
assumed negative and a 25-pair sample confirmed they are cross-franchise/cross-character
(same manufacturer, unrelated figures — e.g. *Ōkami*'s Amaterasu vs a *Rocky* figure).
This is a near-census of the plausibly-matchable space, which is far stronger evidence
than a held-out sample would be: the claim is "every pair that could plausibly match was
checked and none were wrongly merged."

**The gold set was audited, and the audit found label errors in both directions.** Two
pairs labeled as matches were actually different characters sharing only franchise tokens
(the matcher correctly rejected them — it was right and the labels were wrong); two pairs
labeled as non-matches were the same figure split by a naming-convention difference.
All four were corrected. The audit also re-verified all 8 production auto-matches by eye —
all genuine same-figure pairs. The fact that the matcher was, in two cases, more correct
than the data grading it is itself a signal about its precision.

**The held-out set is reported for what it legitimately is.** A 40-row, all-negative
held-out set exists and can serve as a false-positive sanity check on unseen negatives.
It cannot test recall (it has no positives), and given the imbalance above it is too small
to carry the precision claim. The precision claim is carried by the exhaustive inspection;
the holdout is confirmatory only.

### Results

| Metric | Value | Basis |
|---|---|---|
| Precision | 1.000 (0 false positives) | Exhaustive inspection of all 157 token-sharing candidate pairs + sampled zero-overlap pairs |
| Recall (development) | 0.727 on the tuning pool after normalization fixes | Measured on development data; reported as such |
| Held-out recall | Not measurable | Only 19 positives exist; none can be sealed away and still leave a usable development set |
| Production auto-matches | 8, all verified same-figure | Manual re-verification of live `canonicalFigureId` rows |

Recall improved from 0.636 to 0.727 on the tuning pool through three low-risk
normalization fixes (treating "reissue" as non-distinguishing, splitting the compound
"umamusume", normalizing a singular/plural difference), each of which recovered a real
match with **precision held at 1.000.**

### The irreducible residual

After those fixes, the remaining missed matches are not tuning failures — they are the
genuine ceiling of surface-token matching:

- **Naming-convention divergence.** The clearest class is Hatsune Miku listings where
  AmiAmi uses the licensor's official product-line name ("Character Vocal Series 01")
  while BBTS uses the synthesizer brand name ("Vocaloid") as shorthand for the same
  Crypton product line. Both are valid English descriptions of the same thing, but they
  share almost no franchise tokens, so the pair scores below the auto-match threshold.
  No threshold tuning fixes this; the token sets genuinely differ. (Note this is *not* a
  romanization gap — it is two different English vocabularies for the same product line,
  which is a distinct failure mode from cross-lingual divergence.)
- **Upstream data quality.** One miss is a typo in a BBTS title ("Grand Oder" for "Grand
  Order"). This is correctly *not* patched in the matcher — it is a data-quality artifact,
  not a matching-logic problem.

## Where ML belongs (future work)

The vocabulary divergence above is the one place a learned model would genuinely serve
the product rather than decorate it. The current instance is English-to-English (two
naming conventions for the same product line), but the underlying failure is general:
token sets that refer to the same figure while sharing few surface tokens — and as
scrape coverage grows, a genuinely cross-lingual instance (a Japanese-script title vs an
English one) is the more extreme version of the same problem. A similarity model over
title embeddings, or a classifier over pair features, could recognize that two token sets
refer to the same figure despite sharing few surface tokens — exactly what Jaccard
structurally cannot do.
The audited gold set seeds the training data for this directly. This is deferred, not
dismissed: it is the correct *second* version, built on a measured baseline that locates
precisely where it would add value.

A second piece of future work is robustness rather than recall: AmiAmi's catalog number
lives on the product detail page, not in listing titles. Recovering it via a per-item
detail fetch would give the matcher a **language-invariant anchor** — a Nendoroid is
#1365 in any language — which matters most as insurance against the zero-token-overlap
case (a Japanese-script title sharing no tokens with an English one) that does not occur
in the current dataset but is a real risk as the scrape coverage grows.

## What this system demonstrates

The matcher reconciles a sparse, severely imbalanced entity-resolution problem with zero
false positives, established by exhaustive verification rather than an optimistic sample;
it identifies honestly that held-out recall is not measurable from the available data and
explains why; and it locates the exact residual failure mode — vocabulary divergence
between token sets describing the same figure — that motivates the one piece of machine
learning that would genuinely belong here. The 0.11% pair-level prevalence is not a footnote but a finding about the domain:
genuine cross-retailer overlap is rare, which is what makes precision the discipline that
matters.
