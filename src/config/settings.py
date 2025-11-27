"""
Configuration settings for the Addis Ababa Path Finder.
Centralized configuration management.
"""

from pathlib import Path
from typing import Dict, Tuple

# Cache Configuration
CACHE_DIR = Path("cache/osmnx")
GRAPH_CACHE_FILE = CACHE_DIR / "addis_ababa.graphml"

# Map Configuration
DEFAULT_CITY = "Addis Ababa, Ethiopia"
NETWORK_TYPE = "drive"
SIMPLIFY_GRAPH = True

# Visualization Configuration
DEFAULT_FIGSIZE = (12, 10)
DEFAULT_DPI = 300
VISUALIZATION_COLORS = {
    "primary": "red",
    "explored": "blue",
    "alternatives": ["yellow", "lime", "cyan", "magenta", "orange", "purple", "pink"],
    "base_edges": "lightgray"
}

# Path Finding Configuration
DEFAULT_MAX_PATHS = 5
DEFAULT_MAX_NODES = None
DEFAULT_MAX_DISTANCE = None
EXPLORED_LINE_WIDTH = 0.8
EXPLORED_ALPHA = 0.25
PRIMARY_LINE_WIDTH = 4
ALTERNATIVE_LINE_WIDTH = 3

# Known Locations in Addis Ababa
LOCATIONS: Dict[str, Tuple[float, float]] = {
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

# Constraint Handling Messages
CONSTRAINT_MESSAGES = {
    "unknown_location": "Error: Could not find location - {}",
    "same_location": "Constraint: Start and goal are the same location!",
    "node_limit": "Constraint: Maximum node limit ({}) reached!",
    "distance_limit": "Constraint: Path distance ({:.0f}m) exceeds limit ({}m)!",
    "multiple_paths": "Constraint: Found {} optimal paths of equal length ({}) steps"
}
