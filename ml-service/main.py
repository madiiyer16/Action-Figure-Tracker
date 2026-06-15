import os
import pickle

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from features import ALL_FEATURES, extract_figure_features

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.environ["DATABASE_URL"]
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

app = FastAPI()


def _load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


class PredictRequest(BaseModel):
    figure_id: int


@app.get("/health")
def health():
    return {"status": "ok", "model_trained": os.path.exists(MODEL_PATH)}


@app.post("/predict")
def predict(req: PredictRequest):
    model = _load_model()
    if model is None:
        return {"status": "insufficient_data"}

    conn = psycopg2.connect(DATABASE_URL)
    try:
        features = extract_figure_features(req.figure_id, conn)
    finally:
        conn.close()

    if features is None:
        return {"status": "insufficient_data"}

    X = pd.DataFrame([features])[ALL_FEATURES]
    change_pct = float(model.predict(X)[0])

    recommendation = "buy" if change_pct > 0 else "wait"
    # tanh maps predicted % change to a [0, 1] confidence proxy
    confidence = float(np.tanh(abs(change_pct) / 15))

    return {
        "status":         "ok",
        "recommendation": recommendation,
        "confidence":     round(confidence, 4),
        "change_pct":     round(change_pct, 2),
    }
