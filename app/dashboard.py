import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone

from app.database import init_db, query_df, execute
from app.seed import seed_database
from app.detection import monitor_transactions
from app.ml import run_anomaly_detection
from app.network import network_metrics

st.set_page_config(
    page_title="AI-AML Guard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()

# Consistent dashboard palette
COLORS = {
    "blue": "#2563EB", "cyan": "#06B6D4", "green": "#10B981",
    "yellow": "#F59E0B", "orange": "#F97316", "red": "#EF4444",
    "purple": "#8B5CF6", "pink": "#EC4899", "navy": "#0B1F3A"
}
RISK_COLORS = {"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#EF4444"}

st.markdown("""
<style>
.hero {background:linear-gradient(135deg,#0B1F3A,#2563EB,#06B6D4);padding:24px 30px;border-radius:16px;color:white;margin-bottom:18px;}
.hero h1{color:white;margin:0;}
.hero p{color:#E0F2FE;margin:6px 0 0;}
[data-testid=stMetric]{background:#ffffff;border:1px solid #E2E8F0;border-radius:12px;padding:10px;}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🛡️ AI-AML Guard</h1><p>Intelligent Anti-Money Laundering & Transaction Monitoring Analytics</p></div>', unsafe_allow_html=True)


# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("Generate / Reset Demo Data", use_container_width=True):
        seed_database()
        st.success("Demo data generated.")
        st.rerun()

    if st.button("Run Rule Monitoring", use_container_width=True):
        count = monitor_transactions()
        st.success(f"{count:,} alerts generated.")
        st.rerun()

    if st.button("Run ML Anomaly Detection", use_container_width=True):
        count = run_anomaly_detection()
        st.success(f"{count:,} transactions scored.")
        st.rerun()

    st.divider()
    st.caption("All data is synthetic demo data.")

tx = query_df("SELECT * FROM transactions")
alerts = query_df("SELECT * FROM alerts")
customers = query_df("SELECT * FROM customers")
cases = query_df("SELECT * FROM cases")

if tx.empty:
    st.warning("No transaction data found.")
    st.info("Click **Generate / Reset Demo Data** in the sidebar.")
    st.stop()

tx["timestamp_dt"] = pd.to_datetime(tx["timestamp"], utc=True)
tx["date"] = tx["timestamp_dt"].dt.date
tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0)
tx["risk_score"] = pd.to_numeric(tx["risk_score"], errors="coerce").fillna(0)
tx["anomaly_score"] = pd.to_numeric(tx["anomaly_score"], errors="coerce").fillna(0)

# ---------- Global filters ----------
st.subheader("🔎 Dashboard Filters")
f1, f2, f3, f4 = st.columns(4)

with f1:
    risk_filter = st.multiselect(
        "Risk level",
        ["LOW", "MEDIUM", "HIGH"],
        default=["LOW", "MEDIUM", "HIGH"]
    )
with f2:
    type_filter = st.multiselect(
        "Transaction type",
        sorted(tx["transaction_type"].unique()),
        default=sorted(tx["transaction_type"].unique())
    )
with f3:
    channel_filter = st.multiselect(
        "Channel",
        sorted(tx["channel"].unique()),
        default=sorted(tx["channel"].unique())
    )
with f4:
    country_filter = st.multiselect(
        "Country",
        sorted(tx["country"].unique()),
        default=sorted(tx["country"].unique())
    )

filtered = tx[
    tx["risk_level"].isin(risk_filter)
    & tx["transaction_type"].isin(type_filter)
    & tx["channel"].isin(channel_filter)
    & tx["country"].isin(country_filter)
].copy()

# ---------- KPI cards ----------
total_value = filtered["amount"].sum()
high_risk = int((filtered["risk_level"] == "HIGH").sum())
medium_risk = int((filtered["risk_level"] == "MEDIUM").sum())
filtered_alerts = alerts[alerts["transaction_id"].isin(filtered["transaction_id"])] if not alerts.empty else alerts

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Transactions", f"{len(filtered):,}")
k2.metric("Transaction Value", f"₹{total_value:,.0f}")
k3.metric("Alerts", f"{len(filtered_alerts):,}")
k4.metric("High Risk", f"{high_risk:,}")
k5.metric("Medium Risk", f"{medium_risk:,}")

st.divider()

# ---------- Charts ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "💳 Transactions", "🚨 Alerts", "📁 Cases", "🕸️ Network"]
)

with tab1:
    c1, c2 = st.columns(2)

    with c1:
        risk = (
            filtered["risk_level"]
            .value_counts()
            .reindex(["LOW", "MEDIUM", "HIGH"], fill_value=0)
            .rename_axis("Risk Level")
            .reset_index(name="Count")
        )
        fig = px.pie(
            risk,
            names="Risk Level",
            values="Count",
            hole=0.45,
            title="Risk-Level Distribution",
            color="Risk Level",
            color_discrete_map=RISK_COLORS
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        daily = (
            filtered.groupby("date", as_index=False)["amount"]
            .sum()
            .rename(columns={"amount": "Transaction Value"})
        )
        fig = px.line(
            daily,
            x="date",
            y="Transaction Value",
            markers=True,
            title="Daily Transaction Value",
            color_discrete_sequence=[COLORS["blue"]]
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Amount (INR)")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        daily_count = (
            filtered.groupby("date")
            .size()
            .reset_index(name="Transactions")
        )
        fig = px.line(
            daily_count,
            x="date",
            y="Transactions",
            markers=True,
            title="Daily Transaction Count",
            color_discrete_sequence=[COLORS["purple"]]
        )
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        type_summary = (
            filtered.groupby("transaction_type", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        fig = px.bar(
            type_summary,
            x="transaction_type",
            y="amount",
            title="Transaction Value by Type",
            color="transaction_type",
            color_discrete_sequence=[COLORS["blue"], COLORS["cyan"], COLORS["purple"], COLORS["orange"], COLORS["pink"]]
        )
        fig.update_layout(xaxis_title="Transaction Type", yaxis_title="Amount (INR)")
        st.plotly_chart(fig, use_container_width=True)

    c5, c6 = st.columns(2)

    with c5:
        channel_summary = (
            filtered["channel"]
            .value_counts()
            .rename_axis("Channel")
            .reset_index(name="Transactions")
        )
        fig = px.bar(
            channel_summary,
            x="Channel",
            y="Transactions",
            title="Transactions by Channel",
            color="Channel",
            color_discrete_sequence=[COLORS["green"], COLORS["blue"], COLORS["orange"], COLORS["purple"]]
        )
        st.plotly_chart(fig, use_container_width=True)

    with c6:
        country_summary = (
            filtered.groupby("country", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        fig = px.bar(
            country_summary,
            x="country",
            y="amount",
            title="Transaction Value by Country",
            color="amount",
            color_continuous_scale=["#DBEAFE", "#60A5FA", "#2563EB", "#1E3A8A"]
        )
        fig.update_layout(xaxis_title="Country", yaxis_title="Amount (INR)")
        st.plotly_chart(fig, use_container_width=True)

    c7, c8 = st.columns(2)

    with c7:
        customer_value = (
            filtered.groupby("customer_id", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
            .head(10)
        )
        fig = px.bar(
            customer_value,
            x="amount",
            y="customer_id",
            orientation="h",
            title="Top 10 Customers by Transaction Value",
            color="amount",
            color_continuous_scale=["#DBEAFE", "#2563EB", "#1E3A8A"]
        )
        fig.update_layout(xaxis_title="Amount (INR)", yaxis_title="Customer")
        st.plotly_chart(fig, use_container_width=True)

    with c8:
        customer_risk = (
            filtered.groupby("customer_id", as_index=False)["risk_score"]
            .mean()
            .sort_values("risk_score", ascending=False)
            .head(10)
        )
        fig = px.bar(
            customer_risk,
            x="risk_score",
            y="customer_id",
            orientation="h",
            title="Top 10 Customers by Average Risk Score",
            color="risk_score",
            color_continuous_scale=["#FEF3C7", "#F97316", "#DC2626"]
        )
        fig.update_layout(xaxis_title="Risk Score", yaxis_title="Customer")
        st.plotly_chart(fig, use_container_width=True)

    c9, c10 = st.columns(2)

    with c9:
        fig = px.histogram(
            filtered, x="risk_score", nbins=20,
            title="Risk Score Distribution",
            color_discrete_sequence=[COLORS["orange"]]
        )
        fig.update_layout(xaxis_title="Risk Score", yaxis_title="Transactions")
        st.plotly_chart(fig, use_container_width=True)

    with c10:
        fig = px.histogram(
            filtered, x="anomaly_score", nbins=20,
            title="ML Anomaly Score Distribution",
            color_discrete_sequence=[COLORS["pink"]]
        )
        fig.update_layout(xaxis_title="Anomaly Score", yaxis_title="Transactions")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Highest-Risk Transactions")
    display_cols = [
        "transaction_id", "timestamp", "customer_id", "amount",
        "transaction_type", "channel", "country",
        "anomaly_score", "risk_score", "risk_level"
    ]
    st.dataframe(
        filtered.sort_values("risk_score", ascending=False)[display_cols].head(25),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.subheader("💳 Transaction Data Table")
    search = st.text_input("Search customer ID, transaction ID or counterparty", key="tx_search")

    view = filtered.copy()
    if search:
        search = search.strip()
        mask = (
            view["customer_id"].astype(str).str.contains(search, case=False, na=False)
            | view["transaction_id"].astype(str).str.contains(search, case=False, na=False)
            | view["counterparty_id"].astype(str).str.contains(search, case=False, na=False)
        )
        view = view[mask]

    st.dataframe(
        view.sort_values("risk_score", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    st.download_button(
        "⬇️ Download Filtered Transactions CSV",
        view.drop(columns=["timestamp_dt"], errors="ignore").to_csv(index=False),
        "aml_transactions_filtered.csv",
        "text/csv"
    )

with tab3:
    st.subheader("🚨 Explainable AML Alerts")
    if filtered_alerts.empty:
        st.info("No alerts match the current filters.")
    else:
        alert_view = filtered_alerts.sort_values("risk_score", ascending=False)
        st.dataframe(alert_view, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download Alerts CSV",
            alert_view.to_csv(index=False),
            "aml_alerts.csv",
            "text/csv"
        )

with tab4:
    st.subheader("📁 Investigation Cases")

    if not filtered_alerts.empty:
        customer_options = sorted(filtered_alerts["customer_id"].unique())
        selected_customer = st.selectbox("Customer", customer_options)
        title = st.text_input(
            "Case title",
            f"AML investigation — {selected_customer}"
        )
        priority = st.selectbox(
            "Priority",
            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            index=2
        )
        notes = st.text_area("Investigator notes")

        if st.button("Create Investigation Case"):
            execute(
                """
                INSERT INTO cases(customer_id,title,priority,status,notes,created_at)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    selected_customer,
                    title,
                    priority,
                    "OPEN",
                    notes,
                    datetime.now(timezone.utc).isoformat()
                )
            )
            st.success("Investigation case created.")
            st.rerun()

    if cases.empty:
        st.info("No investigation cases created yet.")
    else:
        st.dataframe(
            cases.sort_values("case_id", ascending=False),
            use_container_width=True,
            hide_index=True
        )

with tab5:
    st.subheader("🕸️ Transaction Network Analytics")
    metrics = network_metrics()
    n1, n2, n3 = st.columns(3)
    n1.metric("Network Nodes", f"{metrics['nodes']:,}")
    n2.metric("Relationships", f"{metrics['edges']:,}")
    n3.metric("Largest Degree", f"{metrics['largest_degree']:,}")

    st.write(
        "Customers and counterparties are represented as nodes, while transactions "
        "represent directed relationships. The current release exposes network metrics "
        "for portfolio analysis; a future UI enhancement can render an interactive graph."
    )
