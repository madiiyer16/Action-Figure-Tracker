"""Feature extraction for inference (single figure)."""
from datetime import datetime, timezone

NUMERIC_FEATURES = [
    "days_since_release",
    "price_vs_msrp",
    "in_stock",
    "listing_count",
    "history_count",
    "price_range_pct",
]
CATEGORICAL_FEATURES = ["category", "brand"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def extract_figure_features(figure_id: int, conn) -> dict | None:
    """Return feature dict for one figure, or None if figure not found."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                f.category,
                f.brand,
                f."originalMsrpUsd",
                COALESCE(f."releaseDate", f."createdAt") AS reference_date,
                MIN(l."currentPriceUsd")                  AS min_price,
                BOOL_OR(l."inStock")                      AS any_in_stock,
                COUNT(DISTINCT l.id)                      AS listing_count,
                COUNT(ph.id)                              AS history_count,
                MIN(ph."priceUsd")                        AS min_hist_price,
                MAX(ph."priceUsd")                        AS max_hist_price
            FROM figures f
            LEFT JOIN listings l       ON l."figureId"  = f.id
            LEFT JOIN price_history ph ON ph."listingId" = l.id
            WHERE f.id = %s
            GROUP BY f.id, f.category, f.brand,
                     f."originalMsrpUsd", f."releaseDate", f."createdAt"
            """,
            (figure_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    (
        category, brand, msrp_usd, reference_date,
        min_price, any_in_stock, listing_count, history_count,
        min_hist_price, max_hist_price,
    ) = row

    now = datetime.now(timezone.utc)
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=timezone.utc)
    days_since_release = max(0, (now - reference_date).days)

    if msrp_usd and min_price and float(msrp_usd) > 0:
        price_vs_msrp = float(min_price) / float(msrp_usd)
    else:
        price_vs_msrp = 1.0

    if min_hist_price and max_hist_price and (history_count or 0) >= 2:
        price_range_pct = (
            (float(max_hist_price) - float(min_hist_price))
            / float(min_hist_price)
            * 100
        )
    else:
        price_range_pct = 0.0

    return {
        "days_since_release": days_since_release,
        "price_vs_msrp":      price_vs_msrp,
        "in_stock":           1 if any_in_stock else 0,
        "listing_count":      int(listing_count or 0),
        "history_count":      int(history_count or 0),
        "price_range_pct":    price_range_pct,
        "category":           category or "Other",
        "brand":              brand or "Other",
    }
