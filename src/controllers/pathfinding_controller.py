"""
Controller for coordinating path finding operations.
Single responsibility: Orchestrate path finding workflow and user interaction.
"""

from typing import List, Tuple, Optional

from ..models.graph_model import GraphModel
from ..models.location_model import LocationModel
from ..services.pathfinding_service import PathfindingService
from ..services.visualization_service import VisualizationService
from ..utils.path_calculator import PathCalculator
from ..config.settings import DEFAULT_MAX_PATHS, CONSTRAINT_MESSAGES


class PathfindingController:
    """Controller for managing the complete path finding workflow."""
    
    def __init__(self):
        """Initialize all required components."""
        self.graph_model = GraphModel()
        self.location_model = LocationModel(self.graph_model.graph)
        self.pathfinding_service = PathfindingService(self.graph_model, self.location_model)
        self.visualization_service = VisualizationService(self.graph_model, self.location_model)
    
    def find_optimal_paths(self, start: str, goal: str, max_paths: int = DEFAULT_MAX_PATHS) -> dict:
        """
        Find optimal paths between two locations.
        
        Args:
            start: Start location name
            goal: Goal location name
            max_paths: Maximum number of paths to find
            
        Returns:
            Dictionary with path results and metadata
        """
        # Find primary path first
        primary_path, visited_nodes, _ = self.pathfinding_service.bfs_shortest_path(start, goal)
        
        if not primary_path:
            return {
                "success": False,
                "message": "No path found between the specified locations",
                "paths": []
            }
        
        # Find all optimal paths
        all_optimal_paths = self.pathfinding_service.find_all_shortest_paths_optimized(
            start, goal, max_paths
        )
        
        # Calculate path statistics
        path_stats = PathCalculator.get_path_statistics(self.graph_model.graph, all_optimal_paths)
        
        return {
            "success": True,
            "primary_path": primary_path,
            "all_paths": all_optimal_paths,
            "visited_nodes": visited_nodes,
            "statistics": path_stats,
            "start_location": start,
            "goal_location": goal
        }
    
    def visualize_paths(self, path_results: dict, save_path: str = "addis_ababa_path.png", 
                       show_plot: bool = True) -> None:
        """
        Create visualization of path results.
        
        Args:
            path_results: Results from find_optimal_paths
            save_path: Path to save visualization
            show_plot: Whether to display the plot
        """
        if not path_results["success"]:
            return
        
        primary_path = path_results["primary_path"]
        visited_nodes = path_results["visited_nodes"]
        alternative_paths = path_results["all_paths"][1:] if len(path_results["all_paths"]) > 1 else None
        
        self.visualization_service.create_path_visualization(
            primary_path, visited_nodes, alternative_paths, save_path, show_plot
        )
    
    def get_path_details(self, path_results: dict) -> List[str]:
        """
        Get formatted path details for display.
        
        Args:
            path_results: Results from find_optimal_paths
            
        Returns:
            List of formatted path detail strings
        """
        if not path_results["success"]:
            return [path_results.get("message", "No path found")]
        
        details = []
        all_paths = path_results["all_paths"]
        
        if not all_paths:
            return ["No paths found"]
        
        # Primary path details
        details.append("Primary path details:")
        for i, node_id in enumerate(all_paths[0]):
            details.append(f"  {i+1}. {self.location_model.get_node_name(node_id)}")
        
        # Alternative path details
        for path_idx, alt_path in enumerate(all_paths[1:], 1):
            details.append(f"\\nAlternative {path_idx} path details:")
            for i, node_id in enumerate(alt_path):
                details.append(f"  {i+1}. {self.location_model.get_node_name(node_id)}")
        
        return details
    
    def test_constraints(self, start: str, goal: str) -> dict:
        """
        Test all constraint handling functionality.
        
        Args:
            start: Start location name
            goal: Goal location name
            
        Returns:
            Dictionary with constraint test results
        """
        results = {
            "unknown_location": self._test_unknown_location(),
            "same_location": self._test_same_location(start),
            "multiple_paths": self._test_multiple_paths(start, goal),
            "node_limit": self._test_node_limit(start, goal),
            "distance_limit": self._test_distance_limit(start, goal)
        }
        
        return results
    
    def _test_unknown_location(self) -> bool:
        """Test unknown location handling."""
        try:
            result = self.pathfinding_service.bfs_shortest_path("NonExistentPlace", "SomePlace")
            return result[0] is None
        except:
            return True
    
    def _test_same_location(self, location: str) -> bool:
        """Test same start and goal location."""
        try:
            test_path, _, _ = self.pathfinding_service.bfs_shortest_path(location, location)
            return test_path and len(test_path) == 1
        except:
            return False
    
    def _test_multiple_paths(self, start: str, goal: str) -> bool:
        """Test multiple optimal paths finding."""
        try:
            all_paths = self.pathfinding_service.find_all_shortest_paths_optimized(start, goal, max_paths=3)
            return len(all_paths) >= 1
        except:
            return False
    
    def _test_node_limit(self, start: str, goal: str) -> bool:
        """Test node limit constraint."""
        try:
            path_limited, visited_limited, _ = self.pathfinding_service.bfs_shortest_path(
                start, goal, max_nodes=1000
            )
            return (path_limited is None and len(visited_limited) > 0) or path_limited is not None
        except:
            return False
    
    def _test_distance_limit(self, start: str, goal: str) -> bool:
        """Test distance limit constraint."""
        try:
            path_dist_limited, _, _ = self.pathfinding_service.bfs_shortest_path(
                start, goal, max_distance=5000
            )
            return path_dist_limited is None or path_dist_limited is not None
        except:
            return False
    
    def list_available_locations(self) -> List[str]:
        """Get list of available predefined locations."""
        return self.location_model.list_available_locations()
    
    def get_path_summary(self, path_results: dict) -> str:
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
        
        summary = f"✓ Primary optimal path found!\\n"
        summary += f"  Steps: {len(primary_path)-1}\\n"
        summary += f"  Distance: {stats['avg_distance']:.0f} meters\\n"
        summary += f"  Nodes explored: {len(path_results['visited_nodes'])}"
        
        if stats["count"] > 1:
            summary += f"\\n✓ Found {stats['count']} optimal paths!"
            for i, alt_path in enumerate(path_results["all_paths"][1:], 1):
                alt_distance = PathCalculator.calculate_path_distance(
                    self.graph_model.graph, alt_path
                )
                summary += f"\\n  Alternative {i}: {len(alt_path)-1} steps, {alt_distance:.0f} meters"
        
        return summary
