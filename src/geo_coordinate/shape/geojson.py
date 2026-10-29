from __future__ import annotations

from typing import ClassVar

import numpy as np
from numpy.typing import NDArray
from units import LengthUnit

from ..altitude import Altitude
from ..coordinates import GeoCoordinates
from .geo_shape import GeoShape
from .geojson_type import GeoJsonType
from .json_value import JsonValue
from .line_string import GeoLineString
from .linear_ring import GeoLinearRing
from .multi_polygon import GeoMultiPolygon
from .polygon import GeoPolygon


class GeoJsonGeometry:
    """
    Reader and writer of GeoJSON (RFC 7946) geometry objects.

    Positions are `[longitude, latitude]` in degrees, or `[longitude, latitude, height]`
    when every position of a geometry has a height in meters, which is read into and
    written from `Altitude` as it is. RFC 7946 defines the height above the WGS 84
    ellipsoid while `Altitude` is above mean sea level, so convert heights with `Geoid`
    where the difference matters. Ring orientation is kept as given; call `oriented` on
    a polygon first to write the orientation RFC 7946 requires.

    Examples
    --------
    >>> line = GeoJsonGeometry.decode(
    ...     {"type": "LineString", "coordinates": [[139.0, 35.0], [140.0, 36.0]]}
    ... )
    >>> len(line)
    2
    >>> GeoJsonGeometry.encode(line)["type"]
    'LineString'
    """

    TWO_DIMENSIONS: ClassVar[int] = 2
    THREE_DIMENSIONS: ClassVar[int] = 3

    @classmethod
    def encode(cls, shape: GeoShape) -> dict[str, JsonValue]:
        """
        Write a shape as a GeoJSON geometry object.

        Parameters
        ----------
        shape : GeoShape
            The line or area to write.

        Returns
        -------
        dict[str, JsonValue]
            The geometry object, ready for `json.dumps`.
        """
        match shape:
            case GeoLineString():
                return cls._geometry(GeoJsonType.LINE_STRING, cls._positions(shape.vertices))
            case GeoPolygon():
                return cls._geometry(GeoJsonType.POLYGON, cls._polygon_coordinates(shape))
            case GeoMultiPolygon():
                return cls._geometry(
                    GeoJsonType.MULTI_POLYGON,
                    [cls._polygon_coordinates(polygon) for polygon in shape.polygons],
                )

    @classmethod
    def decode(cls, geometry: JsonValue) -> GeoShape:
        """
        Read a GeoJSON geometry object.

        Parameters
        ----------
        geometry : JsonValue
            The geometry object, such as the `geometry` member of a feature parsed by
            `json.loads`.

        Returns
        -------
        GeoShape
            A `GeoLineString`, `GeoPolygon` or `GeoMultiPolygon` by the `type` member.

        Raises
        ------
        ValueError
            If the object is not a geometry of a supported type, or its coordinates are
            malformed or out of range.
        """
        if not isinstance(geometry, dict):
            raise ValueError(f"a geometry must be a JSON object, given: {type(geometry)}")
        type_name: JsonValue = geometry.get("type")
        if not isinstance(type_name, str):
            raise ValueError(f"a geometry must have a string type, given: {type_name!r}")
        supported_names: list[str] = [member.value for member in GeoJsonType]
        if type_name not in supported_names:
            raise ValueError(
                f"a geometry type must be one of {supported_names}, given: {type_name!r}"
            )
        coordinates: JsonValue = geometry.get("coordinates")
        match GeoJsonType(type_name):
            case GeoJsonType.LINE_STRING:
                return GeoLineString(vertices=cls._vertices(coordinates))
            case GeoJsonType.POLYGON:
                return cls._polygon(coordinates)
            case GeoJsonType.MULTI_POLYGON:
                return GeoMultiPolygon(
                    polygons=tuple(cls._polygon(part) for part in cls._array(coordinates))
                )

    @staticmethod
    def _geometry(geojson_type: GeoJsonType, coordinates: list[JsonValue]) -> dict[str, JsonValue]:
        """
        Build a geometry object.

        Parameters
        ----------
        geojson_type : GeoJsonType
            The type of the geometry.
        coordinates : list[JsonValue]
            The nested positions.

        Returns
        -------
        dict[str, JsonValue]
            The object with its `type` and `coordinates` members.
        """
        return {"type": geojson_type.value, "coordinates": coordinates}

    @classmethod
    def _polygon_coordinates(cls, polygon: GeoPolygon) -> list[JsonValue]:
        """
        Positions of the closed rings of a polygon.

        Parameters
        ----------
        polygon : GeoPolygon
            The polygon to write.

        Returns
        -------
        list[JsonValue]
            One list of positions per ring, the outline first, each closed.
        """
        return [cls._positions(ring.closed_vertices) for ring in polygon.rings]

    @staticmethod
    def _positions(vertices: GeoCoordinates) -> list[JsonValue]:
        """
        GeoJSON positions of coordinates.

        Parameters
        ----------
        vertices : GeoCoordinates
            The coordinates to write.

        Returns
        -------
        list[JsonValue]
            One `[longitude, latitude]` or `[longitude, latitude, height]` per coordinate.
        """
        columns: list[NDArray[np.float64]] = [
            vertices.longitude.degree.astype(np.float64),
            vertices.latitude.degree.astype(np.float64),
        ]
        if vertices.altitude is not None:
            columns.append(vertices.altitude.meter.astype(np.float64))
        rows: NDArray[np.float64] = np.column_stack(columns)
        return [[float(value) for value in row] for row in rows]

    @classmethod
    def _polygon(cls, coordinates: JsonValue) -> GeoPolygon:
        """
        Read the rings of a polygon.

        Parameters
        ----------
        coordinates : JsonValue
            The list of rings, the outline first.

        Returns
        -------
        GeoPolygon
            The polygon.

        Raises
        ------
        ValueError
            If there is no ring or a ring is malformed.
        """
        rings: list[GeoLinearRing] = [
            GeoLinearRing(vertices=cls._vertices(ring)) for ring in cls._array(coordinates)
        ]
        if not rings:
            raise ValueError("a polygon needs an exterior ring")
        return GeoPolygon(exterior=rings[0], holes=tuple(rings[1:]))

    @classmethod
    def _vertices(cls, coordinates: JsonValue) -> GeoCoordinates:
        """
        Read a list of positions.

        Parameters
        ----------
        coordinates : JsonValue
            The positions, all of two or all of three numbers.

        Returns
        -------
        GeoCoordinates
            The coordinates in degrees, with altitudes in meters for three numbers.

        Raises
        ------
        ValueError
            If the positions are malformed, mix dimensions or are out of range.
        """
        positions: list[list[float]] = [
            cls._numbers(position) for position in cls._array(coordinates)
        ]
        dimensions: set[int] = {len(position) for position in positions}
        if not positions:
            raise ValueError("a geometry needs at least one position")
        if len(dimensions) != 1 or not dimensions <= {cls.TWO_DIMENSIONS, cls.THREE_DIMENSIONS}:
            raise ValueError(
                "positions must all have two or all have three numbers, "
                + f"given: {sorted(dimensions)}"
            )
        values: NDArray[np.float64] = np.array(positions, dtype=np.float64)
        altitude: Altitude | None = None
        if dimensions == {cls.THREE_DIMENSIONS}:
            altitude = Altitude(value=values[:, 2], unit=LengthUnit.M)
        return GeoCoordinates.from_degrees(
            latitude=values[:, 1], longitude=values[:, 0], altitude=altitude
        )

    @staticmethod
    def _array(value: JsonValue) -> list[JsonValue]:
        """
        Require a JSON array.

        Parameters
        ----------
        value : JsonValue
            The value to check.

        Returns
        -------
        list[JsonValue]
            The value itself.

        Raises
        ------
        ValueError
            If the value is not an array.
        """
        if not isinstance(value, list):
            raise ValueError(f"coordinates must be nested arrays, given: {value!r}")
        return value

    @classmethod
    def _numbers(cls, value: JsonValue) -> list[float]:
        """
        Require a JSON array of numbers.

        Parameters
        ----------
        value : JsonValue
            The position to check.

        Returns
        -------
        list[float]
            The numbers of the position.

        Raises
        ------
        ValueError
            If the value is not an array of numbers.
        """
        numbers: list[float] = []
        for item in cls._array(value):
            if isinstance(item, bool) or not isinstance(item, int | float):
                raise ValueError(f"a position must contain numbers, given: {value!r}")
            numbers.append(float(item))
        return numbers
