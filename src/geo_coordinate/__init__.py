"""
Geographic coordinate module built on the unit-aware types of `units`.

This module provides array-based latitude, longitude and signed altitude,
and great-circle distances between coordinates.
"""

from .altitude import Altitude
from .coordinate import GeoCoordinate

__all__ = [
    "Altitude",
    "GeoCoordinate",
]
