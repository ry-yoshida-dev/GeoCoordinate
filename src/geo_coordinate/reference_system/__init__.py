"""
Coordinate reference systems: geographic datums and the projections onto planes.
"""

from .coordinate_reference_system import CoordinateReferenceSystem
from .geodetic_crs import GeodeticCrs
from .japan_plane_rectangular_zone import JapanPlaneRectangularZone
from .web_mercator import WebMercator

__all__ = [
    "CoordinateReferenceSystem",
    "GeodeticCrs",
    "JapanPlaneRectangularZone",
    "WebMercator",
]
