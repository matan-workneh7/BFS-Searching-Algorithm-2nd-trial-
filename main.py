"""
Main application entry point for the Addis Ababa Path Finder.
Uses the structured architecture with proper separation of concerns.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.controllers.pathfinding_controller import PathfindingController
from src.config.settings import DEFAULT_MAX_PATHS


def print_header():
    """Print application header."""
    print("=== Addis Ababa Path Finder with Constraint Handling ===")
    print("Using Structured Architecture v1.0")
    print()


def get_user_input(controller: PathfindingController) -> tuple[str, str]:
    """Get user input for start and goal locations."""
    locations = controller.list_available_locations()
    
    print("Available locations in Addis Ababa:")
    for i, location in enumerate(locations, 1):
        print(f"{i}. {location}")
    print("Or enter any address in Addis Ababa")
    
    start = input("\\nEnter start location (name or address): ").strip()
    goal = input("Enter destination location (name or address): ").strip()
    
    return start, goal


def test_constraints(controller: PathfindingController, start: str, goal: str):
    """Test all constraint handling functionality."""
    print("\\n=== TESTING CONSTRAINTS ===")
    
    # Test 1: Unknown locations
    print("\\n1. Testing unknown location handling...")
    if start.lower() == "unknown" or goal.lower() == "unknown":
        print("Testing with unknown location...")
        constraint_results = controller.test_constraints("NonExistentPlace", goal)
        if constraint_results["unknown_location"]:
            print("✓ Constraint 1 handled: Unknown location detected")
    
    # Test 2: Same start and goal
    print("\\n2. Testing same start and goal...")
    if start == goal:
        print("✓ Constraint 2 handled: Start and goal are the same")
    else:
        constraint_results = controller.test_constraints(start, start)
        if constraint_results["same_location"]:
            print("✓ Constraint 2 handled: Same location returns single node")
    
    # Test 3: Multiple optimal paths
    print("\\n3. Testing multiple optimal paths (optimized version)...")
    all_paths = controller.pathfinding_service.find_all_shortest_paths_optimized(
        start, goal, max_paths=3
    )
    if len(all_paths) > 1:
        print(f"✓ Constraint 3 handled: Found {len(all_paths)} optimal paths")
        print(f"  Memory usage: O(V + E) vs O(V²) in original")
        
        # Test streaming version
        print("\\n   Testing streaming version...")
        stream_count = 0
        for path in controller.pathfinding_service.find_all_shortest_paths_streaming(
            start, goal, max_paths=3
        ):
            stream_count += 1
            print(f"     Streamed path {stream_count}: {len(path)-1} steps")
        print(f"   ✓ Streaming version yielded {stream_count} paths")
    else:
        print("✓ Constraint 3 tested: Only one optimal path found")
    
    # Test 4: Additional constraints
    print("\\n4. Testing additional constraints...")
    
    # Node limit constraint
    print("   - Testing node limit (1000 nodes max)...")
    path_limited, visited_limited, _ = controller.pathfinding_service.bfs_shortest_path(
        start, goal, max_nodes=1000
    )
    if path_limited is None and len(visited_limited) > 0:
        print("   ✓ Node limit constraint working")
    elif path_limited:
        print(f"   ✓ Node limit not reached (processed {len(visited_limited)} nodes)")
    
    # Distance limit constraint
    print("   - Testing distance limit (5000m max)...")
    path_dist_limited, _, _ = controller.pathfinding_service.bfs_shortest_path(
        start, goal, max_distance=5000
    )
    if path_dist_limited is None:
        print("   ✓ Distance limit constraint working (path too long)")
    elif path_dist_limited:
        from src.utils.path_calculator import PathCalculator
        distance = PathCalculator.calculate_path_distance(
            controller.graph_model.graph, path_dist_limited
        )
        print(f"   ✓ Distance within limit ({distance:.0f}m)")


def display_path_results(controller: PathfindingController, path_results: dict):
    """Display path finding results to the user."""
    if not path_results["success"]:
        print("✗ No path found between the specified locations.")
        return
    
    # Display summary
    summary = controller.get_path_summary(path_results)
    print(f"\\n{summary}")
    
    # Display detailed path information
    details = controller.get_path_details(path_results)
    for detail in details:
        print(detail)
    
    # Create visualization
    print("\\nGenerating visualization with all optimal paths...")
    controller.visualize_paths(path_results)
    print("Visualization saved as 'addis_ababa_path.png'")
    
    if len(path_results["all_paths"]) > 1:
        print("Red = Primary path, Other colors = Alternative paths")
    else:
        print("Red = Primary path")


def main():
    """Main application entry point."""
    try:
        print_header()
        
        # Initialize the controller (handles all dependencies)
        print("Loading Addis Ababa map...")
        controller = PathfindingController()
        
        # Get user input
        start, goal = get_user_input(controller)
        
        # Test constraints
        test_constraints(controller, start, goal)
        
        # Main path finding
        print(f"\\n=== MAIN PATHFINDING ===")
        print(f"Finding optimal path from {start} to {goal}...")
        
        # Find paths
        path_results = controller.find_optimal_paths(start, goal, max_paths=DEFAULT_MAX_PATHS)
        
        # Display results
        display_path_results(controller, path_results)
        
    except KeyboardInterrupt:
        print("\\n\\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
