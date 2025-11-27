"""
Service for path finding algorithms.
Single responsibility: Path finding algorithms and constraint handling.
"""

from collections import deque
from typing import List, Set, Tuple, Optional, Iterator

from ..config.settings import CONSTRAINT_MESSAGES, DEFAULT_MAX_PATHS


class PathfindingService:
    """Service for implementing path finding algorithms."""
    
    def __init__(self, graph_model, location_model):
        """Initialize with required models."""
        self.graph_model = graph_model
        self.location_model = location_model
    
    def bfs_shortest_path(
        self, 
        start, 
        goal, 
        max_nodes: Optional[int] = None,
        max_distance: Optional[float] = None,
        find_alternative: bool = False
    ) -> Tuple[Optional[List[int]], Set[int], Optional[List[int]]]:
        """
        Find shortest path using BFS with constraint handling.
        
        Args:
            start: Start location (name or coordinates)
            goal: Goal location (name or coordinates)
            max_nodes: Maximum nodes to process
            max_distance: Maximum path distance in meters
            find_alternative: Whether to find one alternative path
            
        Returns:
            Tuple of (primary_path, visited_nodes, alternative_path)
        """
        try:
            start_node = self.location_model.get_nearest_node(start)
            goal_node = self.location_model.get_nearest_node(goal)
        except Exception as e:
            print(CONSTRAINT_MESSAGES["unknown_location"].format(e))
            return None, set(), None
        
        # Constraint: Same start and goal
        if start_node == goal_node:
            print(CONSTRAINT_MESSAGES["same_location"])
            return [start_node], {start_node}, None
        
        # BFS implementation
        queue = deque([start_node])
        visited = {start_node}
        parent = {start_node: None}
        nodes_processed = 0
        shortest_length = None
        alternative_path = None
        
        while queue:
            current = queue.popleft()
            nodes_processed += 1
            
            # Constraint: Node processing limit
            if max_nodes and nodes_processed > max_nodes:
                print(CONSTRAINT_MESSAGES["node_limit"].format(max_nodes))
                return None, visited, None
            
            for neighbor in self.graph_model.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
                    
                    if neighbor == goal_node:
                        path = self._reconstruct_path(parent, neighbor)
                        
                        # Set shortest length on first find
                        if shortest_length is None:
                            shortest_length = len(path)
                            
                            # Constraint: Distance limit
                            if max_distance:
                                from ..utils.path_calculator import PathCalculator
                                path_distance = PathCalculator.calculate_path_distance(
                                    self.graph_model.graph, path
                                )
                                if path_distance > max_distance:
                                    print(CONSTRAINT_MESSAGES["distance_limit"].format(
                                        path_distance, max_distance
                                    ))
                                    return None, visited, None
                        
                        # Find alternative path if requested
                        elif find_alternative and alternative_path is None and len(path) == shortest_length:
                            if not self._paths_are_same(path, alternative_path if alternative_path else []):
                                alternative_path = path
                                print(f"Found alternative optimal path with {len(path)-1} steps")
                                continue
                        
                        # Return primary path if not finding alternatives
                        if shortest_length is not None and not find_alternative:
                            return path, visited, None
        
        # Return results
        if shortest_length is not None:
            primary_path = self._reconstruct_path(parent, goal_node)
            return primary_path, visited, alternative_path
        
        return None, visited, None
    
    def find_all_shortest_paths_optimized(
        self, 
        start, 
        goal, 
        max_paths: int = DEFAULT_MAX_PATHS
    ) -> List[List[int]]:
        """
        Memory-efficient optimized version to find all shortest paths.
        
        Args:
            start: Start location (name or coordinates)
            goal: Goal location (name or coordinates)
            max_paths: Maximum number of paths to find
            
        Returns:
            List of optimal paths
        """
        try:
            start_node = self.location_model.get_nearest_node(start)
            goal_node = self.location_model.get_nearest_node(goal)
        except Exception as e:
            print(CONSTRAINT_MESSAGES["unknown_location"].format(e))
            return []
        
        if start_node == goal_node:
            return [[start_node]]
        
        # Build parent tree
        distance, parents = self._build_parent_tree(start_node, goal_node)
        
        if goal_node not in distance:
            return []  # No path found
        
        # Backtrack to find all paths (memory-efficient recursion)
        all_paths = []
        self._backtrack_paths(goal_node, [goal_node], all_paths, start_node, max_paths, parents)
        
        if len(all_paths) > 1:
            print(CONSTRAINT_MESSAGES["multiple_paths"].format(
                len(all_paths), distance[goal_node]
            ))
        
        return all_paths
    
    def find_all_shortest_paths_streaming(
        self, 
        start, 
        goal, 
        max_paths: int = DEFAULT_MAX_PATHS
    ) -> Iterator[List[int]]:
        """
        Streaming generator version for memory efficiency.
        
        Args:
            start: Start location (name or coordinates)
            goal: Goal location (name or coordinates)
            max_paths: Maximum number of paths to yield
            
        Yields:
            Optimal paths one at a time
        """
        try:
            start_node = self.location_model.get_nearest_node(start)
            goal_node = self.location_model.get_nearest_node(goal)
        except Exception as e:
            print(CONSTRAINT_MESSAGES["unknown_location"].format(e))
            return
        
        if start_node == goal_node:
            yield [start_node]
            return
        
        # Build parent tree
        distance, parents = self._build_parent_tree(start_node, goal_node)
        
        if goal_node not in distance:
            return
        
        # Streaming backtrack
        path_count = 0
        for path in self._stream_backtrack(goal_node, [goal_node], start_node, parents):
            if path_count >= max_paths:
                break
            yield path
            path_count += 1
    
    def _build_parent_tree(self, start_node: int, goal_node: int) -> Tuple[dict, dict]:
        """Build parent tree for path reconstruction."""
        queue = deque([start_node])
        visited = {start_node}
        distance = {start_node: 0}
        parents = {start_node: []}
        
        while queue:
            current = queue.popleft()
            
            if current == goal_node:
                break
            
            for neighbor in self.graph_model.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    distance[neighbor] = distance[current] + 1
                    parents[neighbor] = [current]
                    queue.append(neighbor)
                elif distance[neighbor] == distance[current] + 1:
                    parents[neighbor].append(current)
        
        return distance, parents
    
    def _backtrack_paths(
        self, 
        node: int, 
        current_path: List[int], 
        all_paths: List[List[int]], 
        start_node: int, 
        max_paths: int,
        parents: dict
    ) -> None:
        """Recursive backtrack with early stopping."""
        if len(all_paths) >= max_paths:
            return
        
        if node == start_node:
            all_paths.append(current_path[::-1])  # Reverse to get start->goal
            return
        
        # Try each parent (all lead to optimal paths)
        if node in parents:
            for parent in parents[node]:
                if len(all_paths) >= max_paths:
                    break
                self._backtrack_paths(parent, current_path + [parent], all_paths, start_node, max_paths, parents)
    
    def _stream_backtrack(self, node: int, current_path: List[int], 
                         start_node: int, parents: dict) -> Iterator[List[int]]:
        """Streaming backtrack using generator."""
        if node == start_node:
            yield current_path[::-1]
            return
        
        if node in parents:
            for parent in parents[node]:
                yield from self._stream_backtrack(parent, current_path + [parent], start_node, parents)
    
    def _reconstruct_path(self, parent: dict, goal_node: int) -> List[int]:
        """Reconstruct path from parent dictionary."""
        path = []
        node = goal_node
        while node is not None:
            path.append(node)
            node = parent[node]
        return path[::-1]
    
    def _paths_are_same(self, path1: List[int], path2: List[int]) -> bool:
        """Check if two paths are essentially the same."""
        if not path2:
            return False
        from ..utils.path_calculator import PathCalculator
        return PathCalculator.paths_are_similar(path1, path2)
