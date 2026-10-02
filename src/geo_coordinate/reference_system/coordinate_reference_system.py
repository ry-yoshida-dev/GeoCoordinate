from __future__ import annotations

from typing import Protocol

from pyproj import CRS

from .geodetic_crs import GeodeticCrs


class CoordinateReferenceSystem(Protocol):
    """
    A coordinate reference system identified by an EPSG code.

    `GeodeticCrs`, `JapanPlaneRectangularZone` and `WebMercator` all satisfy it,
    so code that only needs a CRS can accept any of them. Each prints as
    `EPSG:<code>`.
    """

    @property
    def epsg(self) -> int:
        """
        Return the EPSG code.

        Returns
        -------
        int
            The code accepted by `GeoDataFrame.set_crs` and `to_crs`.
        """
        ...

    @property
    def crs(self) -> CRS:
        """
        Return the CRS as a pyproj object.

        Returns
        -------
        CRS
            The CRS of `epsg`.
        """
        ...

    @property
    def geodetic_crs(self) -> GeodeticCrs:
        """
        Return the geographic CRS the coordinates are defined on.

        Returns
        -------
        GeodeticCrs
            The CRS itself when it is geographic, otherwise the one it projects.
        """
        ...
