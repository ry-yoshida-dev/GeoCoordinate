from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from pyproj import Transformer
from pyproj.enums import TransformDirection
from units import Angle, AngleUnit

from ..base import GeoCoordinateBase
from ..coordinates import GeoCoordinates
from ..reference_system import Ellipsoid
from .earth_centered import EarthCenteredCoordinates
from .geodetic_position import GeodeticPosition


class GeocentricConversion:
    """
    Converts latitude, longitude and ellipsoidal height to Earth-centred coordinates.

    The conversion is exact on the ellipsoid and involves no datum shift: coordinates
    on JGD2011 become ECEF coordinates in the frame of JGD2011.

    Parameters
    ----------
    ellipsoid : Ellipsoid
        The ellipsoid the latitudes and heights are measured on.
    """

    def __init__(self, ellipsoid: Ellipsoid = Ellipsoid.GRS80) -> None:
        self._ellipsoid: Ellipsoid = ellipsoid
        self._transformer: Transformer = Transformer.from_pipeline(
            "+proj=pipeline"
            + " +step +proj=unitconvert +xy_in=deg +xy_out=rad"
            + f" +step +proj=cart {ellipsoid.proj_parameters}"
        )

    @property
    def ellipsoid(self) -> Ellipsoid:
        """
        Return the ellipsoid of the conversion.

        Returns
        -------
        Ellipsoid
            The ellipsoid given at construction.
        """
        return self._ellipsoid

    def to_earth_centered(
        self, coordinates: GeoCoordinateBase, ellipsoidal_height: NDArray[np.float64]
    ) -> EarthCenteredCoordinates:
        """
        Convert places to Earth-centred coordinates.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The latitudes and longitudes. Their altitudes, above mean sea level, are
            not used.
        ellipsoidal_height : NDArray[np.float64]
            The heights above the ellipsoid in meters, of shape (N,).

        Returns
        -------
        EarthCenteredCoordinates
            The X, Y and Z in meters.

        Raises
        ------
        ValueError
            If `ellipsoidal_height` differs in shape from the coordinates.
        """
        position: GeodeticPosition = GeodeticPosition(
            coordinates=GeoCoordinates(
                latitude=coordinates.latitude, longitude=coordinates.longitude
            ),
            ellipsoidal_height=ellipsoidal_height.astype(np.float64),
        )
        return self.position_to_earth_centered(position)

    def position_to_earth_centered(self, position: GeodeticPosition) -> EarthCenteredCoordinates:
        """
        Convert geodetic positions to Earth-centred coordinates.

        Parameters
        ----------
        position : GeodeticPosition
            The latitudes, longitudes and heights above the ellipsoid.

        Returns
        -------
        EarthCenteredCoordinates
            The X, Y and Z in meters.
        """
        x, y, z = self._transformer.transform(
            position.coordinates.longitude.degree,
            position.coordinates.latitude.degree,
            position.ellipsoidal_height,
        )
        return EarthCenteredCoordinates(
            x=np.asarray(x, dtype=np.float64),
            y=np.asarray(y, dtype=np.float64),
            z=np.asarray(z, dtype=np.float64),
        )

    def to_geodetic(self, points: EarthCenteredCoordinates) -> GeodeticPosition:
        """
        Convert Earth-centred coordinates to latitudes, longitudes and heights.

        Parameters
        ----------
        points : EarthCenteredCoordinates
            The X, Y and Z in meters.

        Returns
        -------
        GeodeticPosition
            The latitudes and longitudes in degrees and the heights above the ellipsoid
            in meters.
        """
        longitude, latitude, height = self._transformer.transform(
            points.x, points.y, points.z, direction=TransformDirection.INVERSE
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
