"""Repository layer for Talon data access."""

from talon.repositories.vulnerability_repository import VulnerabilityRepository
from talon.repositories.scan_repository import ScanRepository
from talon.repositories.base import BaseRepository

__all__ = [
    "BaseRepository",
    "VulnerabilityRepository",
    "ScanRepository",
]
