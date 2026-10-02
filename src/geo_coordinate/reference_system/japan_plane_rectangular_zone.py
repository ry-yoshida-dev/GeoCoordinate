from __future__ import annotations

from enum import IntEnum

import numpy as np
from pyproj import CRS
from units import Angle, DegreesMinutesSeconds

from .geodetic_crs import GeodeticCrs


class JapanPlaneRectangularZone(IntEnum):
    """
    Zone of the Japan Plane Rectangular Coordinate System on JGD2011.

    Geographic coordinates are measured in degrees, so lengths and areas must
    be computed on a projected system instead. Each member is the EPSG code of
    one of the nineteen zones defined by the Survey Act Enforcement Order, and
    distortion stays below roughly 1 part in 10000 within a zone.

    The Ministry of Land, Infrastructure, Transport and Tourism notice of 2002
    (平成14年国土交通省告示第9号) assigns each zone its area. Zones I to XIII cover
    Kyushu to Hokkaido by prefecture, and within Hokkaido by municipality and
    subprefectural bureau; Kagoshima is split between I and II by lines of
    latitude and longitude. Zone XV covers the main islands of Okinawa, XVI and
    XVII its islands west of 126 and east of 130 degrees east. Zones XIV, XVIII
    and XIX cover the islands of Tokyo south of 28 degrees north: Ogasawara,
    Okinotorishima and Minamitorishima respectively.
    """

    ZONE_1 = 6669
    ZONE_2 = 6670
    ZONE_3 = 6671
    ZONE_4 = 6672
    ZONE_5 = 6673
    ZONE_6 = 6674
    ZONE_7 = 6675
    ZONE_8 = 6676
    ZONE_9 = 6677
    ZONE_10 = 6678
    ZONE_11 = 6679
    ZONE_12 = 6680
    ZONE_13 = 6681
    ZONE_14 = 6682
    ZONE_15 = 6683
    ZONE_16 = 6684
    ZONE_17 = 6685
    ZONE_18 = 6686
    ZONE_19 = 6687

    @property
    def epsg(self) -> int:
        """
        Return the EPSG code of this zone.

        Returns
        -------
        int
            The code accepted by `GeoDataFrame.to_crs`.
        """
        return self.value

    @property
    def crs(self) -> CRS:
        """
        Return this zone as a pyproj object.

        Returns
        -------
        CRS
            The CRS of `epsg`.
        """
        return CRS.from_epsg(self.value)

    @property
    def geodetic_crs(self) -> GeodeticCrs:
        """
        Return the geographic CRS the zones are defined on.

        Returns
        -------
        GeodeticCrs
            JGD2011, for every zone.
        """
        return GeodeticCrs.JGD2011

    @property
    def central_meridian(self) -> Angle:
        """
        Return the east longitude of the zone origin.

        Returns
        -------
        Angle
            The central meridian, along which the scale factor is 0.9999.
        """
        match self:
            case JapanPlaneRectangularZone.ZONE_1:
                return self._east_longitude(129, 30)
            case JapanPlaneRectangularZone.ZONE_2:
                return self._east_longitude(131, 0)
            case JapanPlaneRectangularZone.ZONE_3:
                return self._east_longitude(132, 10)
            case JapanPlaneRectangularZone.ZONE_4:
                return self._east_longitude(133, 30)
            case JapanPlaneRectangularZone.ZONE_5:
                return self._east_longitude(134, 20)
            case JapanPlaneRectangularZone.ZONE_6:
                return self._east_longitude(136, 0)
            case JapanPlaneRectangularZone.ZONE_7:
                return self._east_longitude(137, 10)
            case JapanPlaneRectangularZone.ZONE_8:
                return self._east_longitude(138, 30)
            case JapanPlaneRectangularZone.ZONE_9:
                return self._east_longitude(139, 50)
            case JapanPlaneRectangularZone.ZONE_10:
                return self._east_longitude(140, 50)
            case JapanPlaneRectangularZone.ZONE_11:
                return self._east_longitude(140, 15)
            case JapanPlaneRectangularZone.ZONE_12:
                return self._east_longitude(142, 15)
            case JapanPlaneRectangularZone.ZONE_13:
                return self._east_longitude(144, 15)
            case JapanPlaneRectangularZone.ZONE_14:
                return self._east_longitude(142, 0)
            case JapanPlaneRectangularZone.ZONE_15:
                return self._east_longitude(127, 30)
            case JapanPlaneRectangularZone.ZONE_16:
                return self._east_longitude(124, 0)
            case JapanPlaneRectangularZone.ZONE_17:
                return self._east_longitude(131, 0)
            case JapanPlaneRectangularZone.ZONE_18:
                return self._east_longitude(136, 0)
            case JapanPlaneRectangularZone.ZONE_19:
                return self._east_longitude(154, 0)

    @staticmethod
    def _east_longitude(degrees: int, minutes: int) -> Angle:
        return Angle.from_degrees_minutes_seconds(
            DegreesMinutesSeconds(
                degrees=np.array([float(degrees)]),
                minutes=np.array([float(minutes)]),
                seconds=np.zeros(1),
                is_negative=np.zeros(1, dtype=np.bool_),
            )
        )

    def __str__(self) -> str:
        return f"EPSG:{self.value}"
