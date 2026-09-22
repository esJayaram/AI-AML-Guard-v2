from datetime import datetime, timedelta, timezone
import random
import uuid
from app.database import init_db, get_conn

COUNTRIES = ["IN", "US", "GB", "AE", "SG", "DE"]
TYPES = ["TRANSFER", "CARD", "CASH", "WIRE", "ACH"]
CHANNELS = ["ONLINE", "BRANCH", "MOBILE", "ATM"]

def seed_database(n_customers=250, n_transactions=5000, seed=42):
    random.seed(seed)
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM alerts")
        conn.execute("DELETE FROM cases")
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM customers")

        customers = []
        for i in range(n_customers):
            cid = f"C{i+1:05d}"
            customers.append((
                cid,
                f"Customer {i+1}",
                random.choice(COUNTRIES),
                random.choice(["Engineer", "Manager", "Trader", "Consultant", "Student", "Business Owner"]),
                random.randint(30, 3500),
                "LOW"
            ))
        conn.executemany(
            "INSERT INTO customers(customer_id,name,country,occupation,account_age_days,risk_rating) VALUES (?,?,?,?,?,?)",
            customers
        )

        start = datetime.now(timezone.utc) - timedelta(days=60)
        rows = []
        for i in range(n_transactions):
            cid = random.choice(customers)[0]
            cp = f"CP{random.randint(1, 800):05d}"
            amount = round(random.lognormvariate(8.0, 1.0), 2)
            if i % 137 == 0:
                amount = round(random.uniform(100000, 250000), 2)
            if i % 211 == 0:
                amount = round(random.uniform(9000, 9999), 2)
            ts = start + timedelta(minutes=random.randint(0, 60 * 24 * 60))
            rows.append((
                str(uuid.uuid4()), ts.isoformat(), cid, cp, amount,
                "INR", random.choice(TYPES), random.choice(CHANNELS),
                random.choice(COUNTRIES), "Synthetic demo transaction", 0, 0, "LOW"
            ))
        conn.executemany("""
            INSERT INTO transactions(
                transaction_id,timestamp,customer_id,counterparty_id,amount,currency,
                transaction_type,channel,country,description,anomaly_score,risk_score,risk_level
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows)
        conn.commit()
    print(f"Seeded {n_customers} customers and {n_transactions} transactions.")

if __name__ == "__main__":
    seed_database()
