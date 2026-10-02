from __future__ import annotations

from enum import IntEnum

from pyproj import CRS


class GeodeticCrs(IntEnum):
    """
    Geographic coordinate reference systems in which Japanese data is published.

    Each value is the EPSG code itself, so a member can be passed straight to
    `GeoDataFrame.set_crs` or `to_crs`. All are geographic, measured in degrees, so
    lengths and areas must be computed after projecting to a plane CRS such as a
    `JapanPlaneRectangularZone`.

    Attributes
    ----------
    TOKYO
        Tokyo Datum, the old Japanese datum used before 2002.
    JGD2000
        Japanese Geodetic Datum 2000.
    JGD2011
        Japanese Geodetic Datum 2011, revised after the 2011 Tohoku earthquake and
        used by current distributions.
    WGS84
        WGS 84, the global geographic CRS.
    """

    TOKYO = 4301
    JGD2000 = 4612
    JGD2011 = 6668
    WGS84 = 4326

    @property
    def epsg(self) -> int:
        """
        Return the EPSG code of this CRS.

        Returns
        -------
        int
            A code accepted by `GeoDataFrame.set_crs` and `to_crs`.
        """
        return self.value

    @property
    def crs(self) -> CRS:
        """
        Return this CRS as a pyproj object.

        Returns
        -------
        CRS
            The CRS of `epsg`.
        """
        return CRS.from_epsg(self.value)

    @property
    def geodetic_crs(self) -> GeodeticCrs:
        """
        Return the geographic CRS this CRS is defined on, which is itself.

        Returns
        -------
        GeodeticCrs
            This member.
        """
        return self

    @property
    def label(self) -> str:
        """
        Return the name of this CRS.

        Returns
        -------
        str
            A name for messages and listings.
        """
        match self:
            case GeodeticCrs.TOKYO:
                return "Tokyo Datum"
            case GeodeticCrs.JGD2000:
                return "JGD2000"
            case GeodeticCrs.JGD2011:
                return "JGD2011"
            case GeodeticCrs.WGS84:
                return "WGS 84"

    @classmethod
    def from_crs(cls, crs: CRS) -> GeodeticCrs | None:
        """
        Identify a CRS as one of the members.

        Parameters
        ----------
        crs : CRS
            The CRS to identify.

        Returns
        -------
        GeodeticCrs | None
            The matching member. None when `crs` has no EPSG code or is another CRS,
            including any projected CRS.
        """
        epsg = crs.to_epsg()
        if epsg is None:
            return None
        return next((member for member in cls if member.epsg == epsg), None)

    def __str__(self) -> str:
        return f"EPSG:{self.value}"
