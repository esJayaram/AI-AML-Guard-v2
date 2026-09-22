import sqlite3
from pathlib import Path
from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    occupation TEXT,
    account_age_days INTEGER,
    risk_rating TEXT DEFAULT 'LOW'
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    counterparty_id TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    channel TEXT NOT NULL,
    country TEXT NOT NULL,
    description TEXT,
    anomaly_score REAL DEFAULT 0,
    risk_score REAL DEFAULT 0,
    risk_level TEXT DEFAULT 'LOW',
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    risk_score REAL NOT NULL,
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    title TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
"""

def get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.commit()

def query_df(sql, params=()):
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def execute(sql, params=()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
