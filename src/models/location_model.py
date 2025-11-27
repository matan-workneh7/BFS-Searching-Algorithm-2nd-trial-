"""
Location model for handling location lookup and geocoding.
Single responsibility: Location data management and node lookup.
"""

import osmnx as ox
from typing import Union, Tuple, Optional

from ..config.settings import LOCATIONS


class LocationModel:
    """Manages location data and provides node lookup functionality."""
    
    def __init__(self, graph):
        """Initialize with the road network graph."""
        self.graph = graph
        self.locations = LOCATIONS
    
    def get_nearest_node(self, location: Union[str, Tuple[float, float]]) -> int:
        """
        Get the nearest node to a location.
        
        Args:
            location: Location name (str) or coordinates (lat, lon)
            
        Returns:
            Node ID nearest to the location
            
        Raises:
            ValueError: If location cannot be found
        """
        if isinstance(location, str):
            point = self._resolve_location_name(location)
        else:
            point = location
            
        return ox.distance.nearest_nodes(self.graph, point[1], point[0])
    
    def _resolve_location_name(self, location_name: str) -> Tuple[float, float]:
        """
        Resolve location name to coordinates.
        
        Args:
            location_name: Name of the location
            
        Returns:
            Tuple of (latitude, longitude)
            
        Raises:
            ValueError: If location cannot be found
        """
        # Check predefined locations first
        if location_name in self.locations:
            return self.locations[location_name]
        
        # Try to geocode the location name
        try:
            return ox.geocode(f"{location_name}, Addis Ababa, Ethiopia")
        except Exception:
            raise ValueError(f"Location '{location_name}' not found")
    
    def get_node_name(self, node_id: int) -> str:
        """
        Get human-readable name for a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Human-readable node name
        """
        node_data = self.graph.nodes[node_id]
        
        if 'name' in node_data:
            return node_data['name']
        elif 'amenity' in node_data:
            return f"{node_data['amenity']} (ID: {node_id})"
        elif 'highway' in node_data:
            return f"Highway Node {node_id}"
        return f"Node {node_id}"
    
    def list_available_locations(self) -> list:
        """Get list of all predefined locations."""
        return list(self.locations.keys())
    
    def location_exists(self, location_name: str) -> bool:
        """Check if a location exists in predefined locations."""
        return location_name in self.locations
