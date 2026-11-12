from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
from pyproj import CRS
from units import Angle, AngleUnit, DegreesMinutesSeconds

from ..coordinate import GeoCoordinate
from .geodetic_crs import GeodeticCrs

ZONE_COUNT: Final[int] = 19

# The EPSG code of each zone is the base of its datum plus the zone number.
EPSG_BASES: Final[dict[GeodeticCrs, int]] = {
    GeodeticCrs.JGD2011: 6668,
    GeodeticCrs.JGD2000: 2442,
    GeodeticCrs.TOKYO: 30160,
}

# Central meridians east of Greenwich in degrees and minutes, by zone number.
CENTRAL_MERIDIANS: Final[tuple[tuple[int, int], ...]] = (
    (129, 30),
    (131, 0),
    (132, 10),
    (133, 30),
    (134, 20),
    (136, 0),
    (137, 10),
    (138, 30),
    (139, 50),
    (140, 50),
    (140, 15),
    (142, 15),
    (144, 15),
    (142, 0),
    (127, 30),
    (124, 0),
    (131, 0),
    (136, 0),
    (154, 0),
)

# Origin latitudes north of the equator in degrees, by zone number.
ORIGIN_LATITUDES: Final[tuple[float, ...]] = (
    33.0,
    33.0,
    36.0,
    33.0,
    36.0,
    36.0,
    36.0,
    36.0,
    36.0,
    40.0,
    44.0,
    44.0,
    44.0,
    26.0,
    26.0,
    26.0,
    26.0,
    20.0,
    26.0,
)


