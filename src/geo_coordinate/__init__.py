"""
Geographic coordinate module built on the unit-aware types of `units`.

This module provides single coordinates and batches of latitude, longitude
and signed altitude, hemisphere abbreviations, sexagesimal text notation,
great-circle distances, bearings from true or magnetic north, altitude
profiles along paths, and the coordinate reference systems that coordinates
are measured in or projected to.
"""

from .altitude import Altitude
from .base import GeoCoordinateBase
from .bearing import Bearing, NorthReference
from .coordinate import GeoCoordinate
from .coordinates import GeoCoordinates
from .hemisphere import LatitudeHemisphere, LongitudeHemisphere
from .reference_system import (
    CoordinateReferenceSystem,
    GeodeticCrs,
    JapanPlaneRectangularZone,
    WebMercator,
)
from .sexagesimal import SexagesimalNotation, SexagesimalText

__all__ = [
    "Altitude",
    "Bearing",
    "CoordinateReferenceSystem",
    "GeoCoordinate",
    "GeoCoordinateBase",
    "GeoCoordinates",
    "GeodeticCrs",
    "JapanPlaneRectangularZone",
    "LatitudeHemisphere",
    "LongitudeHemisphere",
    "NorthReference",
    "SexagesimalNotation",
    "SexagesimalText",
    "WebMercator",
]
