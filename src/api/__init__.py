"""
api package - Exposes the Modrinth API client globally.
"""

from .client import ModrinthAPIConfig  # The singleton instance

api = ModrinthAPIConfig()

__all__ = ["api"]