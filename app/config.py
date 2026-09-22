import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("AML_DB_PATH", "data/aml_guard.db")
ANOMALY_CONTAMINATION = float(os.getenv("AML_ANOMALY_CONTAMINATION", "0.05"))
HIGH_VALUE = float(os.getenv("AML_HIGH_VALUE", "100000"))
VELOCITY_COUNT = int(os.getenv("AML_VELOCITY_COUNT", "5"))
VELOCITY_WINDOW_HOURS = int(os.getenv("AML_VELOCITY_WINDOW_HOURS", "24"))
