"""
Service for handling path visualization.
Single responsibility: Map visualization and plot generation.
"""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from typing import List, Set, Optional

from ..config.settings import VISUALIZATION_COLORS, DEFAULT_FIGSIZE, DEFAULT_DPI


class VisualizationService:
    """Service for creating path visualizations."""
    
    def __init__(self, graph_model, location_model):
        """Initialize with required models."""
        self.graph_model = graph_model
        self.location_model = location_model
    
    def create_path_visualization(
        self,
        primary_path: List[int],
        visited_nodes: Set[int] = None,
        alternative_paths: List[List[int]] = None,
        save_path: str = "addis_ababa_path.png",
        show_plot: bool = True
    ) -> None:
        """
        Create a visualization of paths on the Addis Ababa map.
        
        Args:
            primary_path: Primary optimal path
            visited_nodes: Set of explored nodes during search
            alternative_paths: List of alternative optimal paths
            save_path: Path to save the visualization
            show_plot: Whether to display the plot
        """
        try:
            fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
            
            # Plot base graph
            self._plot_base_graph(ax)
            
            # Plot explored area
            if visited_nodes:
                self._plot_explored_area(ax, visited_nodes)
            
            # Plot alternative paths
            legend_entries = []
            if alternative_paths:
                legend_entries = self._plot_alternative_paths(ax, alternative_paths)
            
            # Plot primary path
            self._plot_primary_path(ax, primary_path)
            legend_entries.insert(0, "Primary Path")
            
            # Add title and legend
            self._add_title_and_legend(ax, primary_path, alternative_paths, legend_entries)
            
            # Save and/or show
            self._finalize_plot(fig, save_path, show_plot)
            
        except Exception as e:
            print(f"Error in visualization: {e}")
            self._fallback_text_output(primary_path, alternative_paths)
    
    def _plot_base_graph(self, ax) -> None:
        """Plot the base road network graph."""
        import osmnx as ox
        
        ox.plot_graph(
            self.graph_model.graph,
            show=False,
            close=False,
            node_size=0,  # Hide all nodes
            edge_linewidth=0.3,
            edge_color=VISUALIZATION_COLORS["base_edges"],
            ax=ax
        )
    
    def _plot_explored_area(self, ax, visited_nodes: Set[int]) -> None:
        """Plot the explored area in light blue."""
        from ..config.settings import EXPLORED_LINE_WIDTH, EXPLORED_ALPHA
        
        visited_nodes_list = list(visited_nodes)
        if visited_nodes_list:
            visited_subgraph = self.graph_model.get_subgraph(visited_nodes_list)
            
            for u, v, data in visited_subgraph.edges(data=True):
                if self.graph_model.node_exists(u) and self.graph_model.node_exists(v):
                    x_coords = [self.graph_model.get_node_data(u)['x'], 
                               self.graph_model.get_node_data(v)['x']]
                    y_coords = [self.graph_model.get_node_data(u)['y'], 
                               self.graph_model.get_node_data(v)['y']]
                    ax.plot(x_coords, y_coords, 'b-', 
                           linewidth=EXPLORED_LINE_WIDTH, 
                           alpha=EXPLORED_ALPHA)
    
    def _plot_alternative_paths(self, ax, alternative_paths: List[List[int]]) -> List[str]:
        """Plot all alternative paths with distinct colors."""
        from ..config.settings import ALTERNATIVE_LINE_WIDTH
        
        colors = VISUALIZATION_COLORS["alternatives"]
        legend_entries = []
        
        for i, alt_path in enumerate(alternative_paths):
            if i < len(colors) and alt_path and len(alt_path) > 1:
                color = colors[i]
                self._draw_path(ax, alt_path, color, ALTERNATIVE_LINE_WIDTH)
                legend_entries.append(f'Alternative {i+1}')
                
        return legend_entries
    
    def _plot_primary_path(self, ax, primary_path: List[int]) -> None:
        """Plot the primary path in red."""
        from ..config.settings import PRIMARY_LINE_WIDTH
        
        if primary_path and len(primary_path) > 1:
            self._draw_path(ax, primary_path, VISUALIZATION_COLORS["primary"], PRIMARY_LINE_WIDTH)
    
    def _draw_path(self, ax, path: List[int], color: str, linewidth: float) -> None:
        """Draw a single path on the map."""
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            if self.graph_model.node_exists(u) and self.graph_model.node_exists(v):
                x_coords = [self.graph_model.get_node_data(u)['x'], 
                           self.graph_model.get_node_data(v)['x']]
                y_coords = [self.graph_model.get_node_data(u)['y'], 
                           self.graph_model.get_node_data(v)['y']]
                ax.plot(x_coords, y_coords, color=color, linewidth=linewidth, alpha=0.9)
    
    def _add_title_and_legend(self, ax, primary_path: List[int], 
                             alternative_paths: List[List[int]], 
                             legend_entries: List[str]) -> None:
        """Add title and legend to the plot."""
        # Add title
        start_name = self.location_model.get_node_name(primary_path[0]) if primary_path else "Start"
        end_name = self.location_model.get_node_name(primary_path[-1]) if primary_path else "End"
        title = f"Path from {start_name} to {end_name}"
        if alternative_paths:
            title += f" ({len(alternative_paths)} alternatives)"
        plt.title(title, fontsize=16, fontweight='bold')
        
        # Add legend
        if legend_entries:
            colors = [VISUALIZATION_COLORS["primary"]] + VISUALIZATION_COLORS["alternatives"][:len(alternative_paths)]
            legend_handles = []
            for entry, color in zip(legend_entries, colors):
                legend_handles.append(Line2D([0], [0], color=color, linewidth=3, label=entry))
            ax.legend(handles=legend_handles, loc='upper right', fontsize=12)
        
        # Remove axis for cleaner look
        ax.axis('off')
        
        # Add instruction text
        plt.figtext(0.5, 0.02, "Close this window to continue...", 
                   ha="center", fontsize=10, style='italic')
    
    def _finalize_plot(self, fig, save_path: str, show_plot: bool) -> None:
        """Save and/or display the plot."""
        if save_path:
            plt.savefig(save_path, dpi=DEFAULT_DPI, bbox_inches='tight', facecolor='white')
            print(f"Visualization saved as '{save_path}'")
        
        if show_plot:
            print("Map window opened. Close it manually to continue...")
            plt.show(block=True)
        else:
            plt.close(fig)
    
    def _fallback_text_output(self, primary_path: List[int], 
                             alternative_paths: List[List[int]]) -> None:
        """Fallback text output when visualization fails."""
        from ..utils.path_calculator import PathCalculator
        
        print(f"Path details: {len(primary_path)-1 if primary_path else 0} steps")
        if primary_path:
            print(f"Start: {self.location_model.get_node_name(primary_path[0])}")
            print(f"End: {self.location_model.get_node_name(primary_path[-1])}")
        
        if alternative_paths:
            for i, alt_path in enumerate(alternative_paths, 1):
                print(f"Alternative {i} path: {len(alt_path)-1} steps")
