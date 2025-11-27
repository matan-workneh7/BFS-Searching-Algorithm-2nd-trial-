"""
Configuration package for the Addis Ababa Path Finder.
"""

from .settings import *

__all__ = [
    "CACHE_DIR",
    "GRAPH_CACHE_FILE", 
    "DEFAULT_CITY",
    "NETWORK_TYPE",
    "SIMPLIFY_GRAPH",
    "VISUALIZATION_COLORS",
    "DEFAULT_FIGSIZE",
    "DEFAULT_DPI",
    "DEFAULT_MAX_PATHS",
    "DEFAULT_MAX_NODES",
    "DEFAULT_MAX_DISTANCE",
    "EXPLORED_LINE_WIDTH",
    "EXPLORED_ALPHA",
    "PRIMARY_LINE_WIDTH",
    "ALTERNATIVE_LINE_WIDTH",
    "LOCATIONS",
    "CONSTRAINT_MESSAGES"
]
