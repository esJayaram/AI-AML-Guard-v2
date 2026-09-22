import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from app.config import ANOMALY_CONTAMINATION
from app.database import get_conn, query_df

FEATURES = ["amount", "hour", "customer_tx_count", "customer_avg_amount"]

def run_anomaly_detection():
    df = query_df("SELECT * FROM transactions")
    if df.empty:
        return 0

    df["timestamp_dt"] = pd.to_datetime(df["timestamp"], utc=True)
    df["hour"] = df["timestamp_dt"].dt.hour

    stats = df.groupby("customer_id")["amount"].agg(["count", "mean"]).rename(
        columns={"count": "customer_tx_count", "mean": "customer_avg_amount"}
    )
    df = df.join(stats, on="customer_id")

    X = df[FEATURES].replace([np.inf, -np.inf], np.nan).fillna(0)
    model = IsolationForest(
        n_estimators=200,
        contamination=ANOMALY_CONTAMINATION,
        random_state=42
    )
    model.fit(X)

    raw = -model.decision_function(X)
    score = pd.Series(raw).rank(pct=True).mul(100).round(2)
    df["anomaly_score"] = score.values

    with get_conn() as conn:
        for _, r in df.iterrows():
            final_score = min(
                100,
                round(0.55 * float(r["risk_score"]) + 0.45 * float(r["anomaly_score"]), 2)
            )
            level = "HIGH" if final_score >= 70 else "MEDIUM" if final_score >= 40 else "LOW"
            conn.execute(
                "UPDATE transactions SET anomaly_score=?, risk_score=?, risk_level=? WHERE transaction_id=?",
                (float(r["anomaly_score"]), final_score, level, r["transaction_id"])
            )
        conn.commit()

    return len(df)
