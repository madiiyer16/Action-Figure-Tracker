"""
Normalization utilities for figure matching.

Used by:
  - backfill_sku.py   (extract_retailer_sku)
  - db.py ingest path (all functions, after step-5 ingest changes)
  - match.py          (all functions)
"""

import re
from urllib.parse import urlparse, parse_qs


# ---------------------------------------------------------------------------
# Retailer SKU extraction
# ---------------------------------------------------------------------------

def extract_retailer_sku(retailer: str, url: str) -> str | None:
    """
    Extract the stable retailer-assigned product ID from a product URL.
    Returns None if the URL doesn't match the expected shape — caller must
    handle NULL SKUs rather than silently dropping the listing.
    """
    if retailer == "amiami":
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        # gcode is the canonical key; scode appears on some older detail pages
        candidates = params.get("gcode") or params.get("scode")
        return candidates[0] if candidates else None

    if retailer == "bbts":
        parsed = urlparse(url)
        path = parsed.path
        # Current format: /product/name-slug-190332  (trailing product ID)
        match = re.search(r"-(\d{5,7})$", path)
        if match:
            return match.group(1)
        # Legacy format: /Product/VariationDetails/12345[/slug]
        match = re.search(r"/VariationDetails/(\d+)", path, re.IGNORECASE)
        return match.group(1) if match else None

    return None


# ---------------------------------------------------------------------------
# Brand normalization
# ---------------------------------------------------------------------------

_BRAND_ALIASES: dict[str, str] = {
    "good smile company": "good smile",
    "goodsmile company": "good smile",
    "good smile co.": "good smile",
    "goodsmile": "good smile",
    "gsc": "good smile",
    "max factory": "max factory",
    "maxfactory": "max factory",
    "bandai spirits": "bandai",
    "bandai namco": "bandai",
    "bandai namco entertainment": "bandai",
    "kotobukiya": "kotobukiya",
    "alter": "alter",
    "wave": "wave",
    "native": "native",
    "freeing": "freeing",
    "aniplex": "aniplex",
    "fun4all": "fun4all",
    "funko": "funko",
}


def normalize_brand(raw: str) -> str:
    """
    Map raw brand string to a canonical lowercase form.
    Unknown brands pass through lowercased; they form their own block
    and will only be matched against themselves across retailers.
    """
    key = raw.lower().strip()
    return _BRAND_ALIASES.get(key, key)


# ---------------------------------------------------------------------------
# Title normalization  (populated in step 4; used by match.py in step 8)
# ---------------------------------------------------------------------------

# Edition tokens that, if they differ between two listings, veto the match.
_EDITION_PATTERNS = [
    r"\b(reissue|re-issue|re-release|rerelease)\b",
    r"\b(ver\.?\s*\d+|version\s*\d+)\b",
    r"\b(limited\s+edition|ltd\.?\s*ed\.?)\b",
    r"\b(anniversary|anni\.?)\b",
    r"\b(dx|deluxe)\b",
    r"\b(special\s+edition|sp\.?\s*ed\.?)\b",
    r"\bexclusive\b",
]

_SCALE_PATTERN = re.compile(r"\b1\s*/\s*(\d+)\b")

# Words stripped from titles before Jaccard scoring: category keywords,
# common filler, and the brand name itself.
_STRIP_WORDS = frozenset([
    "nendoroid", "figma", "gunpla", "figure", "action", "scale", "model",
    "kit", "statue", "pre-order", "preorder", "new", "the", "a", "an",
    "of", "and", "in", "on", "at", "to", "for", "from",
])


def normalize_title(raw: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    s = raw.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_edition_tokens(normalized_title: str) -> list[str]:
    """
    Return sorted list of edition signals present in the title.
    Two listings are edition-vetoed if their token sets differ.
    """
    tokens = []
    for pattern in _EDITION_PATTERNS:
        match = re.search(pattern, normalized_title, re.IGNORECASE)
        if match:
            tokens.append(match.group(0).lower().strip())
    return sorted(set(tokens))


def extract_item_number(normalized_title: str) -> str | None:
    """
    Extract a Nendoroid/figma item number like '#100' or 'no. 2576'.
    Returns the numeric portion only (e.g. '100', '2576').
    """
    match = re.search(r"(?:#|no\.?\s*)(\d{2,5})\b", normalized_title, re.IGNORECASE)
    return match.group(1) if match else None


def extract_scale(normalized_title: str) -> str | None:
    """Return scale string like '1/7' if present, else None."""
    match = _SCALE_PATTERN.search(normalized_title)
    return f"1/{match.group(1)}" if match else None


def core_title_tokens(normalized_title: str, brand: str | None = None) -> set[str]:
    """
    Token set used for Jaccard scoring: title tokens minus stop words,
    category keywords, edition tokens, and the brand name.
    """
    stop = set(_STRIP_WORDS)
    if brand:
        stop.update(normalize_brand(brand).split())

    # Also strip edition tokens so they don't inflate Jaccard
    edition = set()
    for tok in extract_edition_tokens(normalized_title):
        edition.update(tok.split())

    tokens = set(normalized_title.split()) - stop - edition
    return {t for t in tokens if len(t) > 1}
