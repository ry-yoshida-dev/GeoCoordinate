from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

import numpy as np
from pyproj import CRS
from units import Angle, AngleUnit

from ..coordinate import GeoCoordinate
from ..hemisphere import LatitudeHemisphere
from .geodetic_crs import GeodeticCrs

ZONE_COUNT: Final[int] = 60
ZONE_WIDTH_DEGREES: Final[float] = 6.0
NORTH_EPSG_BASE: Final[int] = 32600
SOUTH_EPSG_BASE: Final[int] = 32700
NORTHERNMOST_LATITUDE: Final[float] = 84.0
SOUTHERNMOST_LATITUDE: Final[float] = -80.0


@dataclass(frozen=True)
class UtmZone:
    """
    Zone of the Universal Transverse Mercator system on WGS 84.

    Each zone is a band of 6 degrees of longitude, numbered eastward from 1 at 180
    degrees west, and projected separately for each hemisphere. The scale error is
    1 part in 2500 on the central meridian and grows to roughly 1 part in 1000 at
    the edges of a zone near the equator. The system covers latitudes
    from 80 degrees south to 84 degrees north; the polar regions beyond are left to
    the Universal Polar Stereographic system.

    Parameters
    ----------
    number : int
        The zone number, from 1 to 60.
    hemisphere : LatitudeHemisphere
        The hemisphere the zone is projected for.

    Raises
    ------
    ValueError
        If `number` is not between 1 and 60.
    """

    number: int
    hemisphere: LatitudeHemisphere

    def __post_init__(self) -> None:
        if not 1 <= self.number <= ZONE_COUNT:
            raise ValueError(f"UTM zone number must be between 1 and {ZONE_COUNT}: {self.number}")

    @classmethod
    def containing(cls, location: GeoCoordinate) -> UtmZone:
        """
        Choose the zone a location lies in.

        Zones are chosen by longitude alone, ignoring the widened zones of Norway and
        Svalbard, which only move their borders.

        Parameters
        ----------
        location : GeoCoordinate
            The location to measure around, such as the centre of a dataset.

        Returns
        -------
        UtmZone
            The zone whose band holds the longitude, projected for the hemisphere of the
            latitude; a location on 180 degrees east falls in zone 60.

        Raises
        ------
        ValueError
            If the location lies beyond the latitudes the system covers.
        """
        latitude = float(location.latitude.degree[0])
        longitude = float(location.longitude.degree[0])
        if not SOUTHERNMOST_LATITUDE <= latitude <= NORTHERNMOST_LATITUDE:
            raise ValueError(
                f"UTM covers latitudes from {SOUTHERNMOST_LATITUDE} to "
                + f"{NORTHERNMOST_LATITUDE} degrees: {latitude}"
            )
        number = min(math.floor((longitude + 180.0) / ZONE_WIDTH_DEGREES) + 1, ZONE_COUNT)
        return cls(number=number, hemisphere=LatitudeHemisphere.from_is_negative(latitude < 0.0))

    @classmethod
    def from_crs(cls, crs: CRS) -> UtmZone | None:
        """
        Identify a pyproj CRS as a zone.

        Parameters
        ----------
        crs : CRS
            The CRS to identify.

        Returns
        -------
        UtmZone | None
            The zone whose EPSG code the CRS has, or None for any other CRS, including
            UTM zones on other datums.
        """
        epsg = crs.to_epsg()
        if epsg is None:
            return None
        for base, hemisphere in (
            (NORTH_EPSG_BASE, LatitudeHemisphere.NORTH),
            (SOUTH_EPSG_BASE, LatitudeHemisphere.SOUTH),
        ):
            if 1 <= epsg - base <= ZONE_COUNT:
                return cls(number=epsg - base, hemisphere=hemisphere)
        return None

    @property
    def epsg(self) -> int:
        """
        Return the EPSG code of this zone.

        Returns
        -------
        int
            326xx in the northern hemisphere and 327xx in the southern, xx being the
            zone number.
        """
        match self.hemisphere:
            case LatitudeHemisphere.NORTH:
                return NORTH_EPSG_BASE + self.number
            case LatitudeHemisphere.SOUTH:
                return SOUTH_EPSG_BASE + self.number

    @property
    def crs(self) -> CRS:
        """
        Return this zone as a pyproj object.

        Returns
        -------
        CRS
            The CRS of `epsg`.
        """
        return CRS.from_epsg(self.epsg)

    @property
    def geodetic_crs(self) -> GeodeticCrs:
        """
        Return the geographic CRS the zones are defined on.

        Returns
        -------
        GeodeticCrs
            WGS 84, for every zone.
        """
        return GeodeticCrs.WGS84

    @property
    def central_meridian(self) -> Angle:
        """
        Return the longitude at the middle of the zone.

        Returns
        -------
        Angle
            The central meridian, along which the scale factor is 0.9996.
        """
        degrees = -180.0 + ZONE_WIDTH_DEGREES * (self.number - 0.5)
        return Angle(value=np.array([degrees]), unit=AngleUnit.DEGREE)

    def __str__(self) -> str:
        return f"EPSG:{self.epsg}"
