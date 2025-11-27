"""
Utility for validating constraints and business rules.
Single responsibility: Constraint validation and rule checking.
"""

from typing import Tuple, Optional, List, Dict, Any


class ConstraintValidator:
    """Utility class for validating various constraints."""
    
    @staticmethod
    def validate_locations(start: str, goal: str, location_model) -> Tuple[bool, Optional[str]]:
        """
        Validate that start and goal locations are valid.
        
        Args:
            start: Start location name
            goal: Goal location name
            location_model: Location model instance
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            start_node = location_model.get_nearest_node(start)
            goal_node = location_model.get_nearest_node(goal)
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def validate_same_location(start: str, goal: str) -> Tuple[bool, str]:
        """
        Check if start and goal are the same location.
        
        Args:
            start: Start location
            goal: Goal location
            
        Returns:
            Tuple of (is_same, message)
        """
        is_same = start.lower().strip() == goal.lower().strip()
        message = "Start and goal are the same location!" if is_same else ""
        return is_same, message
    
    @staticmethod
    def validate_node_limit(nodes_processed: int, max_nodes: Optional[int]) -> Tuple[bool, str]:
        """
        Validate node processing limit.
        
        Args:
            nodes_processed: Number of nodes processed
            max_nodes: Maximum allowed nodes
            
        Returns:
            Tuple of (exceeded_limit, message)
        """
        if max_nodes and nodes_processed > max_nodes:
            return True, f"Maximum node limit ({max_nodes}) reached!"
        return False, ""
    
    @staticmethod
    def validate_distance_limit(path_distance: float, max_distance: Optional[float]) -> Tuple[bool, str]:
        """
        Validate path distance limit.
        
        Args:
            path_distance: Calculated path distance
            max_distance: Maximum allowed distance
            
        Returns:
            Tuple of (exceeded_limit, message)
        """
        if max_distance and path_distance > max_distance:
            return True, f"Path distance ({path_distance:.0f}m) exceeds limit ({max_distance}m)!"
        return False, ""
    
    @staticmethod
    def validate_path_quality(path: List[int]) -> Dict[str, Any]:
        """
        Validate path quality and return metrics.
        
        Args:
            path: List of node IDs representing the path
            
        Returns:
            Dictionary with path quality metrics
        """
        if not path:
            return {"valid": False, "message": "Empty path"}
        
        return {
            "valid": True,
            "steps": len(path) - 1,
            "nodes": len(path),
            "has_duplicates": len(path) != len(set(path)),
            "is_loop": path[0] == path[-1] if len(path) > 1 else False
        }
    
    @staticmethod
    def validate_multiple_paths(paths: List[List[int]], max_paths: int) -> Dict[str, Any]:
        """
        Validate multiple paths and return statistics.
        
        Args:
            paths: List of paths
            max_paths: Maximum expected paths
            
        Returns:
            Dictionary with validation results
        """
        if not paths:
            return {"valid": False, "message": "No paths found"}
        
        path_lengths = [len(path) for path in paths]
        unique_lengths = set(path_lengths)
        
        return {
            "valid": True,
            "count": len(paths),
            "max_requested": max_paths,
            "exceeded_limit": len(paths) > max_paths,
            "all_same_length": len(unique_lengths) == 1,
            "lengths": path_lengths,
            "unique_lengths": list(unique_lengths)
        }
