from datetime import datetime, timezone
import pandas as pd
import numpy as np
from app.database import get_conn, query_df
from app.config import HIGH_VALUE, VELOCITY_COUNT, VELOCITY_WINDOW_HOURS

def load_transactions():
    return query_df("""
        SELECT t.*, c.country AS customer_country
        FROM transactions t
        JOIN customers c ON c.customer_id=t.customer_id
    """)

def monitor_transactions():
    df = load_transactions()
    if df.empty:
        return 0

    df["timestamp_dt"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values(["customer_id", "timestamp_dt"]).copy()
    # Count each customer's transactions inside the preceding rolling time window.
    # Implemented with sorted integer timestamps to avoid pandas version-specific
    # grouped time-window behaviour.
    window_ns = VELOCITY_WINDOW_HOURS * 60 * 60 * 1_000_000_000
    velocity = np.ones(len(df), dtype=int)
    for _, group in df.groupby("customer_id", sort=False):
        positions = group.index.to_numpy()
        times = group["timestamp_dt"].astype("int64").to_numpy()
        left = np.searchsorted(times, times - window_ns, side="left")
        right = np.arange(len(times)) + 1
        velocity[positions] = right - left
    df["velocity_count"] = velocity

    alerts = []
    with get_conn() as conn:
        for _, r in df.iterrows():
            reasons = []
            score = 0

            if r["amount"] >= HIGH_VALUE:
                score += 45
                reasons.append("High-value transaction")
            if 9000 <= r["amount"] < 10000:
                score += 25
                reasons.append("Amount near reporting threshold")
            if r["velocity_count"] >= VELOCITY_COUNT:
                score += 25
                reasons.append("High transaction velocity")
            if r["country"] != r["customer_country"]:
                score += 10
                reasons.append("Cross-border activity")
            if r["transaction_type"] == "CASH" and r["amount"] > 50000:
                score += 20
                reasons.append("Large cash transaction")

            score = min(score, 100)
            level = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"

            conn.execute(
                "UPDATE transactions SET risk_score=?, risk_level=? WHERE transaction_id=?",
                (score, level, r["transaction_id"])
            )

            if score >= 40:
                severity = "CRITICAL" if score >= 80 else "HIGH" if score >= 60 else "MEDIUM"
                alerts.append((
                    r["transaction_id"], r["customer_id"], "RULE_MONITORING",
                    severity, score, "; ".join(reasons),
                    datetime.now(timezone.utc).isoformat()
                ))

        conn.execute("DELETE FROM alerts")
        conn.executemany("""
            INSERT INTO alerts(
                transaction_id,customer_id,alert_type,severity,risk_score,reason,created_at
            ) VALUES (?,?,?,?,?,?,?)
        """, alerts)
        conn.commit()

    return len(alerts)
