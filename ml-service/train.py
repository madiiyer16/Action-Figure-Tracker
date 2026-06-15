"""
Train the price prediction model.

Requires >= 30 days of price history in the database.
Run from the ml-service directory:  python train.py

Saves model.pkl on success.
"""
import logging
import os
import pickle
import sys
from datetime import timezone

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from features import ALL_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("train")

MIN_HISTORY_DAYS = 30
MIN_EXAMPLES = 50
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
DATABASE_URL = os.environ["DATABASE_URL"]


def fetch_training_data(conn: psycopg2.extensions.connection) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT EXTRACT(EPOCH FROM (MAX(\"recordedAt\") - MIN(\"recordedAt\"))) / 86400 "
            "FROM price_history"
        )
        (span_days,) = cur.fetchone()

    span_days = float(span_days or 0)
    log.info("Price history span: %.1f days", span_days)

    if span_days < MIN_HISTORY_DAYS:
        log.error(
            "Need %d days of history; only have %.1f. "
            "Come back in ~%d more days.",
            MIN_HISTORY_DAYS,
            span_days,
            int(MIN_HISTORY_DAYS - span_days),
        )
        sys.exit(1)

    # For each price point T, find the nearest price point 25–35 days later.
    # That gives us the 30-day future price to use as the training target.
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                f.category,
                f.brand,
                f."originalMsrpUsd",
                COALESCE(f."releaseDate", f."createdAt") AS reference_date,
                ph1."priceUsd"                            AS price_t,
                ph2.price_t30,
                l."inStock",
                (SELECT COUNT(*) FROM listings WHERE "figureId" = f.id) AS listing_count,
                (
                    SELECT COUNT(*) FROM price_history ph3
                    JOIN listings l2 ON l2.id = ph3."listingId"
                    WHERE l2."figureId" = f.id
                ) AS history_count,
                MIN(ph_all."priceUsd") OVER (PARTITION BY l.id) AS min_hist,
                MAX(ph_all."priceUsd") OVER (PARTITION BY l.id) AS max_hist
            FROM price_history ph1
            JOIN listings l ON l.id = ph1."listingId"
            JOIN figures   f ON f.id = l."figureId"
            JOIN LATERAL (
                SELECT ph."priceUsd" AS price_t30
                FROM price_history ph
                WHERE ph."listingId" = ph1."listingId"
                  AND ph."recordedAt" > ph1."recordedAt" + INTERVAL '25 days'
                  AND ph."recordedAt" < ph1."recordedAt" + INTERVAL '35 days'
                ORDER BY ph."recordedAt"
                LIMIT 1
            ) ph2 ON true
            JOIN price_history ph_all ON ph_all."listingId" = l.id
            """
        )
        rows = cur.fetchall()

    if len(rows) < MIN_EXAMPLES:
        log.error(
            "Only %d training examples (need %d). Run more scraper cycles first.",
            len(rows),
            MIN_EXAMPLES,
        )
        sys.exit(1)

    log.info("Fetched %d training rows", len(rows))

    now = pd.Timestamp.now(tz="UTC")
    records = []
    for (
        category, brand, msrp_usd, reference_date,
        price_t, price_t30, in_stock, listing_count, history_count,
        min_hist, max_hist,
    ) in rows:
        price_t = float(price_t)
        if price_t <= 0:
            continue

        ref = pd.Timestamp(reference_date)
        if ref.tzinfo is None:
            ref = ref.tz_localize("UTC")
        days_since_release = max(0, (now - ref).days)

        price_vs_msrp = (
            price_t / float(msrp_usd)
            if msrp_usd and float(msrp_usd) > 0
            else 1.0
        )

        min_h, max_h = float(min_hist or price_t), float(max_hist or price_t)
        price_range_pct = (max_h - min_h) / min_h * 100 if min_h > 0 else 0.0

        target = (float(price_t30) - price_t) / price_t * 100

        records.append({
            "days_since_release": days_since_release,
            "price_vs_msrp":      price_vs_msrp,
            "in_stock":           1 if in_stock else 0,
            "listing_count":      int(listing_count or 0),
            "history_count":      int(history_count or 0),
            "price_range_pct":    price_range_pct,
            "category":           category or "Other",
            "brand":              brand or "Other",
            "target":             target,
        })

    return pd.DataFrame(records)


def build_pipeline() -> Pipeline:
    pre = ColumnTransformer([
        ("num", StandardScaler(),                            NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    return Pipeline([
        ("pre", pre),
        ("model", GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42
        )),
    ])


def main() -> None:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        df = fetch_training_data(conn)
    finally:
        conn.close()

    X = df[ALL_FEATURES]
    y = df["target"]

    pipeline = build_pipeline()

    scores = cross_val_score(pipeline, X, y, cv=5, scoring="r2")
    log.info("CV R² scores: %s  mean=%.3f", np.round(scores, 3), scores.mean())

    pipeline.fit(X, y)
    log.info("Trained on %d examples", len(df))

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    log.info("Saved model to %s", MODEL_PATH)


if __name__ == "__main__":
    main()
