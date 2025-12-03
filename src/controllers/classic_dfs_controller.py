"""
Classic DFS pathfinding controller.
Uses the user's classic DFS algorithm with Addis Ababa constraints.
"""

from typing import List, Dict, Any, Optional

from core.addis_ababa_adapter import AddisAbabaAdapter
from services.generic_pathfinding_service import GenericPathfindingService
from services.visualization_service import VisualizationService
from algorithms.dfs_classic import ClassicDFSAlgorithm
from shared.calculators.generic_path_calculator import GenericPathCalculator
from shared.constraints.node_limit_constraint import NodeLimitConstraint
from shared.constraints.distance_constraint import DistanceConstraint
from shared.constraints.time_constraint import TimeConstraint


class ClassicDFSController:
    """Controller using Classic DFS algorithm with Addis Ababa constraints."""
    
    def __init__(self, domain_adapter=None):
        """
        Initialize Classic DFS controller with domain adapter.
        
        Args:
            domain_adapter: Domain-specific adapter (defaults to Addis Ababa)
        """
        self.domain_adapter = domain_adapter or AddisAbabaAdapter()
        self.visualization_service = None
        
        # Classic DFS algorithm (based on user's implementation)
        self.classic_dfs = ClassicDFSAlgorithm(
            self.domain_adapter.message_handler, 
            max_paths=5
        )
    
    def find_paths_with_constraints(self, start_location: str, goal_location: str,
                                   max_paths: int = 5,
                                   max_depth: Optional[int] = None,
                                   max_cost: Optional[float] = None,
                                   max_time: Optional[float] = None,
                                   diversity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Find paths using Classic DFS with Addis Ababa constraints.
        
        Args:
            start_location: Start location name
            goal_location: Goal location name
            max_paths: Maximum number of paths to find
            max_depth: Maximum exploration depth
            max_cost: Maximum path cost in meters
            max_time: Maximum travel time (seconds)
            diversity_threshold: Minimum diversity between paths
            
        Returns:
            Dictionary with Classic DFS results and constraints
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
        
        # First, try without constraints to get basic paths
        basic_paths = self.classic_dfs.find_path(start_node, goal_node, self.domain_adapter.graph_adapter, [], max_paths)
        
        if not basic_paths:
            return {
                "success": False,
                "message": "No paths found between the specified nodes",
                "paths": []
            }
        
        # Get visited nodes from Classic DFS
        visited_nodes = self.classic_dfs.get_visited_nodes()
        
        # Create Addis Ababa-specific constraints (more lenient)
        constraints = self._create_addis_ababa_constraints(
            max_depth, max_cost, max_time, diversity_threshold
        )
        
        # Filter basic paths through constraints
        valid_paths = []
        for path in basic_paths:
            is_valid = True
            constraint_messages = []
            
            for constraint in constraints:
                valid, message = constraint.validate(path, self.domain_adapter.graph_adapter.graph)
                if not valid:
                    is_valid = False
                    constraint_messages.append(message)
                    break
            
            if is_valid:
                valid_paths.append(path)
        
        if not valid_paths:
            # If no paths pass constraints, return basic paths with warning
            return {
                "success": True,
                "paths": basic_paths,
                "primary_path": basic_paths[0],
                "start_location": start_location,
                "goal_location": goal_location,
                "start_node": start_node,
                "goal_node": goal_node,
                "all_found_paths": self.classic_dfs.get_all_found_paths(),
                "visited_nodes": visited_nodes,  # Add visited nodes here
                "constraints_applied": ["No constraints applied (too restrictive)"],
                "constraint_warning": "Original constraints were too restrictive, showing unconstrained paths"
            }
        
        # Prepare results with valid paths
        results = {
            "success": True,
            "paths": valid_paths,
            "primary_path": valid_paths[0],
            "start_location": start_location,
            "goal_location": goal_location,
            "start_node": start_node,
            "goal_node": goal_node,
            "all_found_paths": self.classic_dfs.get_all_found_paths(),
            "visited_nodes": visited_nodes,  # Add visited nodes here
            "constraints_applied": self._get_constraint_descriptions(constraints)
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
                                        max_cost: Optional[float],
                                        max_time: Optional[float],
                                        diversity_threshold: float) -> List:
        """
        Create Addis Ababa-specific constraints for Classic DFS.
        
        Args:
            max_depth: Maximum exploration depth
            max_cost: Maximum path cost in meters
            max_time: Maximum travel time (seconds)
            diversity_threshold: Minimum diversity between paths
            
        Returns:
            List of constraints
        """
        constraints = []
        
        # Addis Ababa depth constraint (prevent too long routes in the city)
        if max_depth:
            constraints.append(NodeLimitConstraint(max_depth))
        else:
            # Default depth limit for Addis Ababa (reasonable city travel)
            constraints.append(NodeLimitConstraint(25))
        
        # Addis Ababa cost constraint (prevent too expensive routes)
        if max_cost:
            constraints.append(DistanceConstraint(max_cost, path_calculator=self.domain_adapter.path_calculator))
        else:
            # Default cost limit for Addis Ababa (reasonable travel distance)
            constraints.append(DistanceConstraint(10000, path_calculator=self.domain_adapter.path_calculator))
        
        # Addis Ababa time constraint (prevent too long travel time)
        if max_time:
            # Default urban speed: ~8.3 m/s (30 km/h)
            average_speed_m_per_s = 8.3
            constraints.append(TimeConstraint(max_time, self.domain_adapter.path_calculator, average_speed_m_per_s))
        
        return constraints
    
    def _get_constraint_descriptions(self, constraints: List) -> List[str]:
        """Get human-readable descriptions of applied constraints."""
        descriptions = []
        for constraint in constraints:
            if isinstance(constraint, NodeLimitConstraint):
                descriptions.append(f"Max depth: {constraint.max_nodes} nodes")
            elif isinstance(constraint, DistanceConstraint):
                descriptions.append(f"Max cost: {constraint.max_distance:.0f} meters")
            elif isinstance(constraint, TimeConstraint):
                max_min = constraint.max_time_seconds / 60.0
                descriptions.append(f"Max time: {max_min:.1f} minutes")
        return descriptions
    
    def visualize_classic_dfs(self, path_results: Dict[str, Any], 
                            save_path: str = "classic_dfs_paths.png",
                            show_plot: bool = True) -> None:
        """
        Visualize Classic DFS paths with Addis Ababa constraints.
        
        Args:
            path_results: Results from find_paths_with_constraints
            save_path: Path to save visualization
            show_plot: Whether to display the plot
        """
        if not path_results["success"]:
            return
        
        # Create visualization service if needed
        if not self.visualization_service:
            self.visualization_service = VisualizationService(
                self.domain_adapter.graph_model,
                self.domain_adapter.location_model
            )
        
        # Convert node paths to the format expected by visualization service
        primary_path = path_results["primary_path"]
        alternative_paths = path_results["paths"][1:] if len(path_results["paths"]) > 1 else None
        visited_nodes = path_results.get("visited_nodes", set())
        
        # Create visualization
        self.visualization_service.create_path_visualization(
            primary_path=primary_path,
            visited_nodes=visited_nodes,
            alternative_paths=alternative_paths,
            save_path=save_path,
            show_plot=show_plot
        )
    
    def display_constraint_results(self, path_results: Dict[str, Any]) -> None:
        """
        Display Classic DFS results in a clean, concise way.
        
        Args:
            path_results: Results from find_paths_with_constraints
        """
        if not path_results["success"]:
            print(f"No paths found: {path_results.get('message', 'Unknown error')}")
            return
        
        print("=" * 60)
        print("CLASSIC DFS SEARCH RESULTS")
        print("=" * 60)
        
        # Basic Info
        print(f"Route: {path_results['start_location']} -> {path_results['goal_location']}")
        print(f"Nodes Explored: {len(path_results.get('visited_nodes', set())):,}")
        print(f"Paths Found: {len(path_results['paths'])}")
        
        # Path Analysis
        paths = path_results["paths"]
        path_names = path_results.get('path_names', [])
        path_costs = path_results.get('path_costs', [])
        
        # Generate path data if not present
        if not path_names:
            path_names = []
            for path in paths:
                names = [self.domain_adapter.get_node_name(node) for node in path]
                path_names.append(names)
        
        if not path_costs:
            path_costs = []
            for path in paths:
                cost = self.domain_adapter.path_calculator.calculate_path_cost(
                    path, self.domain_adapter.graph_adapter.graph
                )
                path_costs.append(cost)
        
        # Find best path
        if path_costs:
            shortest_idx = min(range(len(path_costs)), key=lambda i: path_costs[i])
            shortest_cost = path_costs[shortest_idx]
            print(f"Shortest Distance: {shortest_cost:.0f} meters (Path {shortest_idx + 1})")
        
        # Show paths
        print(f"\nPATH DETAILS:")
        print("-" * 40)
        
        for i, (path, names, cost) in enumerate(zip(paths, path_names, path_costs)):
            if i == 0:
                print(f"PRIMARY: {cost:.0f}m, {len(path)-1} steps")
            else:
                cost_diff = cost - path_costs[0]
                cost_percent = (cost_diff / path_costs[0]) * 100
                print(f"ALT {i}: {cost:.0f}m ({cost_percent:+.0f}%), {len(path)-1} steps")
            
            # Show start and end points only
            print(f"   {names[0]} -> {names[-1]}")
        
        # Recommendations
        print(f"\nRECOMMENDATION:")
        if path_costs:
            print(f"   Best: Path {shortest_idx + 1} ({shortest_cost:.0f}m)")
        
        print("=" * 60)
        print("Search complete - Check visualization for map!")
        print("=" * 60)
    
    def test_classic_dfs_constraints(self, start_location: str, goal_location: str) -> Dict[str, Any]:
        """
        Test Classic DFS with different constraint combinations.
        
        Args:
            start_location: Start location
            goal_location: Goal location
            
        Returns:
            Test results
        """
        print(f"\\n=== TESTING CLASSIC DFS WITH CONSTRAINTS ===")
        print(f"Testing from {start_location} to {goal_location}")
        
        # Test with different constraint combinations
        test_cases = [
            {"max_depth": 15, "max_cost": 5000, "diversity": 0.8, "name": "Strict"},
            {"max_depth": 25, "max_cost": 10000, "diversity": 0.6, "name": "Balanced"},
            {"max_depth": 35, "max_cost": 15000, "diversity": 0.4, "name": "Relaxed"},
        ]
        
        results = {}
        
        for test_case in test_cases:
            print(f"\\nTesting {test_case['name']} constraints:")
            
            result = self.find_paths_with_constraints(
                start_location=start_location,
                goal_location=goal_location,
                max_paths=3,
                max_depth=test_case['max_depth'],
                max_cost=test_case['max_cost'],
                diversity_threshold=test_case['diversity']
            )
            
            results[test_case['name']] = result
            
            if result["success"]:
                stats = result["statistics"]
                print(f"  ✓ Found {len(result['paths'])} paths")
                print(f"    Average cost: {stats['avg_cost']:.0f}m")
                print(f"    Average steps: {stats['avg_steps']:.0f}")
            else:
                print(f"  ✗ Failed: {result.get('message', 'Unknown error')}")
        
        return results
    
    def run_classic_dfs_with_constraints(self, start_location: str, goal_location: str,
                                        max_depth: Optional[int] = None,
                                        max_cost: Optional[float] = None,
                                        diversity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Run Classic DFS with Addis Ababa constraints.
        
        Args:
            start_location: Start location
            goal_location: Goal location
            max_depth: Maximum exploration depth
            max_cost: Maximum path cost
            diversity_threshold: Path diversity threshold
            
        Returns:
            Results with constraints applied
        """
        print(f"\\n=== CLASSIC DFS WITH ADDIS ABABA CONSTRAINTS ===")
        print(f"Finding paths from {start_location} to {goal_location}")
        print(f"Using stack-based DFS with Addis Ababa constraints")
        
        result = self.find_paths_with_constraints(
            start_location=start_location,
            goal_location=goal_location,
            max_paths=5,
            max_depth=max_depth,
            max_cost=max_cost,
            diversity_threshold=diversity_threshold
        )
        
        if result["success"]:
            # Display results with constraints
            self.display_constraint_results(result)
            
            # Create visualization
            print(f"\\nGenerating Classic DFS visualization...")
            self.visualize_classic_dfs(result, save_path="classic_dfs_constraints.png")
            print("Visualization saved as 'classic_dfs_constraints.png'")
            
            if len(result["paths"]) > 1:
                print(f"\\nVisualization shows {len(result['paths'])} paths:")
                print("Red = Primary path")
                print("Yellow, Lime, Cyan = Alternative paths")
                print(f"Light blue area = Nodes explored by Classic DFS ({len(result.get('visited_nodes', set()))} nodes)")
            else:
                print(f"\\nVisualization shows:")
                print("Red = Primary path")
                print(f"Light blue area = Nodes explored by Classic DFS ({len(result.get('visited_nodes', set()))} nodes)")
        
        return result
    
    def list_available_locations(self) -> List[str]:
        """Get list of available locations from the domain adapter."""
        return self.domain_adapter.list_available_locations()
