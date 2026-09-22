from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.database import init_db, query_df, execute
from app.detection import monitor_transactions
from app.ml import run_anomaly_detection

app = FastAPI(title="AI-AML Guard API", version="3.0.0")
init_db()

class StatusUpdate(BaseModel):
    status: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "AI-AML Guard"}

@app.get("/summary")
def summary():
    tx = query_df("""
        SELECT COUNT(*) AS total_transactions,
               COALESCE(SUM(amount),0) AS total_value,
               SUM(CASE WHEN risk_level='HIGH' THEN 1 ELSE 0 END) AS high_risk
        FROM transactions
    """).iloc[0].to_dict()
    alerts = query_df("SELECT COUNT(*) AS alerts FROM alerts").iloc[0].to_dict()
    return {**tx, **alerts}

@app.get("/transactions")
def transactions(limit: int = 100):
    limit = max(1, min(limit, 1000))
    return query_df(
        "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ).to_dict("records")

@app.get("/alerts")
def alerts(status: str | None = None):
    if status:
        return query_df(
            "SELECT * FROM alerts WHERE status=? ORDER BY created_at DESC",
            (status,)
        ).to_dict("records")
    return query_df("SELECT * FROM alerts ORDER BY created_at DESC").to_dict("records")

@app.get("/customers")
def customers(limit: int = 100):
    limit = max(1, min(limit, 1000))
    return query_df("SELECT * FROM customers LIMIT ?", (limit,)).to_dict("records")

@app.post("/run-monitoring")
def run_monitoring():
    return {"alerts_created": monitor_transactions()}

@app.post("/run-ml")
def run_ml():
    return {"transactions_scored": run_anomaly_detection()}

@app.post("/cases/{case_id}/status")
def update_case(case_id: int, payload: StatusUpdate):
    with __import__("app.database", fromlist=["get_conn"]).get_conn() as conn:
        cur = conn.execute("UPDATE cases SET status=? WHERE case_id=?", (payload.status, case_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Case not found")
        conn.commit()
    return {"case_id": case_id, "status": payload.status}