@dataclass(frozen=True)
class JapanPlaneRectangularZone:
    """
    Zone of the Japan Plane Rectangular Coordinate System.

    Geographic coordinates are measured in degrees, so lengths and areas must
    be computed on a projected system instead. Each of the nineteen zones defined by
    the Survey Act Enforcement Order is a transverse Mercator projection, and
    distortion stays below roughly 1 part in 10000 within a zone.

    The zones are defined on JGD2011 today, on JGD2000 from April 2002 until JGD2011
    took effect in October 2011 after the Tohoku earthquake, and on Tokyo Datum before
    April 2002. All use the same origins and scale
    factor, so the same zone number on any of them projects the same latitudes and
    longitudes to the same plane; but the same place has latitudes and longitudes about
    400 m apart on Tokyo Datum and on JGD2011, and so plane coordinates about as far
    apart. JGD2000 and JGD2011 differ only where the earthquake moved the ground, by up
    to about 5 m.

    The Ministry of Land, Infrastructure, Transport and Tourism notice of 2002
    (平成14年国土交通省告示第9号) assigns each zone its area. Zones I to XIII cover
    Kyushu to Hokkaido by prefecture, and within Hokkaido by municipality and
    subprefectural bureau; Kagoshima is split between I and II by lines of
    latitude and longitude. Zone XV covers the main islands of Okinawa, XVI and
    XVII its islands west of 126 and east of 130 degrees east. Zones XIV, XVIII
    and XIX cover the islands of Tokyo south of 28 degrees north: Ogasawara,
    Okinotorishima and Minamitorishima respectively.

    Parameters
    ----------
    number : int
        The zone number, from 1 to 19, as in 第IX系.
    geodetic_crs : GeodeticCrs
        The datum the zone is defined on: JGD2011, JGD2000 or Tokyo Datum.

    Raises
    ------
    ValueError
        If `number` is not between 1 and 19, or no zones are defined on `geodetic_crs`.
    """

    number: int
    geodetic_crs: GeodeticCrs = GeodeticCrs.JGD2011

    def __post_init__(self) -> None:
        if not 1 <= self.number <= ZONE_COUNT:
            raise ValueError(f"zone number must be between 1 and {ZONE_COUNT}: {self.number}")
        if self.geodetic_crs not in EPSG_BASES:
            raise ValueError(
                "zones are defined on JGD2011, JGD2000 and Tokyo Datum only, given: "
                + self.geodetic_crs.label
            )

    @classmethod
    def zones(
        cls, geodetic_crs: GeodeticCrs = GeodeticCrs.JGD2011
    ) -> tuple[JapanPlaneRectangularZone, ...]:
        """
        Return the nineteen zones on a datum.

        Parameters
        ----------
        geodetic_crs : GeodeticCrs
            JGD2011, JGD2000 or Tokyo Datum.

        Returns
        -------
        tuple[JapanPlaneRectangularZone, ...]
            The zones from I to XIX.

        Raises
        ------
        ValueError
            If no zones are defined on `geodetic_crs`.
        """
        return tuple(cls(number, geodetic_crs) for number in range(1, ZONE_COUNT + 1))

    @classmethod
    def from_crs(cls, crs: CRS) -> JapanPlaneRectangularZone | None:
        """
        Identify a pyproj CRS as a zone.

        Parameters
        ----------
        crs : CRS
            The CRS to identify.

        Returns
        -------
        JapanPlaneRectangularZone | None
            The zone whose EPSG code the CRS has, or None for any other CRS.
        """
        epsg = crs.to_epsg()
        if epsg is None:
            return None
        for geodetic_crs, base in EPSG_BASES.items():
            if 1 <= epsg - base <= ZONE_COUNT:
                return cls(epsg - base, geodetic_crs)
        return None

    @property
    def epsg(self) -> int:
        """
        Return the EPSG code of this zone.

        Returns
        -------
        int
            6669 to 6687 on JGD2011, 2443 to 2461 on JGD2000 and 30161 to 30179 on
            Tokyo Datum, from zone I to XIX.
        """
        return EPSG_BASES[self.geodetic_crs] + self.number

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
    def roman_numeral(self) -> str:
        """
        Return the number of the zone in Roman numerals, as the Survey Act writes it.

        Returns
        -------
        str
            The numeral, from `I` to `XIX`.
        """
        tens: str = "X" * (self.number // 10)
        units: tuple[str, ...] = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
        return tens + units[self.number % 10]

    @property
    def central_meridian(self) -> Angle:
        """
        Return the east longitude of the zone origin.

        Returns
        -------
        Angle
            The central meridian, along which the scale factor is 0.9999.
        """
        degrees, minutes = CENTRAL_MERIDIANS[self.number - 1]
        return Angle.from_degrees_minutes_seconds(
            DegreesMinutesSeconds(
                degrees=np.array([float(degrees)]),
                minutes=np.array([float(minutes)]),
                seconds=np.zeros(1),
                is_negative=np.zeros(1, dtype=np.bool_),
            )
        )

    @property
    def origin_latitude(self) -> Angle:
        """
        Return the north latitude of the zone origin.

        Returns
        -------
        Angle
            The latitude at which the northing of the zone is zero.
        """
        return Angle(value=np.array([ORIGIN_LATITUDES[self.number - 1]]), unit=AngleUnit.DEGREE)

    @property
    def origin(self) -> GeoCoordinate:
        """
        Return the origin of the zone.

        Returns
        -------
        GeoCoordinate
            The point at `origin_latitude` on `central_meridian`, on `geodetic_crs`.
        """
        return GeoCoordinate(latitude=self.origin_latitude, longitude=self.central_meridian)

    @classmethod
    def nearest_to(
        cls, location: GeoCoordinate, geodetic_crs: GeodeticCrs = GeodeticCrs.JGD2011
    ) -> JapanPlaneRectangularZone:
        """
        Choose the zone whose origin is nearest to a location.

        The distance to each zone origin approximates the assignment of the Survey Act,
        which matches it in most of Japan but follows the borders of prefectures, so the
        chosen zone may differ from the assigned one near those borders.

        Parameters
        ----------
        location : GeoCoordinate
            The location to measure around, such as the centre of a dataset.
        geodetic_crs : GeodeticCrs
            The datum of the zone to choose, JGD2011, JGD2000 or Tokyo Datum.

        Returns
        -------
        JapanPlaneRectangularZone
            The zone with the nearest origin; of zones as near, the lowest numbered.

        Raises
        ------
        ValueError
            If no zones are defined on `geodetic_crs`.
        """
        return min(
            cls.zones(geodetic_crs),
            key=lambda zone: float(location.distance_to(zone.origin).meter[0]),
        )

    @classmethod
    def is_covering(cls, location: GeoCoordinate) -> bool:
        """
        Tell whether a location lies where some zone is meant to be used.

        Each zone is meant for the area of use its EPSG definition on JGD2011 gives,
        approximated here by the bounding box of that area. The boxes enclose the land
        of each zone closely, so a location in Korea or Taiwan does not count, and
        neither may one a few kilometres offshore. The 400 m between the datums is
        ignored.

        Parameters
        ----------
        location : GeoCoordinate
            The location to test, such as the centre of a dataset.

        Returns
        -------
        bool
            Whether the bounding box of the area of use of any zone holds the location.
        """
        latitude = float(location.latitude.degree[0])
        longitude = float(location.longitude.degree[0])
        for zone in cls.zones():
            area = zone.crs.area_of_use
            if area is None:
                raise RuntimeError(f"{zone} has no area of use in the EPSG database")
            if area.west <= longitude <= area.east and area.south <= latitude <= area.north:
                return True
        return False

    def __str__(self) -> str:
        return f"EPSG:{self.epsg}"
