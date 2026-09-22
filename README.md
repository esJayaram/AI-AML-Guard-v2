# AI-AML Guard v2

An original, portfolio-ready Anti-Money Laundering (AML) transaction monitoring and analytics application.

## Visual analytics included

- KPI cards: transactions, transaction value, alerts, high-risk transactions
- Risk-level distribution chart
- Daily transaction-value trend
- Daily transaction-count trend
- Transaction type distribution
- Channel distribution
- Country transaction-value comparison
- Top 10 customers by transaction value
- Top 10 customers by risk score
- Interactive transaction table with filters
- Interactive alert table
- CSV export
- Transaction relationship/network metrics

## Technology

Python, Streamlit, Pandas, Plotly, SQLite, Scikit-learn, NetworkX, FastAPI.

## Windows setup

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python run.py seed
streamlit run streamlit_app.py
```

If PowerShell activation is blocked, use:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py seed
.venv\Scripts\python.exe run.py dashboard
```

## API

```powershell
python run.py api
```

Swagger UI is available at `http://127.0.0.1:8000/docs`.

## Tests

```powershell
python run.py test
```

## Important

The project uses synthetic demo data and is intended for learning and portfolio demonstration. It is not a production AML compliance system. Production deployments require validated typologies, regulatory requirements, sanctions/PEP screening, model governance, security, audit controls, data retention and compliance review.
