"""
A* pathfinding controller with Addis Ababa constraints and visualization support.
Integrates the improved A* algorithm with domain-specific components.
"""

from typing import Optional, Dict, Any, List

from core.addis_ababa_adapter import AddisAbabaAdapter
from algorithms.astar_improved import AStarAlgorithm
from shared.constraints.node_limit_constraint import NodeLimitConstraint
from shared.constraints.distance_constraint import DistanceConstraint
from shared.constraints.time_constraint import TimeConstraint


class AStarController:
    """Controller for A* pathfinding with Addis Ababa constraints."""
    
    def __init__(self, domain_adapter: AddisAbabaAdapter):
        """
        Initialize A* controller with domain adapter.
        
        Args:
            domain_adapter: Addis Ababa adapter for graph and locations
        """
        self.domain_adapter = domain_adapter
        self.astar_algorithm = AStarAlgorithm(
            self.domain_adapter.message_handler, 
            max_paths=5
        )
    
    def find_optimal_paths(self, start_location: str, goal_location: str, 
                          algorithm: str = "astar", max_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Find optimal paths using A* algorithm.
        
        Args:
            start_location: Start location name
            goal_location: Goal location name
            algorithm: Algorithm name (for compatibility)
            max_time: Maximum travel time (seconds)
            
        Returns:
            Dictionary with path results and metadata
        """
        try:
            # Convert locations to nodes
            start_node = self.domain_adapter.get_nearest_node(start_location)
            goal_node = self.domain_adapter.get_nearest_node(goal_location)
        except Exception as e:
            return {
                "success": False,
                "message": f"Could not find location: {e}",
                "paths": []
            }
        
        # Create constraints if max_time is provided
        constraints = []
        if max_time is not None:
            # Default urban speed: ~8.3 m/s (30 km/h)
            average_speed_m_per_s = 8.3
            constraints.append(TimeConstraint(max_time, self.domain_adapter.path_calculator, average_speed_m_per_s))
        
        # Find paths using A*
        paths = self.astar_algorithm.find_path(
            start_node, goal_node, 
            self.domain_adapter.graph_adapter, 
            constraints,
            max_paths=5
        )
        
        if not paths:
            return {
                "success": False,
                "message": "No paths found between the specified nodes",
                "paths": []
            }
        
        # Get visited nodes for visualization
        visited_nodes = self.astar_algorithm.get_visited_nodes()
        
        # Prepare results
        results = {
            "success": True,
            "paths": paths,
            "primary_path": paths[0],
            "start_location": start_location,
            "goal_location": goal_location,
            "start_node": start_node,
            "goal_node": goal_node,
            "all_found_paths": self.astar_algorithm.get_all_found_paths(),
            "visited_nodes": visited_nodes,
            "algorithm": "A*"
        }
        
        # Calculate path statistics
        results["statistics"] = self.domain_adapter.path_calculator.get_path_statistics(
            paths, self.domain_adapter.graph_adapter.graph
        )
        
        # Add human-readable node names
        results["path_names"] = []
        results["path_costs"] = []
        for path in results["paths"]:
            path_names = [self.domain_adapter.get_node_name(node) for node in path]
            results["path_names"].append(path_names)
            
            # Calculate path cost
            cost = self.domain_adapter.path_calculator.calculate_path_cost(
                path, self.domain_adapter.graph_adapter.graph
            )
            results["path_costs"].append(cost)
        
        return results
    
    def find_paths_with_constraints(self, start_location: str, goal_location: str,
                                  max_paths: int = 5,
                                  max_depth: Optional[int] = None,
                                  max_cost: Optional[float] = None,
                                  heuristic_weight: float = 1.0) -> Dict[str, Any]:
        """
        Find paths using A* with Addis Ababa-specific constraints.
        
        Args:
            start_location: Start location name
            goal_location: Goal location name
            max_paths: Maximum number of paths to find
            max_depth: Maximum exploration depth
            max_cost: Maximum path cost in meters
            heuristic_weight: Weight for heuristic function
            
        Returns:
            Dictionary with A* results and constraints
        """
        try:
            # Convert locations to nodes
            start_node = self.domain_adapter.get_nearest_node(start_location)
            goal_node = self.domain_adapter.get_nearest_node(goal_location)
        except Exception as e:
            return {
                "success": False,
                "message": f"Could not find location: {e}",
                "paths": []
            }
        
        # Create Addis Ababa-specific constraints
        constraints = self._create_addis_ababa_constraints(max_depth, max_cost)
        
        # Find paths using A*
        paths = self.astar_algorithm.find_path(
            start_node, goal_node, 
            self.domain_adapter.graph_adapter, 
            constraints,
            max_paths=max_paths
        )
        
        if not paths:
            return {
                "success": False,
                "message": "No paths found between the specified nodes",
                "paths": []
            }
        
        # Get visited nodes from A*
        visited_nodes = self.astar_algorithm.get_visited_nodes()
        
        # Prepare results with valid paths
        results = {
            "success": True,
            "paths": paths,
            "primary_path": paths[0],
            "start_location": start_location,
            "goal_location": goal_location,
            "start_node": start_node,
            "goal_node": goal_node,
            "all_found_paths": self.astar_algorithm.get_all_found_paths(),
            "visited_nodes": visited_nodes,
            "constraints_applied": self._get_constraint_descriptions(constraints),
            "heuristic_weight": heuristic_weight,
            "algorithm": "A*"
        }
        
        # Add human-readable node names
        results["path_names"] = []
        results["path_costs"] = []
        for path in results["paths"]:
            path_names = [self.domain_adapter.get_node_name(node) for node in path]
            results["path_names"].append(path_names)
            
            # Calculate path cost
            cost = self.domain_adapter.path_calculator.calculate_path_cost(
                path, self.domain_adapter.graph_adapter.graph
            )
            results["path_costs"].append(cost)
        
        return results
    
    def _create_addis_ababa_constraints(self, max_depth: Optional[int], 
                                       max_cost: Optional[float]) -> List:
        """
        Create Addis Ababa-specific constraints for A*.
        
        Args:
            max_depth: Maximum exploration depth
            max_cost: Maximum path cost in meters
            
        Returns:
            List of constraints
        """
        constraints = []
        
        # Distance constraint (Addis Ababa city is roughly 20km across)
        if max_cost is None:
            max_cost = 20000  # 20km default for Addis Ababa
        constraints.append(DistanceConstraint(max_cost, self.domain_adapter.path_calculator))
        
        # Node limit constraint (prevent infinite loops)
        if max_depth is None:
            max_depth = 1000  # Reasonable limit for city navigation
        constraints.append(NodeLimitConstraint(max_depth))
        
        return constraints
    
    def _get_constraint_descriptions(self, constraints: List) -> List[str]:
        """
        Get human-readable descriptions of applied constraints.
        
        Args:
            constraints: List of constraints
            
        Returns:
            List of constraint descriptions
        """
        descriptions = []
        for constraint in constraints:
            if isinstance(constraint, DistanceConstraint):
                descriptions.append(f"Maximum distance: {constraint.max_distance:.0f}m")
            elif isinstance(constraint, NodeLimitConstraint):
                descriptions.append(f"Maximum nodes: {constraint.max_nodes}")
        
        return descriptions
