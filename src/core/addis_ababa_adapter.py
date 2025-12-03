"""
Addis Ababa specific adapter.
Implements domain-specific functionality using generic components.
"""

import osmnx as ox
from typing import List, Dict, Any, Optional, Tuple, Union

from core.graph_interface import MessageHandlerInterface
from core.networkx_graph_adapter import NetworkXGraphAdapter
from core.graph_model import GraphModel
from core.location_model import LocationModel
from shared.constraints.node_limit_constraint import NodeLimitConstraint
from shared.constraints.distance_constraint import DistanceConstraint
from shared.constraints.same_location_constraint import SameLocationConstraint
from shared.constraints.time_constraint import TimeConstraint
from config.settings import AVERAGE_SPEED_KMH
from shared.calculators.generic_path_calculator import GenericPathCalculator
from algorithms.bfs import BFSAlgorithm
from algorithms.dfs_classic import ClassicDFSAlgorithm as DFSAlgorithm
from algorithms.astar_improved import AStarAlgorithm
from services.generic_pathfinding_service import GenericPathfindingService


class AddisAbabaMessageHandler(MessageHandlerInterface):
    """Message handler for Addis Ababa domain."""
    
    def handle_error(self, message: str) -> None:
        print(f"Error: {message}")
    
    def handle_info(self, message: str) -> None:
        print(f"Info: {message}")
    
    def handle_success(self, message: str) -> None:
        print(f"✓ {message}")


class AddisAbabaAdapter:
    """Adapter for Addis Ababa specific functionality using generic components."""
    
    def __init__(self):
        """Initialize Addis Ababa adapter with generic components."""
        # Domain-specific models
        self.graph_model = GraphModel()
        self.location_model = LocationModel(self.graph_model.graph)
        
        # Generic adapters
        self.graph_adapter = NetworkXGraphAdapter(self.graph_model.graph)
        self.path_calculator = GenericPathCalculator()
        self.message_handler = AddisAbabaMessageHandler()
        
        # Initialize algorithms
        self.bfs_algorithm = BFSAlgorithm(self.message_handler)
        self.dfs_algorithm = DFSAlgorithm(self.message_handler)
        self.astar_algorithm = AStarAlgorithm(self._euclidean_heuristic, self.message_handler)
    
    def create_pathfinding_service(self, algorithm_name: str = "bfs") -> GenericPathfindingService:
        """
        Create a pathfinding service with the specified algorithm.
        
        Args:
            algorithm_name: Algorithm to use ("bfs", "dfs", "astar")
            
        Returns:
            Configured pathfinding service
        """
        algorithms = {
            "bfs": self.bfs_algorithm,
            "dfs": self.dfs_algorithm,
            "astar": self.astar_algorithm
        }
        
        algorithm = algorithms.get(algorithm_name.lower(), self.bfs_algorithm)
        
        return GenericPathfindingService(
            graph=self.graph_adapter,
            algorithm=algorithm,
            path_calculator=self.path_calculator,
            message_handler=self.message_handler
        )
    
    def get_nearest_node(self, location: Union[str, Tuple[float, float]]) -> int:
        """Get nearest node to a location."""
        return self.location_model.get_nearest_node(location)
    
    def get_node_name(self, node_id: int) -> str:
        """Get human-readable name for a node."""
        return self.location_model.get_node_name(node_id)
    
    def create_addis_constraints(
        self,
        max_nodes: Optional[int] = None,
        max_distance: Optional[float] = None,
        max_time: Optional[float] = None,
    ) -> List:
        """
        Create Addis Ababa specific constraints.
        
        Args:
            max_nodes: Maximum nodes to process
            max_distance: Maximum path distance in meters
            
        Returns:
            List of constraints
        """
        constraints = [SameLocationConstraint()]
        
        if max_nodes:
            constraints.append(NodeLimitConstraint(max_nodes))
        
        if max_distance:
            constraints.append(DistanceConstraint(max_distance, self.path_calculator))

        if max_time:
            # Convert average speed from km/h to m/s
            speed_m_per_s = (AVERAGE_SPEED_KMH * 1000.0) / 3600.0
            constraints.append(TimeConstraint(max_time, self.path_calculator, speed_m_per_s))
        
        return constraints
    
    def _euclidean_heuristic(self, node: int, goal: int, graph) -> float:
        """Euclidean distance heuristic for A*."""
        node_data = graph.get_node_data(node)
        goal_data = graph.get_node_data(goal)
        
        lat1, lon1 = node_data['y'], node_data['x']
        lat2, lon2 = goal_data['y'], goal_data['x']
        
        # Simple Euclidean distance approximation
        return ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 111000  # Convert to meters
    
    def list_available_locations(self) -> List[str]:
        """Get list of available Addis Ababa locations."""
        return self.location_model.list_available_locations()
    
    def location_exists(self, location_name: str) -> bool:
        """Check if a location exists in Addis Ababa."""
        return self.location_model.location_exists(location_name)
