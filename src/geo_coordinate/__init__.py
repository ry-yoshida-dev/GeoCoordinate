"""
Geographic coordinate module built on the unit-aware types of `units`.

This module provides single coordinates and batches of latitude, longitude
and signed altitude, hemisphere abbreviations, sexagesimal text notation,
great-circle distances and bearings, and altitude profiles along paths.
"""

from .altitude import Altitude
from .base import GeoCoordinateBase
from .coordinate import GeoCoordinate
from .coordinates import GeoCoordinates
from .hemisphere import LatitudeHemisphere, LongitudeHemisphere
from .sexagesimal import SexagesimalNotation, SexagesimalText

__all__ = [
    "Altitude",
    "GeoCoordinate",
    "GeoCoordinateBase",
    "GeoCoordinates",
    "LatitudeHemisphere",
    "LongitudeHemisphere",
    "SexagesimalNotation",
    "SexagesimalText",
]
