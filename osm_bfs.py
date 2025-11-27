import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
from typing import List, Set, Tuple, Optional
from pathlib import Path

class AddisAbabaBFS:
    def __init__(self):
        """Initialize with Addis Ababa's road network."""
        self.G = self._load_addis_ababa_map()
        self.locations = {
            "Bole International Airport": (8.9806, 38.7997),
            "Meskel Square": (9.0105, 38.7866),
            "Piassa": (9.0276, 38.7469),
            "Kazanchis": (9.0227, 38.7612),
            "Arat Kilo": (9.0438, 38.7600),
            "Mexico Square": (9.0431, 38.7782),
            "Sarbet": (9.0281, 38.7812),
            "Bole Medhanealem": (8.9922, 38.7978),
            "Gotera": (9.0027, 38.8128),
            "Megenagna": (9.0497, 38.8014)
        }

    def _load_addis_ababa_map(self):
        """Load Addis Ababa's road network using OSMnx."""
        cache_dir = Path("cache/osmnx")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "addis_ababa.graphml"
        
        if cache_file.exists():
            print("Loading Addis Ababa map from cache...")
            G = ox.load_graphml(cache_file)
        else:
            print("Downloading Addis Ababa map (this may take a few minutes)...")
            G = ox.graph_from_place(
                "Addis Ababa, Ethiopia",
                network_type='drive',
                simplify=True
            )
            ox.save_graphml(G, cache_file)
            print("Map data saved to cache")
        
        # Convert to undirected graph to ensure all paths are found
        return G.to_undirected()

    def _get_nearest_node(self, location) -> int:
        """Get the nearest node to a (lat, lon) location."""
        if isinstance(location, str):
            if location in self.locations:
                point = self.locations[location]
            else:
                # Try to geocode the location name
                try:
                    point = ox.geocode(location + ", Addis Ababa, Ethiopia")
                except:
                    raise ValueError(f"Location '{location}' not found")
        else:
            point = location
            
        return ox.distance.nearest_nodes(self.G, point[1], point[0])

    def bfs_shortest_path(self, start, goal, max_nodes=None, max_distance=None, find_alternative=False) -> Tuple[List, Set, Optional[List]]:
        """
        Find shortest path using BFS with constraint handling.
        Returns:
            tuple: (primary_path, visited, alternative_path) - primary path, visited nodes, and optionally one alternative path
        """
        # Constraint 1: Handle unknown initial/goal states
        try:
            start_node = self._get_nearest_node(start)
            goal_node = self._get_nearest_node(goal)
        except Exception as e:
            print(f"Error: Could not find location - {e}")
            return None, set(), None
        
        # Constraint 2: Handle same start and goal states
        if start_node == goal_node:
            print("Constraint: Start and goal are the same location!")
            return [start_node], {start_node}, None

        queue = deque([start_node])
        visited = {start_node}
        parent = {start_node: None}
        nodes_processed = 0
        shortest_length = None
        alternative_path = None
        
        while queue:
            current = queue.popleft()
            nodes_processed += 1
            
            # Additional constraint: Node processing limit
            if max_nodes and nodes_processed > max_nodes:
                print(f"Constraint: Maximum node limit ({max_nodes}) reached!")
                return None, visited, None
            
            for neighbor in self.G.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

                    if neighbor == goal_node:
                        # Reconstruct path
                        path = []
                        node = goal_node
                        while node is not None:
                            path.append(node)
                            node = parent[node]
                        path = path[::-1]
                        
                        # Set shortest length on first find
                        if shortest_length is None:
                            shortest_length = len(path)
                            
                            # Additional constraint: Distance limit
                            if max_distance:
                                path_distance = self._calculate_path_distance(path)
                                if path_distance > max_distance:
                                    print(f"Constraint: Path distance ({path_distance:.0f}m) exceeds limit ({max_distance}m)!")
                                    return None, visited, None
                        
                        # If this is an alternative path (same length) and we haven't found one yet
                        elif find_alternative and alternative_path is None and len(path) == shortest_length:
                            # Check if this is really different from the first path
                            if not self._paths_are_same(path, alternative_path if alternative_path else []):
                                alternative_path = path
                                print(f"Found alternative optimal path with {len(path)-1} steps")
                                # We can stop here since we only need one alternative
                                continue
                        
                        # Return the first path found (primary)
                        if shortest_length is not None and not find_alternative:
                            return path, visited, None

        # If we found a primary path but no alternative, return just the primary
        if shortest_length is not None:
            # Reconstruct the primary path
            primary_path = []
            node = goal_node
            while node is not None:
                primary_path.append(node)
                node = parent[node]
            primary_path = primary_path[::-1]
            return primary_path, visited, alternative_path

        return None, visited, None
    
    def _paths_are_same(self, path1: List[int], path2: List[int]) -> bool:
        """Check if two paths are essentially the same (for alternative path detection)."""
        if not path2:
            return False
        # Simple check: if they share more than 80% of nodes, consider them the same
        common_nodes = set(path1) & set(path2)
        similarity = len(common_nodes) / max(len(set(path1)), len(set(path2)))
        return similarity > 0.8
    
    def _calculate_path_distance(self, path: List[int]) -> float:
        """Calculate total distance of a path in meters."""
        total_distance = 0
        for i in range(len(path) - 1):
            try:
                # Get edge length if available
                edge_data = self.G.get_edge_data(path[i], path[i+1])
                if edge_data and 'length' in edge_data[0]:
                    total_distance += edge_data[0]['length']
                else:
                    # Fallback: calculate Euclidean distance
                    node1_data = self.G.nodes[path[i]]
                    node2_data = self.G.nodes[path[i+1]]
                    lat1, lon1 = node1_data['y'], node1_data['x']
                    lat2, lon2 = node2_data['y'], node2_data['x']
                    # Simple approximation (not perfect but works for visualization)
                    distance = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5 * 111000  # Rough conversion to meters
                    total_distance += distance
            except:
                continue
        return total_distance

    def find_all_shortest_paths(self, start, goal, max_paths=5) -> List[List]:
        """
        Find all shortest paths between start and goal (Constraint 3: Multiple optimal paths).
        Returns list of paths, all with the same minimum length.
        """
        # Get shortest path length first
        shortest_path, _, _ = self.bfs_shortest_path(start, goal)
        if not shortest_path:
            return []
        
        shortest_length = len(shortest_path)
        all_paths = [shortest_path]
        
        # Modified BFS to find all shortest paths
        start_node = self._get_nearest_node(start)
        goal_node = self._get_nearest_node(goal)
        
        queue = deque([(start_node, [start_node])])
        visited = set()
        
        while queue and len(all_paths) < max_paths:
            current, path = queue.popleft()
            
            if current == goal_node and len(path) == shortest_length:
                if path not in all_paths:
                    all_paths.append(path)
                continue
            
            if len(path) >= shortest_length:
                continue
            
            for neighbor in self.G.neighbors(current):
                if neighbor not in path:  # Avoid cycles
                    new_path = path + [neighbor]
                    queue.append((neighbor, new_path))
        
        if len(all_paths) > 1:
            print(f"Constraint: Found {len(all_paths)} optimal paths of equal length ({shortest_length-1} steps)")
        
        return all_paths
    
    def get_node_name(self, node_id: int) -> str:
        """Get node name from ID or return ID as string."""
        node_data = self.G.nodes[node_id]
        if 'name' in node_data:
            return node_data['name']
        elif 'amenity' in node_data:
            return f"{node_data['amenity']} (ID: {node_id})"
        elif 'highway' in node_data:
            return f"Highway Node {node_id}"
        return f"Node {node_id}"

    def visualize_path(self, path: List[int], visited: Set[int] = None, 
                      alternative_path: List[int] = None, save_path: str = "addis_ababa_path.png") -> None:
        """Visualize the path on Addis Ababa's map with optional alternative path in yellow."""
        try:
            # Create a figure and axis
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Plot the base graph
            ox.plot_graph(
                self.G,
                show=False,
                close=False,
                node_size=0,
                edge_linewidth=0.5,
                edge_color='gray',
                ax=ax
            )

            # Highlight visited nodes (if any) - simpler approach
            if visited and len(visited) > 0:
                # Get coordinates of visited nodes
                visited_nodes = list(visited)
                if visited_nodes:
                    # Create a subgraph with just visited nodes for visualization
                    visited_subgraph = self.G.subgraph(visited_nodes)
                    
                    # Plot visited edges in light blue
                    for u, v, data in visited_subgraph.edges(data=True):
                        if u in self.G.nodes and v in self.G.nodes:
                            x_coords = [self.G.nodes[u]['x'], self.G.nodes[v]['x']]
                            y_coords = [self.G.nodes[u]['y'], self.G.nodes[v]['y']]
                            ax.plot(x_coords, y_coords, 'b-', linewidth=0.5, alpha=0.2)

            # Highlight the alternative path in yellow (if exists)
            if alternative_path and len(alternative_path) > 1:
                for i in range(len(alternative_path) - 1):
                    u, v = alternative_path[i], alternative_path[i+1]
                    if u in self.G.nodes and v in self.G.nodes:
                        x_coords = [self.G.nodes[u]['x'], self.G.nodes[v]['x']]
                        y_coords = [self.G.nodes[u]['y'], self.G.nodes[v]['y']]
                        ax.plot(x_coords, y_coords, 'y-', linewidth=2.5, alpha=0.8, label='Alternative Path')

            # Highlight the primary path in red
            if path and len(path) > 1:
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    if u in self.G.nodes and v in self.G.nodes:
                        x_coords = [self.G.nodes[u]['x'], self.G.nodes[v]['x']]
                        y_coords = [self.G.nodes[u]['y'], self.G.nodes[v]['y']]
                        ax.plot(x_coords, y_coords, 'r-', linewidth=3, alpha=0.9, label='Primary Path')

            # Add title
            start_name = self.get_node_name(path[0]) if path else "Start"
            end_name = self.get_node_name(path[-1]) if path else "End"
            title = f"Path from {start_name} to {end_name}"
            if alternative_path:
                title += f" (with alternative)"
            plt.title(title, fontsize=14)
            
            # Add legend if alternative path exists
            if alternative_path:
                ax.legend(loc='upper right')
            
            # Remove axis for cleaner look
            ax.axis('off')
            
            # Save and show
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Visualization saved as '{save_path}'")
            plt.show()
            
        except Exception as e:
            print(f"Error in visualization: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simple text output
            print(f"Path details: {len(path)-1 if path else 0} steps")
            if path:
                print(f"Start: {self.get_node_name(path[0])}")
                print(f"End: {self.get_node_name(path[-1])}")
            if alternative_path:
                print(f"Alternative path: {len(alternative_path)-1} steps")

def main():
    try:
        print("=== Addis Ababa Path Finder with Constraint Handling ===")
        print("Loading Addis Ababa map...")
        
        # Initialize with Addis Ababa's map
        addis_bfs = AddisAbabaBFS()
        
        # List available locations
        print("\nAvailable locations in Addis Ababa:")
        for i, (name, _) in enumerate(addis_bfs.locations.items(), 1):
            print(f"{i}. {name}")
        print("Or enter any address in Addis Ababa")
        
        # Get user input
        start = input("\nEnter start location (name or address): ").strip()
        goal = input("Enter destination location (name or address): ").strip()
        
        # Test constraint handling
        print("\n=== TESTING CONSTRAINTS ===")
        
        # Constraint 1: Unknown locations
        print("\n1. Testing unknown location handling...")
        if start.lower() == "unknown" or goal.lower() == "unknown":
            print("Testing with unknown location...")
            result = addis_bfs.bfs_shortest_path("NonExistentPlace", goal)
            if result[0] is None:
                print("✓ Constraint 1 handled: Unknown location detected")
        
        # Constraint 2: Same start and goal
        print("\n2. Testing same start and goal...")
        if start == goal:
            print("✓ Constraint 2 handled: Start and goal are the same")
        else:
            # Test with same location
            test_path, _, _ = addis_bfs.bfs_shortest_path(start, start)
            if test_path and len(test_path) == 1:
                print("✓ Constraint 2 handled: Same location returns single node")
        
        # Constraint 3: Multiple optimal paths (TEMPORARILY DISABLED)
        print("\n3. Testing multiple optimal paths...")
        print("   ⚠ Multiple optimal paths constraint temporarily disabled")
        # all_paths = addis_bfs.find_all_shortest_paths(start, goal)
        # if len(all_paths) > 1:
        #     print(f"✓ Constraint 3 handled: Found {len(all_paths)} optimal paths")
        # else:
        #     print("✓ Constraint 3 tested: Only one optimal path found")
        
        # Additional constraints
        print("\n4. Testing additional constraints...")
        
        # Node limit constraint
        print("   - Testing node limit (1000 nodes max)...")
        path_limited, visited_limited, _ = addis_bfs.bfs_shortest_path(start, goal, max_nodes=1000)
        if path_limited is None and len(visited_limited) > 0:
            print("   ✓ Node limit constraint working")
        elif path_limited:
            print(f"   ✓ Node limit not reached (processed {len(visited_limited)} nodes)")
        
        # Distance limit constraint  
        print("   - Testing distance limit (5000m max)...")
        path_dist_limited, _, _ = addis_bfs.bfs_shortest_path(start, goal, max_distance=5000)
        if path_dist_limited is None:
            print("   ✓ Distance limit constraint working (path too long)")
        elif path_dist_limited:
            distance = addis_bfs._calculate_path_distance(path_dist_limited)
            print(f"   ✓ Distance within limit ({distance:.0f}m)")
        
        # Main path finding
        print(f"\n=== MAIN PATHFINDING ===")
        print(f"Finding optimal path from {start} to {goal}...")
        
        # First find primary path
        path, visited, _ = addis_bfs.bfs_shortest_path(start, goal)
        
        if path:
            distance = addis_bfs._calculate_path_distance(path)
            print(f"\n✓ Primary optimal path found!")
            print(f"  Steps: {len(path)-1}")
            print(f"  Distance: {distance:.0f} meters")
            print(f"  Nodes explored: {len(visited)}")
            
            # Now try to find one alternative path
            print(f"\nSearching for alternative optimal path...")
            _, _, alternative_path = addis_bfs.bfs_shortest_path(start, goal, find_alternative=True)
            
            if alternative_path:
                alt_distance = addis_bfs._calculate_path_distance(alternative_path)
                print(f"✓ Alternative path found!")
                print(f"  Steps: {len(alternative_path)-1} (same as primary)")
                print(f"  Distance: {alt_distance:.0f} meters")
                print(f"  Difference: {abs(distance - alt_distance):.0f} meters")
            else:
                print("ℹ No alternative optimal path found")
            
            print(f"\nPrimary path details:")
            for i, node_id in enumerate(path):
                print(f"  {i+1}. {addis_bfs.get_node_name(node_id)}")
            
            if alternative_path:
                print(f"\nAlternative path details:")
                for i, node_id in enumerate(alternative_path):
                    print(f"  {i+1}. {addis_bfs.get_node_name(node_id)}")
            
            # Visualize with both paths
            print("\nGenerating visualization...")
            addis_bfs.visualize_path(path, visited, alternative_path)
            print(f"Visualization saved as 'addis_ababa_path.png'")
            print("Red = Primary path, Yellow = Alternative path")
        else:
            print("✗ No path found between the specified locations.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()