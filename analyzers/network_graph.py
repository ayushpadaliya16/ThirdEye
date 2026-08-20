import networkx as nx
import logging

logger = logging.getLogger(__name__)

def build_network_topology(seed_user: str, connections: list) -> dict:
    """
    Constructs a directed graph representing follower/following interactions 
    and calculates centrality metrics to detect coordinated clusters.
    """
    logger.info(f"Building network topology for seed: {seed_user}")
    
    G = nx.DiGraph()
    G.add_node(seed_user, type="seed")
    
    # connections should be a list of tuples: (source, target, type)
    # E.g., ('user1', 'seed_user', 'follows')
    for conn in connections:
        if len(conn) >= 2:
            src, tgt = conn[0], conn[1]
            G.add_edge(src, tgt)
            
    # Calculate metrics
    degree_cent = nx.degree_centrality(G)
    
    # Clustering coefficient requires an undirected graph or specifically defined directed metric
    # We use the generic average clustering on an undirected representation for simplicity
    try:
        clustering_coeff = nx.average_clustering(G.to_undirected())
    except Exception:
        clustering_coeff = 0.0
        
    # Format for JSON serialization (D3.js / Recharts friendly)
    nodes = [{"id": node, "degree_centrality": degree_cent.get(node, 0)} for node in G.nodes()]
    edges = [{"source": u, "target": v} for u, v in G.edges()]
    
    return {
        "metrics": {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "average_clustering_coefficient": round(clustering_coeff, 4)
        },
        "graph_data": {
            "nodes": nodes,
            "links": edges
        }
    }
