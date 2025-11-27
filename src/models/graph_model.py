"""
Graph model for managing the road network data.
Single responsibility: Graph data management and basic operations.
"""

import osmnx as ox
import networkx as nx
from pathlib import Path
from typing import Optional, Dict, Any

from ..config.settings import (
    CACHE_DIR, GRAPH_CACHE_FILE, DEFAULT_CITY, 
    NETWORK_TYPE, SIMPLIFY_GRAPH
)


class GraphModel:
    """Manages the road network graph data and basic operations."""
    
    def __init__(self):
        """Initialize the graph model with cached or fresh data."""
        self._graph: Optional[nx.Graph] = None
        self._load_graph()
    
    def _load_graph(self) -> None:
        """Load graph from cache or download fresh data."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        if GRAPH_CACHE_FILE.exists():
            print("Loading Addis Ababa map from cache...")
            self._graph = ox.load_graphml(GRAPH_CACHE_FILE)
        else:
            print("Downloading Addis Ababa map (this may take a few minutes)...")
            self._graph = ox.graph_from_place(
                DEFAULT_CITY,
                network_type=NETWORK_TYPE,
                simplify=SIMPLIFY_GRAPH
            )
            ox.save_graphml(self._graph, GRAPH_CACHE_FILE)
            print("Map data saved to cache")
        
        # Convert to undirected for comprehensive path finding
        self._graph = self._graph.to_undirected()
    
    @property
    def graph(self) -> nx.Graph:
        """Get the road network graph."""
        return self._graph
    
    def get_node_data(self, node_id: int) -> Dict[str, Any]:
        """Get data for a specific node."""
        return self._graph.nodes[node_id]
    
    def get_edge_data(self, u: int, v: int) -> Optional[Dict[str, Any]]:
        """Get edge data between two nodes."""
        try:
            return self._graph.get_edge_data(u, v)
        except:
            return None
    
    def get_neighbors(self, node_id: int) -> list:
        """Get neighbors of a node."""
        return list(self._graph.neighbors(node_id))
    
    def node_exists(self, node_id: int) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self._graph.nodes
    
    def edge_exists(self, u: int, v: int) -> bool:
        """Check if an edge exists between two nodes."""
        return self._graph.has_edge(u, v)
    
    def get_subgraph(self, nodes: list) -> nx.Graph:
        """Get a subgraph containing only the specified nodes."""
        return self._graph.subgraph(nodes)
