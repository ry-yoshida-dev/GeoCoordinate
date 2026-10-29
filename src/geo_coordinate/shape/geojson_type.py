from __future__ import annotations

from enum import Enum


class GeoJsonType(Enum):
    """
    GeoJSON geometry types (RFC 7946) read and written by `GeoJsonGeometry`.

    Each value is the `type` member of the geometry object.

    Attributes
    ----------
    LINE_STRING
        A `GeoLineString`.
    POLYGON
        A `GeoPolygon`.
    MULTI_POLYGON
        A `GeoMultiPolygon`.
    """

    LINE_STRING = "LineString"
    POLYGON = "Polygon"
    MULTI_POLYGON = "MultiPolygon"
