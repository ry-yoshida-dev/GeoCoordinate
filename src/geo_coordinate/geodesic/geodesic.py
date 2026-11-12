from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from pyproj import Geod
from units import Angle, AngleUnit, Area, AreaUnit, Length, LengthUnit

from ..altitude import Altitude
from ..base import GeoCoordinateBase
from ..bearing import Bearing
from ..coordinates import GeoCoordinates
from ..reference_system import Ellipsoid
from ..shape import GeoLinearRing, GeoMultiPolygon, GeoPolygon
from .inverse import GeodesicInverse


class Geodesic:
    """
    Shortest paths on a reference ellipsoid, accurate to a few nanometres.

    `GeoCoordinateBase.distance_to` approximates the Earth by a sphere, which is off by
    up to about 0.5 percent. Surveying and the measurement of parcels need the
    ellipsoid of the datum instead, which this class solves with the algorithms of
    Karney (2013) as implemented by PROJ. Altitudes are ignored.

    Parameters
    ----------
    ellipsoid : Ellipsoid
        The ellipsoid to solve on, such as `GeodeticCrs.JGD2011.ellipsoid`.
    """

    def __init__(self, ellipsoid: Ellipsoid = Ellipsoid.GRS80) -> None:
        self._ellipsoid: Ellipsoid = ellipsoid
        self._geod: Geod = ellipsoid.geod

    @property
    def ellipsoid(self) -> Ellipsoid:
        """
        Return the ellipsoid the geodesics are solved on.

        Returns
        -------
        Ellipsoid
            The ellipsoid given at construction.
        """
        return self._ellipsoid

    def inverse(self, start: GeoCoordinateBase, end: GeoCoordinateBase) -> GeodesicInverse:
        """
        Solve for the geodesics between pairs of places.

        Parameters
        ----------
        start : GeoCoordinateBase
            The places to start from.
        end : GeoCoordinateBase
            The places to end at, element-wise. Either side may hold a single
            coordinate, which is broadcast against the other.

        Returns
        -------
        GeodesicInverse
            The lengths and the bearings at both ends of each geodesic.

        Raises
        ------
        ValueError
            If both sides hold more than one coordinate and differ in length.
        """
        length: int = GeoCoordinateBase.broadcast_length({"start": len(start), "end": len(end)})
        start_longitude, start_latitude = self._broadcast(start, length)
        end_longitude, end_latitude = self._broadcast(end, length)
        initial, final, distance = self._geod.inv(
            start_longitude,
            start_latitude,
            end_longitude,
            end_latitude,
            return_back_azimuth=False,
        )
        return GeodesicInverse(
            distance=Length(value=np.asarray(distance, dtype=np.float64), unit=LengthUnit.M),
            initial_bearing=self._bearing(initial),
            final_bearing=self._bearing(final),
        )

    def distance(self, start: GeoCoordinateBase, end: GeoCoordinateBase) -> Length:
        """
        Lengths of the geodesics between pairs of places.

        Parameters
        ----------
        start : GeoCoordinateBase
            The places to start from.
        end : GeoCoordinateBase
            The places to end at, broadcast as in `inverse`.

        Returns
        -------
        Length
            The distances in meters.

        Raises
        ------
        ValueError
            If both sides hold more than one coordinate and differ in length.
        """
        return self.inverse(start, end).distance

    def direct[Coordinates: GeoCoordinateBase](
        self, start: Coordinates, bearing: Bearing, distance: Length
    ) -> Coordinates:
        """
        Places reached by travelling along geodesics, with the altitudes carried over.

        Parameters
        ----------
        start : Coordinates
            The places to start from, a `GeoCoordinate` or a `GeoCoordinates`.
        bearing : Bearing
            The initial bearings, clockwise from true north.
        distance : Length
            The distances to travel on the ellipsoid.

        Returns
        -------
        Coordinates
            The destinations, of the same type, in degrees with longitudes within
            [-180, 180). Each argument may hold a single element, which is broadcast
            against the others.

        Raises
        ------
        ValueError
            If the bearings are measured from magnetic north, the arguments hold more
            than one element and differ in length, or the destinations do not fit the
            type of `start`.
        """
        if not bearing.is_true_north:
            raise ValueError("direct requires bearings measured from true north")
        length: int = GeoCoordinateBase.broadcast_length(
            {"start": len(start), "bearing": len(bearing), "distance": len(distance.value)}
        )
        start_longitude, start_latitude = self._broadcast(start, length)
        longitude, latitude, _ = self._geod.fwd(
            start_longitude,
            start_latitude,
            np.broadcast_to(bearing.degree, (length,)).astype(np.float64),
            np.broadcast_to(distance.meter, (length,)).astype(np.float64),
            return_back_azimuth=False,
        )
        wrapped_longitude: NDArray[np.float64] = (
            np.mod(np.asarray(longitude, dtype=np.float64) + 180.0, 360.0) - 180.0
        )
        altitude: Altitude | None = (
            None if start.altitude is None else start.altitude.broadcast_to(length)
        )
        return type(start)(
            latitude=Angle(value=np.asarray(latitude, dtype=np.float64), unit=AngleUnit.DEGREE),
            longitude=Angle(value=wrapped_longitude, unit=AngleUnit.DEGREE),
            altitude=altitude,
        )

    def segment_distances(self, path: GeoCoordinates) -> Length:
        """
        Lengths of the geodesics between consecutive coordinates of a path.

        Parameters
        ----------
        path : GeoCoordinates
            The coordinates in order.

        Returns
        -------
        Length
            The distances in meters, of shape (N - 1,), or empty for fewer than two
            coordinates.
        """
        if len(path) < 2:
            return Length(value=np.zeros(0), unit=LengthUnit.M)
        return self.distance(path[:-1], path[1:])

    def path_length(self, path: GeoCoordinates) -> Length:
        """
        Total length along a path of geodesics through the coordinates in order.

        Parameters
        ----------
        path : GeoCoordinates
            The coordinates in order.

        Returns
        -------
        Length
            The total distance in meters, of shape (1,).
        """
        total: NDArray[np.float64] = np.array([np.sum(self.segment_distances(path).meter)])
        return Length(value=total, unit=LengthUnit.M)

    def area(self, shape: GeoPolygon | GeoMultiPolygon) -> Area:
        """
        Area of a polygon or of all parts of a multi polygon on the ellipsoid.

        The edges are taken as geodesics, and holes are subtracted. The rings may run
        either way.

        Parameters
        ----------
        shape : GeoPolygon | GeoMultiPolygon
            The area to measure.

        Returns
        -------
        Area
            The total area in square meters, of shape (1,).
        """
        match shape:
            case GeoPolygon():
                polygons: tuple[GeoPolygon, ...] = (shape,)
            case GeoMultiPolygon():
                polygons = shape.polygons
        total: float = sum(
            (
                self._ring_area(polygon.exterior)
                - sum((self._ring_area(hole) for hole in polygon.holes), 0.0)
                for polygon in polygons
            ),
            0.0,
        )
        return Area(value=np.array([total]), unit=AreaUnit.SQUARE_METER)

    def perimeter(self, shape: GeoLinearRing | GeoPolygon | GeoMultiPolygon) -> Length:
        """
        Length around a ring, or around every ring of a polygon or multi polygon.

        Parameters
        ----------
        shape : GeoLinearRing | GeoPolygon | GeoMultiPolygon
            The shape to measure. The rings of holes count towards the perimeter.

        Returns
        -------
        Length
            The total length of the geodesic edges in meters, of shape (1,).
        """
        match shape:
            case GeoLinearRing():
                rings: tuple[GeoLinearRing, ...] = (shape,)
            case GeoPolygon():
                rings = shape.rings
            case GeoMultiPolygon():
                rings = tuple(ring for polygon in shape.polygons for ring in polygon.rings)
        total: float = sum(
            (float(self.path_length(ring.closed_vertices).meter[0]) for ring in rings), 0.0
        )
        return Length(value=np.array([total]), unit=LengthUnit.M)

    def _ring_area(self, ring: GeoLinearRing) -> float:
        """
        Unsigned area enclosed by a ring of geodesic edges.

        Parameters
        ----------
        ring : GeoLinearRing
            The ring to measure.

        Returns
        -------
        float
            The area in square meters.
        """
        area, _ = self._geod.polygon_area_perimeter(
            ring.vertices.longitude.degree.astype(np.float64),
            ring.vertices.latitude.degree.astype(np.float64),
        )
        return abs(float(area))

    @staticmethod
    def _broadcast(coordinates: GeoCoordinateBase, length: int) -> NDArray[np.float64]:
        """
        Longitudes and latitudes in degrees broadcast to a length.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The coordinates, of length one or `length`.
        length : int
            The length to broadcast to.

        Returns
        -------
        NDArray[np.float64]
            The longitudes and latitudes, of shape (2, length).
        """
        return np.vstack(
            [
                np.broadcast_to(coordinates.longitude.degree, (length,)),
                np.broadcast_to(coordinates.latitude.degree, (length,)),
            ]
        ).astype(np.float64)

    @staticmethod
    def _bearing(azimuth: NDArray[np.float64] | float) -> Bearing:
        """
        Bearings from true north of azimuths within [-180, 180] degrees.

        Parameters
        ----------
        azimuth : NDArray[np.float64] | float
            The azimuths returned by PROJ.

        Returns
        -------
        Bearing
            The bearings within [0, 360).
        """
        degree: NDArray[np.float64] = np.atleast_1d(np.asarray(azimuth, dtype=np.float64))
        return Bearing.wrapped(Angle(value=degree, unit=AngleUnit.DEGREE))
