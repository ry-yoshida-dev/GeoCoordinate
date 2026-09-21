"""
Geographic coordinate module built on the unit-aware types of `units`.

This module provides array-based latitude, longitude and signed altitude,
hemisphere abbreviations, and great-circle distances between coordinates.
"""

from .altitude import Altitude
from .coordinate import GeoCoordinate
from .hemisphere import LatitudeHemisphere, LongitudeHemisphere

__all__ = [
    "Altitude",
    "GeoCoordinate",
    "LatitudeHemisphere",
    "LongitudeHemisphere",
]
