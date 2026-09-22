from app.database import init_db, query_df
from app.seed import seed_database
from app.detection import monitor_transactions
from app.ml import run_anomaly_detection
from app.network import network_metrics

def test_seed_creates_data():
    seed_database(n_customers=10, n_transactions=100, seed=7)
    assert len(query_df("SELECT * FROM customers")) == 10
    assert len(query_df("SELECT * FROM transactions")) == 100

def test_rule_monitoring_runs():
    count = monitor_transactions()
    assert count >= 0

def test_ml_scoring_runs():
    count = run_anomaly_detection()
    assert count == 100

def test_network_metrics():
    metrics = network_metrics()
    assert metrics["nodes"] > 0
    assert metrics["edges"] > 0
