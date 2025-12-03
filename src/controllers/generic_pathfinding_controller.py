"""
Generic pathfinding controller.
Works with any domain through adapters and generic components.
"""

from typing import List, Dict, Any, Optional

from core.addis_ababa_adapter import AddisAbabaAdapter
from services.generic_pathfinding_service import GenericPathfindingService
from services.visualization_service import VisualizationService


class GenericPathfindingController:
    """Controller that can work with any domain through adapters."""
    
    def __init__(self, domain_adapter=None):
        """
        Initialize with a domain adapter.
        
        Args:
            domain_adapter: Domain-specific adapter (defaults to Addis Ababa)
        """
        self.domain_adapter = domain_adapter or AddisAbabaAdapter()
        self.visualization_service = None  # Will be created when needed
    
    def find_optimal_paths(
        self,
        start_location: str,
        goal_location: str,
        algorithm: str = "bfs",
        max_paths: int = 5,
        max_nodes: Optional[int] = None,
        max_distance: Optional[float] = None,
        max_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Find optimal paths between two locations.
        
        Args:
            start_location: Start location name
            goal_location: Goal location name
            algorithm: Algorithm to use ("bfs", "dfs", "astar")
            max_paths: Maximum number of paths to find
            max_nodes: Maximum nodes to process
            max_distance: Maximum path distance (meters)
            max_time: Maximum travel time (seconds)
            
        Returns:
            Dictionary with path results
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
        
        # Create pathfinding service with specified algorithm
        pathfinding_service = self.domain_adapter.create_pathfinding_service(algorithm)
        
        # Create domain-specific constraints
        constraints = self.domain_adapter.create_addis_constraints(
            max_nodes=max_nodes,
            max_distance=max_distance,
            max_time=max_time,
        )
        
        # Find paths
        results = pathfinding_service.find_paths(start_node, goal_node, constraints, max_paths)
        
        # Add domain-specific information
        if results["success"]:
            results["start_location"] = start_location
            results["goal_location"] = goal_location
            results["start_node"] = start_node
            results["goal_node"] = goal_node
            
            # Add human-readable node names
            results["path_names"] = []
            for path in results["paths"]:
                path_names = [self.domain_adapter.get_node_name(node) for node in path]
                results["path_names"].append(path_names)
        
        return results
    
    def visualize_paths(self, path_results: Dict[str, Any], 
                       save_path: str = "path_visualization.png", 
                       show_plot: bool = True) -> None:
        """
        Visualize paths using the domain-specific visualization service.
        
        Args:
            path_results: Results from find_optimal_paths
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
        
        # Create visualization (domain-specific)
        self.visualization_service.create_path_visualization(
            primary_path=primary_path,
            visited_nodes=visited_nodes,
            alternative_paths=alternative_paths,
            save_path=save_path,
            show_plot=show_plot
        )
    
    def get_path_details(self, path_results: Dict[str, Any]) -> List[str]:
        """
        Get formatted path details for display (clean and concise).
        
        Args:
            path_results: Results from find_optimal_paths
            
        Returns:
            List of formatted path detail strings
        """
        if not path_results["success"]:
            return [path_results.get("message", "No path found")]
        
        details = []
        paths = path_results["paths"]
        path_names = path_results.get("path_names", [])
        
        if not paths:
            return ["No paths found"]
        
        # Path analysis
        total_paths = len(paths)
        primary_steps = len(paths[0]) - 1
        
        # Summary
        details.append(f"Found {total_paths} optimal paths!")
        details.append(f"  Primary: {primary_steps} steps")
        
        # Alternative paths summary
        for i in range(1, min(len(paths), 4)):  # Show max 3 alternatives
            alt_steps = len(paths[i]) - 1
            details.append(f"  Alternative {i}: {alt_steps} steps")
        
        # Start and end points
        if path_names and path_names[0]:
            start_name = path_names[0][0]
            end_name = path_names[0][-1]
            details.append(f"Route: {start_name} to {end_name}")
        
        return details
    
    def test_all_algorithms(self, start_location: str, goal_location: str) -> Dict[str, Any]:
        """
        Test all available algorithms on the same path.
        
        Args:
            start_location: Start location
            goal_location: Goal location
            
        Returns:
            Dictionary with results for each algorithm
        """
        algorithms = ["bfs", "dfs", "astar"]
        results = {}
        
        for algorithm in algorithms:
            print(f"\\nTesting {algorithm.upper()} algorithm...")
            result = self.find_optimal_paths(
                start_location, goal_location, algorithm, max_paths=3
            )
            results[algorithm] = result
            
            if result["success"]:
                print(f"✓ {algorithm.upper()} found {len(result['paths'])} paths")
            else:
                print(f"✗ {algorithm.upper()} failed: {result.get('message', 'Unknown error')}")
        
        return results
    
    def list_available_locations(self) -> List[str]:
        """Get list of available locations from the domain adapter."""
        return self.domain_adapter.list_available_locations()
    
    def get_path_summary(self, path_results: Dict[str, Any]) -> str:
        """
        Get a summary of path results.
        
        Args:
            path_results: Results from find_optimal_paths
            
        Returns:
            Formatted summary string
        """
        if not path_results["success"]:
            return "No path found"
        
        stats = path_results["statistics"]
        primary_path = path_results["primary_path"]
        algorithm = path_results["algorithm"]
        
        summary = f"✓ Primary optimal path found using {algorithm.upper()}!\\n"
        summary += f"  Steps: {len(primary_path)-1}\\n"
        summary += f"  Cost: {stats['avg_cost']:.0f} meters\\n"
        summary += f"  Total paths: {stats['count']}"
        
        if stats["count"] > 1:
            summary += f"\\n✓ Found {stats['count']} optimal paths!"
            for i, path in enumerate(path_results["paths"][1:], 1):
                summary += f"\\n  Alternative {i}: {len(path)-1} steps"
        
        return summary
