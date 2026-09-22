import networkx as nx
from app.database import query_df

def build_transaction_graph():
    df = query_df("SELECT customer_id, counterparty_id, amount FROM transactions")
    graph = nx.DiGraph()

    for _, row in df.iterrows():
        source = row["customer_id"]
        target = row["counterparty_id"]
        amount = float(row["amount"])
        if graph.has_edge(source, target):
            graph[source][target]["weight"] += amount
            graph[source][target]["count"] += 1
        else:
            graph.add_edge(source, target, weight=amount, count=1)
    return graph

def network_metrics():
    graph = build_transaction_graph()
    if graph.number_of_nodes() == 0:
        return {"nodes": 0, "edges": 0, "largest_degree": 0}
    degrees = dict(graph.degree())
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "largest_degree": max(degrees.values()) if degrees else 0
    }
