"""
Geographic coordinate module built on the unit-aware types of `units`.

This module provides single coordinates and batches of latitude, longitude
and signed altitude, hemisphere abbreviations, sexagesimal text notation,
great-circle and ellipsoidal distances, bearings from true or magnetic north,
altitude profiles along paths, the coordinate reference systems
that coordinates are measured in, transformed between or projected to,
Earth-centred and local Cartesian frames,
and the regional meshes of JIS X 0410 that Japanese statistics are tabulated on.
"""

from .altitude import Altitude
from .base import GeoCoordinateBase
from .bearing import Bearing, NorthReference
from .cartesian import (
    EarthCenteredCoordinates,
    EastNorthUp,
    GeocentricConversion,
    GeodeticPosition,
    LocalTangentPlane,
)
from .coordinate import GeoCoordinate
from .coordinates import GeoCoordinates
from .geodesic import Geodesic, GeodesicInverse
from .hemisphere import LatitudeHemisphere, LongitudeHemisphere
from .reference_system import (
    CoordinateReferenceSystem,
    DatumTransformation,
    Ellipsoid,
    GeodeticCrs,
    Geoid,
    GeoidModel,
    JapanPlaneRectangularZone,
    PlaneCoordinates,
    PlaneProjection,
    UtmZone,
    WebMercator,
    WebMercatorProjection,
)
from .regional_mesh import RegionalMeshBounds, RegionalMeshCode, RegionalMeshLevel
from .sexagesimal import SexagesimalNotation, SexagesimalText

__all__ = [
    "Altitude",
    "Bearing",
    "CoordinateReferenceSystem",
    "DatumTransformation",
    "EarthCenteredCoordinates",
    "EastNorthUp",
    "Ellipsoid",
    "GeoCoordinate",
    "GeoCoordinateBase",
    "GeoCoordinates",
    "GeocentricConversion",
    "Geodesic",
    "GeodesicInverse",
    "GeodeticCrs",
    "GeodeticPosition",
    "Geoid",
    "GeoidModel",
    "JapanPlaneRectangularZone",
    "LatitudeHemisphere",
    "LocalTangentPlane",
    "LongitudeHemisphere",
    "NorthReference",
    "PlaneCoordinates",
    "PlaneProjection",
    "RegionalMeshBounds",
    "RegionalMeshCode",
    "RegionalMeshLevel",
    "SexagesimalNotation",
    "SexagesimalText",
    "UtmZone",
    "WebMercator",
    "WebMercatorProjection",
]
