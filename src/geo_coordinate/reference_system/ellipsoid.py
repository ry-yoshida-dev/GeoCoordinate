from __future__ import annotations

from enum import Enum

import numpy as np
from pyproj import Geod
from units import Length, LengthUnit


class Ellipsoid(Enum):
    """
    Reference ellipsoids the geodetic datums of `GeodeticCrs` are defined on.

    Each value is the name PROJ knows the ellipsoid by.

    Attributes
    ----------
    GRS80
        Geodetic Reference System 1980, the ellipsoid of JGD2000 and JGD2011.
    WGS84
        The ellipsoid of WGS 84, which differs from GRS80 by 0.1 mm in its minor axis.
    BESSEL_1841
        Bessel 1841, the ellipsoid of Tokyo Datum.
    """

    GRS80 = "GRS80"
    WGS84 = "WGS84"
    BESSEL_1841 = "bessel"

    @property
    def semi_major_axis(self) -> Length:
        """
        Return the equatorial radius.

        Returns
        -------
        Length
            The semi-major axis in meters, of shape (1,).
        """
        return Length(value=np.array([self.semi_major_axis_meter]), unit=LengthUnit.M)

    @property
    def semi_major_axis_meter(self) -> float:
        """
        Return the equatorial radius in meters.

        Returns
        -------
        float
            The semi-major axis.
        """
        match self:
            case Ellipsoid.GRS80 | Ellipsoid.WGS84:
                return 6_378_137.0
            case Ellipsoid.BESSEL_1841:
                return 6_377_397.155

    @property
    def inverse_flattening(self) -> float:
        """
        Return the reciprocal of the flattening, the defining constant besides the radius.

        Returns
        -------
        float
            `a / (a - b)`, about 298 for the ellipsoids of the Earth.
        """
        match self:
            case Ellipsoid.GRS80:
                return 298.257222101
            case Ellipsoid.WGS84:
                return 298.257223563
            case Ellipsoid.BESSEL_1841:
                return 299.1528128

    @property
    def flattening(self) -> float:
        """
        Return the flattening.

        Returns
        -------
        float
            `(a - b) / a`.
        """
        return 1.0 / self.inverse_flattening

    @property
    def semi_minor_axis_meter(self) -> float:
        """
        Return the polar radius in meters.

        Returns
        -------
        float
            The semi-minor axis `a * (1 - f)`.
        """
        return self.semi_major_axis_meter * (1.0 - self.flattening)

    @property
    def eccentricity_squared(self) -> float:
        """
        Return the square of the first eccentricity.

        Returns
        -------
        float
            `f * (2 - f)`.
        """
        return self.flattening * (2.0 - self.flattening)

    @property
    def mean_radius_meter(self) -> float:
        """
        Return the arithmetic mean radius in meters.

        Returns
        -------
        float
            `(2a + b) / 3`, the radius of the sphere closest to the ellipsoid on average.
        """
        return (2.0 * self.semi_major_axis_meter + self.semi_minor_axis_meter) / 3.0

    @property
    def proj_parameters(self) -> str:
        """
        Return the PROJ parameters that define this ellipsoid.

        Returns
        -------
        str
            `+a=<radius> +rf=<inverse flattening>`, for use in a PROJ pipeline.
        """
        return f"+a={self.semi_major_axis_meter!r} +rf={self.inverse_flattening!r}"

    @property
    def geod(self) -> Geod:
        """
        Return the geodesic calculator of pyproj on this ellipsoid.

        Returns
        -------
        Geod
            A `Geod` of the radius and flattening of this ellipsoid.
        """
        return Geod(a=self.semi_major_axis_meter, rf=self.inverse_flattening)

    @property
    def label(self) -> str:
        """
        Return the name of this ellipsoid.

        Returns
        -------
        str
            A name for messages and listings.
        """
        match self:
            case Ellipsoid.GRS80:
                return "GRS 1980"
            case Ellipsoid.WGS84:
                return "WGS 84"
            case Ellipsoid.BESSEL_1841:
                return "Bessel 1841"

    def __str__(self) -> str:
        return self.label
