"""
api/client.py - Modrinth API v2 URL builder using modrinth_api.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus


class ModrinthAPIConfig:
    """Singleton class that loads modrinth_api.json and builds URLs."""
    
    _instance: Optional["ModrinthAPIConfig"] = None

    def __new__(cls) -> "ModrinthAPIConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str | Path = "modrinth_api.json"):
        if self._initialized:
            return
        
        self.config_path = Path(config_path)
        self.base_url: str = ""
        self.endpoints: Dict[str, Any] = {}
        self._load_config()
        self._initialized = True

    def _load_config(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Modrinth API config not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.base_url = data.get("BASE_URL", "").rstrip("/")
        if not self.base_url:
            raise ValueError("BASE_URL missing in modrinth_api.json")

        self.endpoints = data.get("ENDPOINTS", {})
        if not isinstance(self.endpoints, dict):
            raise ValueError("ENDPOINTS section is invalid")

    def build_url(self, template: str, **kwargs: str) -> str:
        """Format a template string with kwargs and prepend base URL."""
        try:
            path = template.format(**kwargs)
            return f"{self.base_url}{path}"
        except KeyError as e:
            raise ValueError(f"Missing URL parameter: {e}")

    # === Endpoint URL Builders ===

    def search(
        self,
        query: Optional[str] = None,
        facets: Optional[List[List[str]] | str] = None,
        categories: Optional[List[str]] = None,
        loaders: Optional[List[str]] = None,
        game_versions: Optional[List[str]] = None,
        license_: Optional[str] = None,
        project_type: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = 10,
        index: Optional[str] = "relevance",  # relevance, downloads, updated, newest
    ) -> str:
        """
        Build the Modrinth search URL with query parameters.

        Docs: https://docs.modrinth.com/api-spec#endpoints-search

        Facets format: [[inner AND], [inner AND]] = outer OR
        Example: [["categories:performance"], ["project_type:mod"]]

        Args:
            query: Search term (e.g., "sodium")
            facets: Advanced filters as list of lists or JSON string
            categories: Filter by categories (e.g., ["performance"])
            loaders: Filter by loaders (e.g., ["fabric", "quilt"])
            game_versions: Filter by Minecraft versions (e.g., ["1.21.1"])
            license_: Filter by license (e.g., "MIT")
            project_type: "mod", "resourcepack", "shader", "modpack", "datapack"
            offset: Pagination offset
            limit: Results per page (max 100)
            index: Sort by "relevance", "downloads", "updated", "newest"

        Returns:
            Full search URL with query parameters
        """
        base = self.build_url(self.endpoints["search"])
        
        params = []
        
        if query:
            params.append(f"query={quote_plus(query)}")
        
        # Build facets array from all filter parameters
        facets_array = []
        
        if facets:
            # If facets provided directly, use them
            if isinstance(facets, str):
                params.append(f"facets={quote_plus(facets)}")
            else:
                facets_array.extend(facets)
        
        # Add convenience filters to facets
        if project_type:
            facets_array.append([f"project_type:{project_type}"])
        
        if categories:
            for cat in categories:
                facets_array.append([f"categories:{cat}"])
        
        if loaders:
            facets_array.append([f"categories:{loader}" for loader in loaders])
        
        if game_versions:
            facets_array.append([f"versions:{version}" for version in game_versions])
        
        if license_:
            facets_array.append([f"license:{license_}"])
        
        # Convert facets array to JSON string if we have any
        if facets_array and not (isinstance(facets, str)):
            import json as json_lib
            facets_str = json_lib.dumps(facets_array)
            params.append(f"facets={quote_plus(facets_str)}")
        
        if offset is not None:
            params.append(f"offset={offset}")
        
        if limit is not None:
            params.append(f"limit={min(limit, 100)}")  # Modrinth caps at 100
        
        if index:
            params.append(f"index={index}")

        query_string = "&".join(params)
        return f"{base}?{query_string}" if params else base

    def project(self, project_id: str) -> str:
        return self.build_url(self.endpoints["projects"]["project"], id=project_id)

    def project_versions(self, project_id: str) -> str:
        return self.build_url(self.endpoints["projects"]["project_versions"], id=project_id)

    def version(self, version_id: str) -> str:
        return self.build_url(self.endpoints["versions"]["version"], id=version_id)

    def version_file(self, version_id: str, filename: str) -> str:
        return self.build_url(
            self.endpoints["versions"]["download"],
            id=version_id,
            filename=filename,
        )

    def file_by_hash(self, hash_: str) -> str:
        return self.build_url(self.endpoints["versions"]["file_by_hash"], hash=hash_)

    def project_icon(self, project_id: str) -> str:
        return self.build_url(self.endpoints["projects"]["icon"], id=project_id)

    def categories(self) -> str:
        return self.build_url(self.endpoints["tags"]["categories"])

    def loaders(self) -> str:
        return self.build_url(self.endpoints["tags"]["loaders"])

    def game_versions(self) -> str:
        return self.build_url(self.endpoints["tags"]["game_versions"])

    def bulk_projects(self) -> str:
        return self.build_url(self.endpoints["bulk"]["projects"])

    def bulk_versions(self) -> str:
        return self.build_url(self.endpoints["bulk"]["versions"])