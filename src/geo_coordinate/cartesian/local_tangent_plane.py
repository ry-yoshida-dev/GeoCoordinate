from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray
from pyproj import Transformer
from pyproj.enums import TransformDirection
from units import Angle, AngleUnit

from ..base import GeoCoordinateBase
from ..coordinate import GeoCoordinate
from ..coordinates import GeoCoordinates
from ..reference_system import Ellipsoid
from .east_north_up import EastNorthUp
from .geodetic_position import GeodeticPosition


class LocalTangentPlane:
    """
    East-north-up frame tangent to the ellipsoid at an origin.

    Places are expressed relative to the origin in meters, east, north and up along
    the normal of the ellipsoid, as a drone, a robot or an AR scene expects. The
    conversion is exact, so it holds at any distance, although the axes only match the
    local east, north and up near the origin.

    Parameters
    ----------
    origin : GeoCoordinate
        The latitude and longitude of the origin. Its altitude is not used.
    origin_ellipsoidal_height : float
        The height of the origin above the ellipsoid, in meters.
    ellipsoid : Ellipsoid
        The ellipsoid the latitudes and heights are measured on.

    Raises
    ------
    ValueError
        If `origin_ellipsoidal_height` is not finite.
    """

    def __init__(
        self,
        origin: GeoCoordinate,
        origin_ellipsoidal_height: float = 0.0,
        ellipsoid: Ellipsoid = Ellipsoid.GRS80,
    ) -> None:
        if not math.isfinite(origin_ellipsoidal_height):
            raise ValueError(
                f"origin_ellipsoidal_height must be finite: {origin_ellipsoidal_height}"
            )
        self._origin: GeoCoordinate = origin
        self._origin_ellipsoidal_height: float = origin_ellipsoidal_height
        self._ellipsoid: Ellipsoid = ellipsoid
        self._transformer: Transformer = Transformer.from_pipeline(
            "+proj=pipeline"
            + " +step +proj=unitconvert +xy_in=deg +xy_out=rad"
            + f" +step +proj=cart {ellipsoid.proj_parameters}"
            + f" +step +proj=topocentric {ellipsoid.proj_parameters}"
            + f" +lon_0={float(origin.longitude.degree[0])!r}"
            + f" +lat_0={float(origin.latitude.degree[0])!r}"
            + f" +h_0={origin_ellipsoidal_height!r}"
        )

    @property
    def origin(self) -> GeoCoordinate:
        """
        Return the latitude and longitude of the origin.

        Returns
        -------
        GeoCoordinate
            The origin given at construction.
        """
        return self._origin

    @property
    def origin_ellipsoidal_height(self) -> float:
        """
        Return the height of the origin above the ellipsoid.

        Returns
        -------
        float
            The height in meters.
        """
        return self._origin_ellipsoidal_height

    @property
    def ellipsoid(self) -> Ellipsoid:
        """
        Return the ellipsoid of the frame.

        Returns
        -------
        Ellipsoid
            The ellipsoid given at construction.
        """
        return self._ellipsoid

    def to_east_north_up(
        self, coordinates: GeoCoordinateBase, ellipsoidal_height: NDArray[np.float64]
    ) -> EastNorthUp:
        """
        Express places relative to the origin.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The latitudes and longitudes. Their altitudes, above mean sea level, are
            not used.
        ellipsoidal_height : NDArray[np.float64]
            The heights above the ellipsoid in meters, of shape (N,).

        Returns
        -------
        EastNorthUp
            The east, north and up of each place in meters.

        Raises
        ------
        ValueError
            If `ellipsoidal_height` differs in shape from the coordinates.
        """
        if ellipsoidal_height.shape != (len(coordinates),):
            raise ValueError(
                f"ellipsoidal_height must be of shape ({len(coordinates)},), "
                + f"given: {ellipsoidal_height.shape}"
            )
        east, north, up = self._transformer.transform(
            coordinates.longitude.degree,
            coordinates.latitude.degree,
            ellipsoidal_height.astype(np.float64),
        )
        return EastNorthUp(
            east=np.asarray(east, dtype=np.float64),
            north=np.asarray(north, dtype=np.float64),
            up=np.asarray(up, dtype=np.float64),
        )

    def to_geodetic(self, points: EastNorthUp) -> GeodeticPosition:
        """
        Turn points relative to the origin back into latitudes, longitudes and heights.

        Parameters
        ----------
        points : EastNorthUp
            The east, north and up in meters.

        Returns
        -------
        GeodeticPosition
            The latitudes and longitudes in degrees and the heights above the ellipsoid
            in meters.
        """
        longitude, latitude, height = self._transformer.transform(
            points.east, points.north, points.up, direction=TransformDirection.INVERSE
        )
        return GeodeticPosition(
            coordinates=GeoCoordinates(
                latitude=Angle(value=np.asarray(latitude, dtype=np.float64), unit=AngleUnit.DEGREE),
                longitude=Angle(
                    value=np.asarray(longitude, dtype=np.float64), unit=AngleUnit.DEGREE
                ),
            ),
            ellipsoidal_height=np.asarray(height, dtype=np.float64),
        )
