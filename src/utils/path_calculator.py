"""
Utility functions for path calculations.
Single responsibility: Mathematical calculations for paths.
"""

from typing import List, Dict, Any


class PathCalculator:
    """Utility class for path-related calculations."""
    
    @staticmethod
    def calculate_path_distance(graph, path: List[int]) -> float:
        """
        Calculate total distance of a path in meters.
        
        Args:
            graph: NetworkX graph object
            path: List of node IDs representing the path
            
        Returns:
            Total distance in meters
        """
        total_distance = 0.0
        
        for i in range(len(path) - 1):
            try:
                # Get edge length if available
                edge_data = graph.get_edge_data(path[i], path[i+1])
                if edge_data and 'length' in edge_data[0]:
                    total_distance += edge_data[0]['length']
                else:
                    # Fallback: calculate Euclidean distance
                    node1_data = graph.nodes[path[i]]
                    node2_data = graph.nodes[path[i+1]]
                    lat1, lon1 = node1_data['y'], node1_data['x']
                    lat2, lon2 = node2_data['y'], node2_data['x']
                    # Simple approximation (not perfect but works for visualization)
                    distance = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 111000
                    total_distance += distance
            except:
                continue
                
        return total_distance
    
    @staticmethod
    def paths_are_similar(path1: List[int], path2: List[int], threshold: float = 0.8) -> bool:
        """
        Check if two paths are essentially the same based on node overlap.
        
        Args:
            path1: First path
            path2: Second path  
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            True if paths are similar, False otherwise
        """
        if not path2:
            return False
            
        # Calculate similarity based on common nodes
        common_nodes = set(path1) & set(path2)
        similarity = len(common_nodes) / max(len(set(path1)), len(set(path2)))
        return similarity > threshold
    
    @staticmethod
    def get_path_statistics(graph, paths: List[List[int]]) -> Dict[str, Any]:
        """
        Get statistics for a collection of paths.
        
        Args:
            graph: NetworkX graph object
            paths: List of paths
            
        Returns:
            Dictionary with path statistics
        """
        if not paths:
            return {"count": 0, "avg_distance": 0, "avg_steps": 0}
        
        distances = [PathCalculator.calculate_path_distance(graph, path) for path in paths]
        steps = [len(path) - 1 for path in paths]  # steps = nodes - 1
        
        return {
            "count": len(paths),
            "avg_distance": sum(distances) / len(distances),
            "avg_steps": sum(steps) / len(steps),
            "min_distance": min(distances),
            "max_distance": max(distances),
            "min_steps": min(steps),
            "max_steps": max(steps)
        }
