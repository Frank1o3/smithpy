from typing import Iterable, List, Set
from collections import deque

from smithpy.core.policy import ModPolicy
from smithpy.core.models import SearchResult, ProjectVersionList
from smithpy.api import ModrinthAPIConfig
from requests import get


# Import version info
try:
    from smithpy.__version__ import __version__, __author__
except ImportError:
    __version__ = "unknown"
    __author__ = "Frank1o3"

class ModResolver:
    def __init__(
        self,
        *,
        policy: ModPolicy,
        api: ModrinthAPIConfig,
        mc_version: str,
        loader: str,
    ) -> None:
        self.policy = policy
        self.api = api
        self.mc_version = mc_version
        self.loader = loader

    def resolve(self, mods: Iterable[str]) -> Set[str]:
        expanded = self.policy.apply(mods)
        resolved_ids: Set[str] = set()
        queue: deque[str] = deque()
        
        # Phase 1: Convert slugs to initial Project IDs
        for slug in expanded:
            url = self.api.search(slug, game_versions=[self.mc_version], loaders=[self.loader])
            response = get(url, headers={"User-Agent": f"{__author__}/SmithPy/{__version__}"})
            data = SearchResult.model_validate_json(response.text)
            
            if data.hits:
                for hit in data.hits:
                    if hit.slug == slug:
                        if hit.project_id not in resolved_ids:
                            resolved_ids.add(hit.project_id)
                            queue.append(hit.project_id)
                        break
            del url, response, data
        

        # Phase 2: Recursive Dependency Resolution
        while queue:
            current_id = queue.popleft()
            url = self.api.project_versions(current_id)
            print(url)
            response = get(url, headers={"User-Agent": f"{__author__}/SmithPy/{__version__}"})
            versions = ProjectVersionList.validate_json(response.text)
            
            # Find the first version that matches our MC version and Loader
            valid_v = next((v for v in versions if 
                           self.mc_version in (v.game_versions or []) and 
                           self.loader in (v.loaders or [])), None)
            
            if valid_v and valid_v.dependencies:
                for dep in valid_v.dependencies:
                    if dep.dependency_type in ["required", "optional"] and dep.project_id:
                        if dep.project_id not in resolved_ids:
                            resolved_ids.add(dep.project_id)
                            queue.append(dep.project_id)
            del valid_v, response, versions, url, current_id
        del queue, expanded
        
        return resolved_ids