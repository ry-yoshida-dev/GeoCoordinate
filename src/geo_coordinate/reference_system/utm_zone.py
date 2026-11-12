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
JAPANESE_ZONE_NUMBERS: Final[range] = range(51, 56)

# The EPSG code of a northern zone over Japan on a Japanese datum is the base of the
# datum plus the zone number.
JAPANESE_EPSG_BASES: Final[dict[GeodeticCrs, int]] = {
    GeodeticCrs.JGD2011: 6637,
    GeodeticCrs.JGD2000: 3046,
    GeodeticCrs.TOKYO: 3041,
}


@dataclass(frozen=True)
class UtmZone:
    """
    Zone of the Universal Transverse Mercator system.

    Each zone is a band of 6 degrees of longitude, numbered eastward from 1 at 180
    degrees west, and projected separately for each hemisphere. The scale error is
    1 part in 2500 on the central meridian and grows to roughly 1 part in 1000 at
    the edges of a zone near the equator. The system covers latitudes
    from 80 degrees south to 84 degrees north; the polar regions beyond are left to
    the Universal Polar Stereographic system.

    The zones are defined on WGS 84 worldwide. The northern zones 51 to 55, which
    cover Japan, are also defined on JGD2011, JGD2000 and Tokyo Datum, as used by
    Japanese topographic maps. Minamitorishima, at about 154 degrees east, lies in
    zone 56, which no Japanese datum defines; use WGS 84 or a Japan Plane
    Rectangular zone there.

    Parameters
    ----------
    number : int
        The zone number, from 1 to 60.
    hemisphere : LatitudeHemisphere
        The hemisphere the zone is projected for.
    geodetic_crs : GeodeticCrs
        The datum the zone is defined on.

    Raises
    ------
    ValueError
        If `number` is not between 1 and 60, or the zone is not defined on
        `geodetic_crs`: on a Japanese datum, only northern zones 51 to 55 are.
    """

    number: int
    hemisphere: LatitudeHemisphere
    geodetic_crs: GeodeticCrs = GeodeticCrs.WGS84

    def __post_init__(self) -> None:
        if not 1 <= self.number <= ZONE_COUNT:
            raise ValueError(f"UTM zone number must be between 1 and {ZONE_COUNT}: {self.number}")
        if self.geodetic_crs is not GeodeticCrs.WGS84 and (
            self.hemisphere is not LatitudeHemisphere.NORTH
            or self.number not in JAPANESE_ZONE_NUMBERS
        ):
            raise ValueError(
                f"UTM zones on {self.geodetic_crs.label} are the northern zones "
                + f"{JAPANESE_ZONE_NUMBERS.start} to {JAPANESE_ZONE_NUMBERS.stop - 1} only, "
                + f"given: {self.number}{self.hemisphere.value}"
            )

    @classmethod
    def containing(
        cls, location: GeoCoordinate, geodetic_crs: GeodeticCrs = GeodeticCrs.WGS84
    ) -> UtmZone:
        """
        Choose the zone a location lies in.

        Zones are chosen by longitude alone, ignoring the widened zones of Norway and
        Svalbard, which only move their borders.

        Parameters
        ----------
        location : GeoCoordinate
            The location to measure around, such as the centre of a dataset.
        geodetic_crs : GeodeticCrs
            The datum of the zone to choose.

        Returns
        -------
        UtmZone
            The zone whose band holds the longitude, projected for the hemisphere of the
            latitude; a location on 180 degrees east falls in zone 60.

        Raises
        ------
        ValueError
            If the location lies beyond the latitudes the system covers, or in a zone
            not defined on `geodetic_crs`.
        """
        latitude = float(location.latitude.degree[0])
        longitude = float(location.longitude.degree[0])
        if not SOUTHERNMOST_LATITUDE <= latitude <= NORTHERNMOST_LATITUDE:
            raise ValueError(
                f"UTM covers latitudes from {SOUTHERNMOST_LATITUDE} to "
                + f"{NORTHERNMOST_LATITUDE} degrees: {latitude}"
            )
        number = min(math.floor((longitude + 180.0) / ZONE_WIDTH_DEGREES) + 1, ZONE_COUNT)
        return cls(
            number=number,
            hemisphere=LatitudeHemisphere.from_is_negative(latitude < 0.0),
            geodetic_crs=geodetic_crs,
        )

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
            UTM zones on datums other than those of `GeodeticCrs`.
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
        for geodetic_crs, base in JAPANESE_EPSG_BASES.items():
            if epsg - base in JAPANESE_ZONE_NUMBERS:
                return cls(
                    number=epsg - base,
                    hemisphere=LatitudeHemisphere.NORTH,
                    geodetic_crs=geodetic_crs,
                )
        return None

    @property
    def epsg(self) -> int:
        """
        Return the EPSG code of this zone.

        Returns
        -------
        int
            On WGS 84, 326xx in the northern hemisphere and 327xx in the southern, xx
            being the zone number. Zones 51 to 55 are 6688 to 6692 on JGD2011, 3097 to
            3101 on JGD2000 and 3092 to 3096 on Tokyo Datum.
        """
        if self.geodetic_crs is not GeodeticCrs.WGS84:
            return JAPANESE_EPSG_BASES[self.geodetic_crs] + self.number
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
