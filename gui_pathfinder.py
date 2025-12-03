#!/usr/bin/env python3
"""
GUI Path Finder using Tkinter.
Map display on left, output on right, with algorithm selection and location inputs.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
from pathlib import Path
import threading
import tempfile
import webbrowser
from typing import List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import networkx as nx
import osmnx as ox
import contextily as ctx
import folium
from difflib import get_close_matches

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.controllers.generic_pathfinding_controller import GenericPathfindingController
from src.controllers.classic_dfs_controller import ClassicDFSController
from src.controllers.astar_controller import AStarController
from src.services.place_index_service import PlaceIndexService


class PathFinderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Path Finder - Addis Ababa")
        self.root.geometry("1400x800")
        
        # Initialize place index (downloads + caches Addis Ababa place names)
        self.place_index = PlaceIndexService()
        
        # Initialize controllers
        self.bfs_controller = GenericPathfindingController()
        self.dfs_controller = ClassicDFSController()
        from core.addis_ababa_adapter import AddisAbabaAdapter
        adapter = AddisAbabaAdapter()
        self.astar_controller = AStarController(adapter)
        # Store last successful pathfinding result for web map visualization
        self.last_result = None
        
        # Available locations with common variations and aliases (static list)
        static_locations = [
            "Bole International Airport", "Bole Airport", "Airport",
            "Meskel Square", "Meskel Sq", "Meskel",
            "Piassa", "Piazza", "Piaza",
            "Kazanchis", "Kazanchis Area", "Kazanchis Square",
            "Arat Kilo", "Arada", "Arada Kilo", "4 Kilo",
            "Mexico Square", "Mexico", "Mexico Area",
            "Sarbet", "Sarbet Area", "Sarbet Road",
            "Bole Medhanealem", "Medhanealem", "Bole Meda",
            "Gotera", "Gotera Interchange", "Gotera Area",
            "Megenagna", "Megenagna Square", "Megenagna Area"
        ]
        
        # Combine static locations with dynamic OSM-based index for suggestions
        osm_locations = self.place_index.get_all_names()
        self.locations = list(dict.fromkeys(static_locations + osm_locations))
        
        # Original location mapping for display
        self.original_locations = [
            "Bole International Airport", "Meskel Square", "Piassa",
            "Kazanchis", "Arat Kilo", "Mexico Square", "Sarbet",
            "Bole Medhanealem", "Gotera", "Megenagna"
        ]
        
        # Location mapping from variations to original names
        self.location_mapping = {}
        for loc in self.original_locations:
            self.location_mapping[loc.lower()] = loc
            
        # Add common variations
        variations = {
            "Bole International Airport": ["bole airport", "airport", "bole intl airport"],
            "Meskel Square": ["meskel sq", "meskel"],
            "Piassa": ["piazza", "piaza"],
            "Arat Kilo": ["arada", "arada kilo", "4 kilo"],
            "Mexico Square": ["mexico", "mexico area"],
            "Sarbet": ["sarbet area", "sarbet road"],
            "Bole Medhanealem": ["medhanealem", "bole meda"],
            "Gotera": ["gotera interchange", "gotera area"],
            "Megenagna": ["megenagna square", "megenagna area"]
        }
        
        for original, vars in variations.items():
            for var in vars:
                self.location_mapping[var.lower()] = original
        
        # Current algorithm
        self.current_algorithm = tk.StringVar(value="BFS")
        
        # Setup suggestion lists
        self.start_listbox = None
        self.end_listbox = None
        self.start_list_visible = False
        self.end_list_visible = False
        
        # Setup GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the main GUI layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Top panel - Controls
        self.setup_control_panel(main_frame)
        
        # Middle panel - Map and Output
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Left panel - Map
        self.setup_map_panel(content_frame)
        
        # Right panel - Output
        self.setup_output_panel(content_frame)
        
    def setup_control_panel(self, parent):
        """Setup the control panel with inputs and algorithm selection."""
        control_frame = ttk.LabelFrame(parent, text="Path Finding Controls", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start Location
        ttk.Label(control_frame, text="Start Location:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.start_var = tk.StringVar()
        self.start_entry = ttk.Entry(control_frame, textvariable=self.start_var, width=30)
        self.start_entry.grid(row=0, column=1, padx=(0, 20))
        # Show suggestions only while typing
        self.start_entry.bind('<KeyRelease>', lambda e: self._on_entry_key('start'))
        
        # End Location
        ttk.Label(control_frame, text="Destination:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.end_var = tk.StringVar()
        self.end_entry = ttk.Entry(control_frame, textvariable=self.end_var, width=30)
        self.end_entry.grid(row=0, column=3, padx=(0, 20))
        # Show suggestions only while typing
        self.end_entry.bind('<KeyRelease>', lambda e: self._on_entry_key('end'))
        
        # Algorithm Selection
        ttk.Label(control_frame, text="Algorithm:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        algorithm_frame = ttk.Frame(control_frame)
        algorithm_frame.grid(row=0, column=5, padx=(0, 20))
        
        ttk.Radiobutton(algorithm_frame, text="BFS", variable=self.current_algorithm, 
                       value="BFS").grid(row=0, column=0, padx=(0, 10))
        ttk.Radiobutton(algorithm_frame, text="DFS", variable=self.current_algorithm, 
                       value="DFS").grid(row=0, column=1, padx=(0, 10))
        ttk.Radiobutton(algorithm_frame, text="A*", variable=self.current_algorithm, 
                       value="A*").grid(row=0, column=2)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=6, padx=(10, 0))
        
        self.find_button = ttk.Button(button_frame, text="Find Path", command=self.find_path)
        self.find_button.grid(row=0, column=0, padx=(0, 5))
        
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_all)
        self.clear_button.grid(row=0, column=1, padx=(0, 5))

        # Open interactive web map (Folium/Leaflet)
        self.webmap_button = ttk.Button(button_frame, text="Open Web Map", command=self.open_interactive_map)
        self.webmap_button.grid(row=0, column=2, padx=(0, 5))
        
    def setup_map_panel(self, parent):
        """Setup the map display panel with zoom controls."""
        map_frame = ttk.LabelFrame(parent, text="Map Visualization", padding="10")
        map_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Create matplotlib figure for map
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add navigation toolbar for zoom/pan controls
        toolbar_frame = ttk.Frame(map_frame)
        toolbar_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Enable zoom with mouse wheel
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        
        # Store original view limits for reset
        self.original_xlim = None
        self.original_ylim = None
        
        # Load initial map
        self.load_initial_map()
        
    def setup_output_panel(self, parent):
        """Setup the output display panel."""
        output_frame = ttk.LabelFrame(parent, text="Results Output", padding="10")
        output_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Create scrolled text widget for output
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=60, height=40)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for formatting
        self.output_text.tag_configure("success", foreground="green", font=("Arial", 10, "bold"))
        self.output_text.tag_configure("error", foreground="red", font=("Arial", 10, "bold"))
        self.output_text.tag_configure("info", foreground="blue", font=("Arial", 10, "bold"))
        self.output_text.tag_configure("header", font=("Arial", 12, "bold"))
        
    def load_initial_map(self):
        """Load the initial Addis Ababa map."""
        try:
            # Get the graph from BFS controller's domain adapter
            graph = self.bfs_controller.domain_adapter.graph_model.graph

            # Plot the road network
            self.ax.clear()
            ox.plot_graph(
                graph,
                ax=self.ax,
                show=False,
                close=False,
                node_size=0,
                edge_color="orange",
                edge_linewidth=1.0,
                bgcolor="white",
            )

            # Add real map tiles behind the graph using OpenStreetMap via contextily
            try:
                ctx.add_basemap(
                    self.ax,
                    crs="EPSG:4326",  # graph is in lat/lon
                    source=ctx.providers.OpenStreetMap.Mapnik,
                )
            except Exception as tile_err:
                # If tiles fail to load (offline, rate limit, etc.), continue with graph only
                print(f"Warning: could not load basemap tiles: {tile_err}")

            self.ax.set_title("Addis Ababa Road Network (with OSM basemap)", fontsize=14, fontweight='bold')
            
            # Store original limits for reset functionality
            self.original_xlim = self.ax.get_xlim()
            self.original_ylim = self.ax.get_ylim()
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error loading map: {e}")
            # Create empty plot
            self.ax.clear()
            self.ax.text(0.5, 0.5, "Map loading failed\nPath finding still works", 
                        ha='center', va='center', transform=self.ax.transAxes, fontsize=12)
            self.ax.set_title("Addis Ababa Road Network", fontsize=14, fontweight='bold')
            self.original_xlim = self.ax.get_xlim()
            self.original_ylim = self.ax.get_ylim()
            self.canvas.draw()
    
    def on_scroll(self, event):
        """Handle mouse wheel zoom."""
        if event.inaxes != self.ax:
            return
            
        # Get current x and y limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # Get mouse position in data coordinates
        xdata = event.xdata
        ydata = event.ydata
        
        # Determine zoom direction
        if event.button == 'up':
            # Zoom in
            scale_factor = 0.9
        else:
            # Zoom out
            scale_factor = 1.1
            
        # Calculate new limits
        new_width = (xlim[1] - xlim[0]) * scale_factor
        new_height = (ylim[1] - ylim[0]) * scale_factor
        
        # Center on mouse position
        relx = (xdata - xlim[0]) / (xlim[1] - xlim[0])
        rely = (ydata - ylim[0]) / (ylim[1] - ylim[0])
        
        new_xlim = [
            xdata - new_width * relx,
            xdata + new_width * (1 - relx)
        ]
        new_ylim = [
            ydata - new_height * rely,
            ydata + new_height * (1 - rely)
        ]
        
        # Apply new limits
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw_idle()
    
    def on_mouse_press(self, event):
        """Handle mouse click for pan mode."""
        if event.inaxes != self.ax:
            return
            
        # Middle mouse button to reset view
        if event.button == 2:  # Middle button
            self.reset_view()
    
    def reset_view(self):
        """Reset the map view to original limits."""
        if self.original_xlim and self.original_ylim:
            self.ax.set_xlim(self.original_xlim)
            self.ax.set_ylim(self.original_ylim)
            self.canvas.draw_idle()
            
    def _get_original_location(self, location):
        """Get the original location name from user input."""
        if not location:
            return None
            
        # Check for exact match first
        loc_lower = location.lower()
        if loc_lower in self.location_mapping:
            return self.location_mapping[loc_lower]
            
        # Try to find close matches
        matches = get_close_matches(loc_lower, self.location_mapping.keys(), n=1, cutoff=0.5)
        if matches:
            return self.location_mapping[matches[0]]
            
        return None
        
    def _on_entry_key(self, entry_type):
        """Handle key input in location entries and manage suggestions."""
        if entry_type == 'start':
            text = self.start_var.get().strip().lower()
        else:
            text = self.end_var.get().strip().lower()

        if not text:
            # No text -> hide suggestions completely
            self._hide_search_list(entry_type)
            return

        self._update_search_suggestions(entry_type, text)

    def _update_search_suggestions(self, entry_type, current):
        """Update the search suggestions in real-time."""
        # Find all locations that contain the current input
        matches = [loc for loc in self.locations if current in loc.lower()]

        # If no matches, try fuzzy matching
        if not matches:
            matches = get_close_matches(current, self.locations, n=5, cutoff=0.4)

        if not matches:
            # Nothing to show
            self._hide_search_list(entry_type)
            return

        # Update the listbox with suggestions
        self._update_listbox(entry_type, matches[:10])

    def _create_listbox(self, entry_type):
        """Create a listbox for suggestions."""
        if entry_type == 'start':
            entry = self.start_entry
        else:
            entry = self.end_entry
            
        # Get entry position
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
        
        # Create listbox as a toplevel window
        list_window = tk.Toplevel(self.root)
        list_window.overrideredirect(True)  # Remove window decorations
        list_window.geometry(f"{entry.winfo_width()}x150")
        list_window.geometry(f"+{x}+{y}")
        
        listbox = tk.Listbox(list_window, height=6, font=("Arial", 10))
        listbox.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection
        listbox.bind('<ButtonRelease-1>', lambda e: self._select_suggestion(entry_type))
        listbox.bind('<Return>', lambda e: self._select_suggestion(entry_type))
        
        return list_window, listbox
        
    def _update_listbox(self, entry_type, suggestions):
        """Update the listbox with new suggestions."""
        if entry_type == 'start':
            if not self.start_listbox:
                self.start_list_window, self.start_listbox = self._create_listbox('start')
                self.start_list_visible = True
            listbox = self.start_listbox
        else:
            if not self.end_listbox:
                self.end_list_window, self.end_listbox = self._create_listbox('end')
                self.end_list_visible = True
            listbox = self.end_listbox
            
        # Clear and update listbox
        listbox.delete(0, tk.END)
        for suggestion in suggestions:
            listbox.insert(tk.END, suggestion)
            
    def _clear_listbox(self, entry_type):
        """Clear the listbox."""
        if entry_type == 'start' and self.start_listbox:
            self.start_listbox.delete(0, tk.END)
        elif entry_type == 'end' and self.end_listbox:
            self.end_listbox.delete(0, tk.END)
            
    def _select_suggestion(self, entry_type):
        """Select a suggestion from the listbox."""
        if entry_type == 'start' and self.start_listbox:
            selection = self.start_listbox.curselection()
            if selection:
                selected = self.start_listbox.get(selection[0])
                # Prefer canonical mapped name, but fall back to selected text
                original = self._get_original_location(selected)
                self.start_var.set(original or selected)
                self._hide_search_list('start')
        elif entry_type == 'end' and self.end_listbox:
            selection = self.end_listbox.curselection()
            if selection:
                selected = self.end_listbox.get(selection[0])
                # Prefer canonical mapped name, but fall back to selected text
                original = self._get_original_location(selected)
                self.end_var.set(original or selected)
                self._hide_search_list('end')
                
    def _hide_search_list(self, entry_type):
        """Hide the search list when entry loses focus."""
        if entry_type == 'start' and hasattr(self, 'start_list_window'):
            try:
                self.start_list_window.destroy()
            except:
                pass
            self.start_listbox = None
            self.start_list_visible = False
        elif entry_type == 'end' and hasattr(self, 'end_list_window'):
            try:
                self.end_list_window.destroy()
            except:
                pass
            self.end_listbox = None
            self.end_list_visible = False
            
    def find_path(self):
        """Find path using selected algorithm."""
        # Get start location (allow any Addis Ababa place name or coordinates)
        start_input = self.start_var.get().strip()
        if not start_input:
            messagebox.showwarning("Input Error", "Please enter a start location.")
            return
        start = start_input

        # Get destination location
        end_input = self.end_var.get().strip()
        if not end_input:
            messagebox.showwarning("Input Error", "Please enter a destination.")
            return
        end = end_input
            
        algorithm = self.current_algorithm.get()
        
        # Update the combo boxes with the original names
        self.start_var.set(start)
        self.end_var.set(end)
        
        if start == end:
            # Handle same location case
            if self._validate_location(start):
                self._display_same_location_result(start, algorithm)
            else:
                # Show suggestions for the invalid location
                self._display_location_error(start, is_start=True)
            return
            
        # Clear previous output
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Finding path from {start} to {end} using {algorithm}...\n\n", "info")
        
        # Validate locations before running algorithms
        start_valid = self._validate_location(start)
        end_valid = self._validate_location(end)
        
        if not start_valid and not end_valid:
            # Both locations are invalid, show suggestions for both
            self._display_location_error(start, is_start=True)
            self._display_location_error(end, is_start=False)
            return
        elif not start_valid:
            # Only start location is invalid
            self._display_location_error(start, is_start=True)
            return
        elif not end_valid:
            # Only end location is invalid
            self._display_location_error(end, is_start=False)
            return
        
        # Disable button during processing
        self.find_button.config(state="disabled")
        
        # Run pathfinding in separate thread to avoid GUI freezing
        threading.Thread(target=self._run_pathfinding, args=(start, end, algorithm), daemon=True).start()
        
    def _run_pathfinding(self, start, end, algorithm):
        """Run pathfinding in separate thread with 1-minute time constraint."""
        try:
            # Fixed 1-minute time constraint (60 seconds)
            max_time_seconds = 60.0
            
            # Run the selected algorithm with 1-minute time constraint
            if algorithm == "DFS":
                # Run DFS with 1-minute time constraint
                result = self.dfs_controller.find_paths_with_constraints(start, end, max_time=max_time_seconds)
                self.last_result = result
                self._display_dfs_result(result, start, end)
            elif algorithm == "A*":
                # Run A* with 1-minute time constraint
                result = self.astar_controller.find_optimal_paths(start, end, algorithm.lower(), max_time=max_time_seconds)
                self.last_result = result
                self._display_astar_result(result, start, end)
            else:
                # Run BFS with 1-minute time constraint
                result = self.bfs_controller.find_optimal_paths(start, end, algorithm.lower(), max_time=max_time_seconds)
                self.last_result = result
                self._display_bfs_result(result, start, end, algorithm)
                
        except Exception as e:
            self.root.after(0, lambda: self._display_error(str(e)))
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.find_button.config(state="normal"))
            
    def _display_bfs_result(self, result, start, end, algorithm):
        """Display BFS/A* result."""
        self.root.after(0, lambda: self.output_text.insert(tk.END, f"=== {algorithm} RESULTS ===\n\n", "header"))
        
        if result["success"]:
            paths = result["paths"]
            if paths:
                # Display path information
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Found {len(paths)} optimal paths\n", "success"))
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Primary path: {len(paths[0])-1} steps\n", "info"))
                
                if len(paths) > 1:
                    self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ {len(paths)-1} alternative paths\n", "info"))
                
                # Display route
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"\nRoute: {result.get('start_node', 'Unknown')} to {result.get('goal_node', 'Unknown')}\n"))
                
                # Visualize paths
                self.root.after(0, self._visualize_paths, result)
                
            else:
                self.root.after(0, lambda: self.output_text.insert(tk.END, "No paths found\n", "error"))
        else:
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"✗ {result.get('message', 'Unknown error')}\n", "error"))
            
    def _display_dfs_result(self, result, start, end):
        """Display Classic DFS result."""
        self.root.after(0, lambda: self.output_text.insert(tk.END, "=== CLASSIC DFS RESULTS ===\n\n", "header"))
        
        if result["success"]:
            paths = result["paths"]
            if paths:
                # Display DFS-specific information
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Found {len(paths)} paths\n", "success"))
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Nodes explored: {len(result.get('visited_nodes', [])):,}\n", "info"))
                
                # Find shortest path
                shortest_idx = min(range(len(paths)), key=lambda i: len(paths[i]))
                shortest_length = len(paths[shortest_idx]) - 1
                
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Shortest path: {shortest_length} steps (Path {shortest_idx + 1})\n", "info"))
                
                # Display all path details
                self.root.after(0, lambda: self.output_text.insert(tk.END, "\nPATH DETAILS:\n", "header"))
                for i, path in enumerate(paths):
                    path_length = len(path) - 1
                    if i == shortest_idx:
                        self.root.after(0, lambda i=i, path_length=path_length: 
                                       self.output_text.insert(tk.END, f"PRIMARY: {path_length} steps\n", "success"))
                    else:
                        self.root.after(0, lambda i=i, path_length=path_length: 
                                       self.output_text.insert(tk.END, f"ALT {i}: {path_length} steps\n"))
                
                # Visualize paths
                self.root.after(0, self._visualize_paths, result)
                
            else:
                self.root.after(0, lambda: self.output_text.insert(tk.END, "No paths found\n", "error"))
        else:
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"✗ {result.get('message', 'Unknown error')}\n", "error"))
            
    def _display_astar_result(self, result, start, end):
        """Display A* result."""
        self.root.after(0, lambda: self.output_text.insert(tk.END, "=== A* RESULTS ===\n\n", "header"))
        
        if result["success"]:
            paths = result["paths"]
            if paths:
                # Display A*-specific information
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Found {len(paths)} optimal paths\n", "success"))
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Nodes explored: {len(result.get('visited_nodes', [])):,}\n", "info"))
                
                # Display heuristic weight if available
                heuristic_weight = result.get('heuristic_weight', 1.0)
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Heuristic weight: {heuristic_weight}\n", "info"))
                
                # Find shortest path
                shortest_idx = min(range(len(paths)), key=lambda i: len(paths[i]))
                shortest_length = len(paths[shortest_idx]) - 1
                
                self.root.after(0, lambda: self.output_text.insert(tk.END, f"✓ Shortest path: {shortest_length} steps (Path {shortest_idx + 1})\n", "info"))
                
                # Display all path details
                self.root.after(0, lambda: self.output_text.insert(tk.END, "\nPATH DETAILS:\n", "header"))
                for i, path in enumerate(paths):
                    path_length = len(path) - 1
                    if i == shortest_idx:
                        self.root.after(0, lambda i=i, path_length=path_length: 
                                       self.output_text.insert(tk.END, f"PRIMARY: {path_length} steps\n", "success"))
                    else:
                        self.root.after(0, lambda i=i, path_length=path_length: 
                                       self.output_text.insert(tk.END, f"ALT {i}: {path_length} steps\n"))
                
                # Visualize paths
                self.root.after(0, self._visualize_paths, result)
                
            else:
                self.root.after(0, lambda: self.output_text.insert(tk.END, "No paths found\n", "error"))
        else:
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"✗ {result.get('message', 'Unknown error')}\n", "error"))
            
    def _visualize_paths(self, result):
        """Visualize paths on the map using original terminal visualization style."""
        try:
            # Store current zoom level
            current_xlim = self.ax.get_xlim()
            current_ylim = self.ax.get_ylim()
            
            # Clear previous plot
            self.ax.clear()
            
            # Get graph and visualization settings
            graph = self.bfs_controller.domain_adapter.graph_model.graph
            from config.settings import VISUALIZATION_COLORS, EXPLORED_LINE_WIDTH, EXPLORED_ALPHA, PRIMARY_LINE_WIDTH, ALTERNATIVE_LINE_WIDTH
            
            # Plot base graph (lightgray edges)
            ox.plot_graph(graph, ax=self.ax, show=False, close=False, node_size=0, 
                         edge_linewidth=0.3, edge_color=VISUALIZATION_COLORS["base_edges"])
            
            # Add real map tiles behind the graph (same as initial map)
            try:
                import contextily as ctx
                ctx.add_basemap(
                    self.ax,
                    crs="EPSG:4326",  # graph is in lat/lon
                    source=ctx.providers.OpenStreetMap.Mapnik,
                )
            except Exception as tile_err:
                print(f"Warning: could not load basemap tiles: {tile_err}")
                # Continue with graph only if tiles fail
            
            # Plot explored nodes (blue) - if available in result
            visited_nodes = result.get("visited_nodes", set())
            if visited_nodes:
                self._plot_explored_area_gui(visited_nodes, graph, EXPLORED_LINE_WIDTH, EXPLORED_ALPHA)
            
            # Plot paths
            paths = result["paths"]
            if paths:
                # Plot alternative paths first (so primary is on top)
                colors = VISUALIZATION_COLORS["alternatives"]
                for i, path in enumerate(paths[1:], 1):  # Skip primary (index 0)
                    if i - 1 < len(colors) and len(path) > 1:
                        self._draw_path_gui(path, graph, colors[i - 1], ALTERNATIVE_LINE_WIDTH)
                
                # Plot primary path (red) on top
                primary_path = paths[0]
                if len(primary_path) > 1:
                    self._draw_path_gui(primary_path, graph, VISUALIZATION_COLORS["primary"], PRIMARY_LINE_WIDTH)
                    
                    # Add start and end markers
                    start_node, end_node = primary_path[0], primary_path[-1]
                    if graph.has_node(start_node) and graph.has_node(end_node):
                        start_y, start_x = graph.nodes[start_node]['y'], graph.nodes[start_node]['x']
                        end_y, end_x = graph.nodes[end_node]['y'], graph.nodes[end_node]['x']
                        
                        self.ax.plot(start_x, start_y, 'go', markersize=10, label='Start')
                        self.ax.plot(end_x, end_y, 'ro', markersize=10, label='End')
            
            # Add title
            algorithm = "BFS" if "BFS" in str(result) else "DFS"
            self.ax.set_title(f"Path Finding - {algorithm} Algorithm", fontsize=14, fontweight='bold')
            
            # Add legend with proper colors
            self._add_legend_gui(paths, VISUALIZATION_COLORS, visited_nodes)
            
            # Restore zoom level
            self.ax.set_xlim(current_xlim)
            self.ax.set_ylim(current_ylim)
            
            # Refresh canvas
            self.canvas.draw()
            
        except Exception as e:
            print(f"Visualization error: {e}")
            # Show error on plot
            self.ax.clear()
            self.ax.text(0.5, 0.5, f"Visualization Error\n{str(e)}\n\nPath finding results\nare shown in the\noutput panel", 
                        ha='center', va='center', transform=self.ax.transAxes, fontsize=12)
            algorithm = "BFS" if "BFS" in str(result) else "DFS"
            self.ax.set_title(f"Path Finding - {algorithm} Algorithm", fontsize=14, fontweight='bold')
            self.canvas.draw()

    def open_interactive_map(self):
        """
        Open an interactive Folium/Leaflet map in the browser.

        This does NOT rely on osmnx.plot_graph_folium, so it works with your
        current OSMnx version. It uses Folium directly, drawing the primary
        path (if available) over real OSM tiles.
        """
        try:
            graph = self.bfs_controller.domain_adapter.graph_model.graph

            # If we have a path result, prefer to center and zoom on that route
            coords = []
            if self.last_result and self.last_result.get("success") and self.last_result.get("paths"):
                route_nodes = self.last_result["paths"][0]
                if len(route_nodes) > 1:
                    for node in route_nodes:
                        if node in graph.nodes:
                            ndata = graph.nodes[node]
                            # graph uses y=lat, x=lon
                            coords.append((ndata["y"], ndata["x"]))

            if coords:
                # Center on route centroid
                avg_lat = sum(c[0] for c in coords) / len(coords)
                avg_lng = sum(c[1] for c in coords) / len(coords)
                fmap = folium.Map(location=[avg_lat, avg_lng], zoom_start=15, tiles="OpenStreetMap")

                folium.PolyLine(
                    coords,
                    color="red",
                    weight=5,
                    opacity=0.8,
                ).add_to(fmap)

                # Mark start and end
                folium.Marker(coords[0], popup="Start", icon=folium.Icon(color="green")).add_to(fmap)
                folium.Marker(coords[-1], popup="End", icon=folium.Icon(color="red")).add_to(fmap)

                # Fit map bounds tightly to the route
                fmap.fit_bounds(coords)
            else:
                # No route yet: center on the graph itself
                if len(graph.nodes) == 0:
                    messagebox.showwarning("Interactive Map", "Graph is empty, cannot build map.")
                    return

                first_node = next(iter(graph.nodes))
                center_lat = graph.nodes[first_node].get("y")
                center_lng = graph.nodes[first_node].get("x")

                if center_lat is None or center_lng is None:
                    messagebox.showwarning("Interactive Map", "Graph nodes have no coordinates.")
                    return

                fmap = folium.Map(location=[center_lat, center_lng], zoom_start=13, tiles="OpenStreetMap")

            # Save to a temporary HTML file with timestamp to avoid caching and open in default browser
            import time
            timestamp = int(time.time())
            temp_filename = f"pathfinding_map_{timestamp}.html"
            
            with tempfile.NamedTemporaryFile(suffix=temp_filename, delete=False) as tmp:
                fmap.save(tmp.name)
                # Force browser to open fresh content by adding cache-busting parameter
                webbrowser.open(f"file://{tmp.name}?t={timestamp}")

        except Exception as e:
            messagebox.showerror("Web Map Error", f"Could not open web map:\n{e}")
    
    def _plot_explored_area_gui(self, visited_nodes, graph, line_width, alpha):
        """Plot explored area in blue - matches original terminal visualization."""
        visited_nodes_list = list(visited_nodes)
        if visited_nodes_list:
            # Create subgraph of visited nodes
            visited_subgraph = graph.subgraph(visited_nodes_list)
            
            # Plot edges in explored area
            for u, v in visited_subgraph.edges():
                if graph.has_node(u) and graph.has_node(v):
                    u_data = graph.nodes[u]
                    v_data = graph.nodes[v]
                    x_coords = [u_data['x'], v_data['x']]
                    y_coords = [u_data['y'], v_data['y']]
                    self.ax.plot(x_coords, y_coords, 'b-', 
                               linewidth=line_width, 
                               alpha=alpha)
    
    def _draw_path_gui(self, path, graph, color, linewidth):
        """Draw a single path on the map - matches original visualization."""
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            if graph.has_node(u) and graph.has_node(v):
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]
                x_coords = [u_data['x'], v_data['x']]
                y_coords = [u_data['y'], v_data['y']]
                self.ax.plot(x_coords, y_coords, color=color, linewidth=linewidth, alpha=0.9)
    
    def _add_legend_gui(self, paths, colors, visited_nodes):
        """Add legend matching original terminal visualization."""
        legend_handles = []
        legend_labels = []
        
        # Add explored nodes if present
        if visited_nodes:
            from matplotlib.lines import Line2D
            explored_line = Line2D([0], [0], color='blue', linewidth=0.8, alpha=0.25, label='Explored Area')
            legend_handles.append(explored_line)
            legend_labels.append('Explored Area')
        
        # Add paths
        if paths and len(paths) > 0:
            # Primary path (red)
            from matplotlib.lines import Line2D
            primary_line = Line2D([0], [0], color=colors["primary"], linewidth=4, label='Primary Path')
            legend_handles.append(primary_line)
            legend_labels.append('Primary Path')
            
            # Alternative paths
            for i, path in enumerate(paths[1:], 1):
                if i - 1 < len(colors["alternatives"]):
                    alt_color = colors["alternatives"][i - 1]
                    alt_line = Line2D([0], [0], color=alt_color, linewidth=3, label=f'Alternative {i}')
                    legend_handles.append(alt_line)
                    legend_labels.append(f'Alternative {i}')
        
        # Add start/end markers if paths exist
        if paths and len(paths) > 0:
            from matplotlib.lines import Line2D
            start_marker = Line2D([0], [0], marker='o', color='w', markerfacecolor='g', 
                                markersize=8, label='Start')
            end_marker = Line2D([0], [0], marker='o', color='w', markerfacecolor='r', 
                              markersize=8, label='End')
            legend_handles.append(start_marker)
            legend_labels.append('Start')
            legend_handles.append(end_marker)
            legend_labels.append('End')
        
        if legend_handles:
            self.ax.legend(handles=legend_handles, labels=legend_labels, loc='upper right')
            
    def _validate_location(self, location_input: str) -> bool:
        """Check if a location exists in the available locations."""
        if not location_input:
            return False
        
        location_lower = location_input.lower()
        
        # Check exact matches
        for location in self.locations:
            if location.lower() == location_lower:
                return True
        
        # Check if it's in the location mapping
        if location_lower in self.location_mapping:
            return True
        
        return False
    
    def _get_location_suggestions(self, user_input: str, max_suggestions: int = 4) -> List[str]:
        """Get location suggestions based on user input."""
        if not user_input or len(user_input) < 2:
            return []
        
        user_input_lower = user_input.lower()
        suggestions = []
        
        # Priority 1: Locations starting with the first 2-3 letters
        for location in self.locations:
            location_lower = location.lower()
            if location_lower.startswith(user_input_lower):
                suggestions.append(location)
                if len(suggestions) >= max_suggestions:
                    return suggestions
        
        # Priority 2: Locations containing the input as a word
        for location in self.locations:
            location_lower = location.lower()
            words = location_lower.split()
            for word in words:
                if word.startswith(user_input_lower) and location not in suggestions:
                    suggestions.append(location)
                    if len(suggestions) >= max_suggestions:
                        return suggestions
        
        # Priority 3: Locations containing the input anywhere
        for location in self.locations:
            location_lower = location.lower()
            if user_input_lower in location_lower and location not in suggestions:
                suggestions.append(location)
                if len(suggestions) >= max_suggestions:
                    return suggestions
        
        # Priority 4: Fuzzy matching for similar sounding names
        if len(suggestions) < max_suggestions:
            from difflib import get_close_matches
            fuzzy_matches = get_close_matches(user_input_lower, [loc.lower() for loc in self.locations], 
                                            n=max_suggestions - len(suggestions), cutoff=0.4)
            
            # Convert back to original case
            for match in fuzzy_matches:
                for location in self.locations:
                    if location.lower() == match and location not in suggestions:
                        suggestions.append(location)
                        break
        
        return suggestions[:max_suggestions]
    
    def _display_same_location_result(self, location: str, algorithm: str):
        """Display result for same start and end location."""
        # Clear previous output
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Finding path from {location} to {location} using {algorithm}...\n\n", "info")
        
        # Display the result
        self.output_text.insert(tk.END, f"=== {algorithm} RESULTS ===\n\n", "header")
        self.output_text.insert(tk.END, f"✓ Path found: 0 steps (same location)\n", "success")
        self.output_text.insert(tk.END, f"✓ Distance: 0 meters\n", "info")
        self.output_text.insert(tk.END, f"✓ Valid path of zero distance\n", "success")
        self.output_text.insert(tk.END, f"\nRoute: {location} (start = destination)\n", "info")
        
        # Visualize the single point on map
        self._visualize_same_location(location, algorithm)
    
    def _visualize_same_location(self, location: str, algorithm: str):
        """Visualize a single location on the map."""
        try:
            print(f"Debug: Starting visualization for location: {location}")
            
            # Store current zoom level
            current_xlim = self.ax.get_xlim()
            current_ylim = self.ax.get_ylim()
            print(f"Debug: Current limits - xlim: {current_xlim}, ylim: {current_ylim}")
            
            # Clear previous plot
            self.ax.clear()
            
            # Get graph and visualization settings (same as working method)
            try:
                graph = self.bfs_controller.domain_adapter.graph_model.graph
                print(f"Debug: Graph loaded successfully, nodes: {len(graph.nodes())}")
            except Exception as graph_error:
                print(f"Debug: Error loading graph: {graph_error}")
                # Fallback: show simple map without graph
                self._show_fallback_visualization(location, algorithm)
                return
            
            from config.settings import VISUALIZATION_COLORS, EXPLORED_LINE_WIDTH, EXPLORED_ALPHA, PRIMARY_LINE_WIDTH, ALTERNATIVE_LINE_WIDTH
            
            # Plot base graph (lightgray edges) - same as working method
            try:
                ox.plot_graph(graph, ax=self.ax, show=False, close=False, node_size=0, 
                             edge_linewidth=0.3, edge_color=VISUALIZATION_COLORS["base_edges"])
                print("Debug: Base graph plotted successfully")
                
                # Add real map tiles behind the graph (same as initial map)
                try:
                    import contextily as ctx
                    ctx.add_basemap(
                        self.ax,
                        crs="EPSG:4326",  # graph is in lat/lon
                        source=ctx.providers.OpenStreetMap.Mapnik,
                    )
                    print("Debug: Basemap tiles added successfully")
                except Exception as tile_err:
                    print(f"Debug: Could not load basemap tiles: {tile_err}")
                    # Continue with graph only if tiles fail
                    
            except Exception as plot_error:
                print(f"Debug: Error plotting base graph: {plot_error}")
                self._show_fallback_visualization(location, algorithm)
                return
            
            # Try to get the node for this location
            node_found = False
            try:
                node = self.bfs_controller.domain_adapter.get_nearest_node(location)
                print(f"Debug: Found nearest node: {node}")
                
                if graph.has_node(node):
                    print(f"Debug: Node {node} exists in graph")
                    # Get coordinates
                    y, x = graph.nodes[node]['y'], graph.nodes[node]['x']
                    print(f"Debug: Node coordinates - x: {x}, y: {y}")
                    
                    # Plot a single marker (both start and end at same point)
                    self.ax.plot(x, y, 'go', markersize=15, label='Start = End', 
                               markeredgecolor='darkgreen', markeredgewidth=2)
                    print("Debug: Marker plotted successfully")
                    
                    # Add location label
                    self.ax.annotate(location, (x, y), xytext=(10, 10), 
                                   textcoords='offset points', fontsize=10,
                                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
                    print("Debug: Annotation added successfully")
                    node_found = True
                else:
                    print(f"Debug: Node {node} not found in graph")
            except Exception as node_error:
                print(f"Debug: Error getting node: {node_error}")
            
            if not node_found:
                # Node not found in graph
                print("Debug: Using fallback text display")
                self.ax.text(0.5, 0.5, f"Location: {location}\n(Node not found in graph)\n\nPath found: 0 steps", 
                            ha='center', va='center', transform=self.ax.transAxes, 
                            fontsize=12, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
            
            # Add title
            self.ax.set_title(f"Path Finding - {algorithm} Algorithm (Same Location)", fontsize=14, fontweight='bold')
            
            # Add legend if we have a valid node
            if node_found:
                try:
                    from matplotlib.lines import Line2D
                    marker_line = Line2D([0], [0], marker='o', color='w', markerfacecolor='g', 
                                        markeredgecolor='darkgreen', markersize=10, label='Start = End')
                    self.ax.legend(handles=[marker_line], loc='upper right')
                    print("Debug: Legend added successfully")
                except Exception as legend_error:
                    print(f"Debug: Error adding legend: {legend_error}")
            
            # Restore zoom level
            self.ax.set_xlim(current_xlim)
            self.ax.set_ylim(current_ylim)
            
            # Refresh canvas
            self.canvas.draw()
            print("Debug: Canvas refreshed successfully")
            
        except Exception as e:
            print(f"Debug: Major visualization error: {e}")
            self._show_fallback_visualization(location, algorithm)
    
    def _show_fallback_visualization(self, location: str, algorithm: str):
        """Show a fallback visualization when the main one fails."""
        try:
            print(f"Debug: Using fallback visualization for {location}")
            self.ax.clear()
            self.ax.text(0.5, 0.5, f"Location: {location}\n\nPath found: 0 steps\n\nSame location", 
                        ha='center', va='center', transform=self.ax.transAxes, fontsize=12,
                        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
            self.ax.set_title(f"Path Finding - {algorithm} Algorithm (Same Location)", fontsize=14, fontweight='bold')
            self.canvas.draw()
            print("Debug: Fallback visualization completed")
        except Exception as fallback_error:
            print(f"Debug: Fallback visualization failed: {fallback_error}")
    
    def _display_location_error(self, location_input: str, is_start: bool = True):
        """Display location error with helpful suggestions."""
        location_type = "start" if is_start else "destination"
        suggestions = self._get_location_suggestions(location_input)
        
        self.output_text.insert(tk.END, f"✗ Location '{location_input}' not found\n", "error")
        
        if suggestions:
            self.output_text.insert(tk.END, f"Did you mean one of these {location_type} locations?\n", "info")
            for i, suggestion in enumerate(suggestions, 1):
                self.output_text.insert(tk.END, f"  {i}. {suggestion}\n", "success")
        else:
            self.output_text.insert(tk.END, f"No similar locations found for '{location_input}'\n", "info")
            self.output_text.insert(tk.END, "Try typing a more specific location name\n", "info")
        
        self.output_text.insert(tk.END, "\n", "normal")
    
    def _display_error(self, error_msg):
        """Display error message."""
        self.output_text.insert(tk.END, f"✗ Error: {error_msg}\n", "error")
        
    def clear_all(self):
        """Clear all outputs and reset map."""
        # Clear output
        self.output_text.delete(1.0, tk.END)
        
        # Clear inputs
        self.start_var.set("")
        self.end_var.set("")
        
        # Reset map
        self.load_initial_map()


def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = PathFinderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
