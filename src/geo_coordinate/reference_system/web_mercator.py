from __future__ import annotations

import math
from enum import IntEnum
from typing import Final

from pyproj import CRS

from .geodetic_crs import GeodeticCrs

EARTH_EQUATORIAL_RADIUS_METRES: Final[float] = 6_378_137.0


class WebMercator(IntEnum):
    """
    The Web Mercator projection of web maps and their tiles.

    Like the other CRSs, the member is its EPSG code. The projection treats WGS 84
    coordinates as if on a sphere of the equatorial radius. Its world is the square
    of side `2 * half_extent` metres centred on the origin, reached at about 85.05
    degrees of latitude north and south.

    Attributes
    ----------
    PSEUDO_MERCATOR
        WGS 84 / Pseudo-Mercator, EPSG:3857.
    """

    PSEUDO_MERCATOR = 3857

    @property
    def epsg(self) -> int:
        """
        Return the EPSG code of this projection.

        Returns
        -------
        int
            3857.
        """
        return self.value

    @property
    def crs(self) -> CRS:
        """
        Return this projection as a pyproj object.

        Returns
        -------
        CRS
            The CRS of `epsg`.
        """
        return CRS.from_epsg(self.value)

    @property
    def geodetic_crs(self) -> GeodeticCrs:
        """
        Return the geographic CRS the projection is defined on.

        Returns
        -------
        GeodeticCrs
            WGS 84.
        """
        return GeodeticCrs.WGS84

    @property
    def half_extent(self) -> float:
        """
        Return half the side of the square world, in metres.

        Returns
        -------
        float
            Pi times the equatorial radius of WGS 84.
        """
        return math.pi * EARTH_EQUATORIAL_RADIUS_METRES

    def __str__(self) -> str:
        return f"EPSG:{self.value}"
