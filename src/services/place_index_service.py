"""
Service for building and querying a place-name index for Addis Ababa.

Uses OpenStreetMap data via OSMnx to fetch essentially all named places
within the configured city boundary and caches them locally for fast
autocomplete / lookup.
"""

from __future__ import annotations

import json
from difflib import get_close_matches
from pathlib import Path
from typing import List

import osmnx as ox

from config.settings import CACHE_DIR, DEFAULT_CITY


class PlaceIndexService:
    """Manages an index of named places in Addis Ababa for suggestions."""

    def __init__(self, city: str = DEFAULT_CITY) -> None:
        self.city = city
        self.cache_file = Path(CACHE_DIR) / "addis_place_index.json"
        self._names: list[str] = []
        self._ensure_cache_dir()
        self._load_or_build_index()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get_all_names(self) -> List[str]:
        """Return all indexed place names."""
        return list(self._names)

    def search(self, query: str, limit: int = 10) -> List[str]:
        """
        Return up to `limit` matching place names for the given query.

        - First uses simple "contains" matching (case-insensitive).
        - If nothing is found, falls back to fuzzy matching.
        """
        q = query.strip().lower()
        if not q:
            return []

        # Simple substring search
        contains_matches = [name for name in self._names if q in name.lower()]

        if contains_matches:
            return contains_matches[:limit]

        # Fuzzy fallback
        fuzzy = get_close_matches(q, self._names, n=limit, cutoff=0.6)
        return fuzzy

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_cache_dir(self) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _load_or_build_index(self) -> None:
        if self.cache_file.exists():
            try:
                with self.cache_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                # Ensure it's a list of strings
                self._names = [str(name) for name in data]
                if self._names:
                    return
            except Exception:
                # Fall back to rebuild if cache is corrupted
                pass

        self._build_index()

    def _build_index(self) -> None:
        """
        Download and index named geometries for Addis Ababa from OSM.

        This is done once (or when the cache is missing/corrupt) and then
        stored as a simple JSON array of names.
        """
        # Broad tag set to capture as many named features as possible
        tags = {
            "place": True,    # suburbs, neighbourhoods, etc.
            "amenity": True,  # schools, hospitals, cafes, etc.
            "shop": True,
            "highway": True,  # junctions, bus stops, etc.
            "landuse": True,
        }

        # osmnx >= 2 uses features_from_place instead of geometries_from_place
        gdf = ox.features_from_place(self.city, tags)

        if "name" in gdf.columns:
            unique_names = {
                str(name).strip()
                for name in gdf["name"].dropna().unique()
                if str(name).strip()
            }
        else:
            unique_names = set()

        # Store sorted for nicer UX
        self._names = sorted(unique_names)

        try:
            with self.cache_file.open("w", encoding="utf-8") as f:
                json.dump(self._names, f, ensure_ascii=False, indent=2)
        except Exception:
            # If caching fails, we still keep _names in memory
            pass


