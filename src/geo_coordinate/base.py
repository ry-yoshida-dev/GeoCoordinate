from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Self

import numpy as np
from units import Angle, AngleUnit, Length, LengthUnit, NumericArray

from .altitude import Altitude
from .bearing import Bearing
from .sexagesimal import SexagesimalNotation, SexagesimalText


@dataclass(eq=False)
class GeoCoordinateBase(ABC):
    """
    Abstract geographic coordinates on the Earth, stored as 1D arrays.

    Subclasses decide how many coordinates the arrays may hold.

    Parameters
    ----------
    latitude : Angle
        The latitudes, positive north of the equator, within [-90, 90] degrees.
    longitude : Angle
        The longitudes, positive east of the prime meridian, within [-180, 180] degrees.
    altitude : Altitude | None
        The heights relative to mean sea level, or None when unknown.
    """

    latitude: Angle
    longitude: Angle
    altitude: Altitude | None = None

    EARTH_MEAN_RADIUS: ClassVar[Length] = Length(value=np.array([6_371_008.8]), unit=LengthUnit.M)

    def __post_init__(self) -> None:
        if len(self.latitude) != len(self.longitude):
            raise ValueError(
                "latitude and longitude must have the same length, "
                + f"given: {len(self.latitude)} and {len(self.longitude)}"
            )
        if self.altitude is not None and len(self.altitude) != len(self.latitude):
            raise ValueError(
                "altitude must have the same length as latitude, "
                + f"given: {len(self.altitude)} and {len(self.latitude)}"
            )
        if not np.all(np.isfinite(self.latitude.degree)):
            raise ValueError("latitude must be finite")
        if not np.all(np.isfinite(self.longitude.degree)):
            raise ValueError("longitude must be finite")
        if np.any(np.abs(self.latitude.degree) > 90):
            raise ValueError("latitude must be within [-90, 90] degrees")
        if np.any(np.abs(self.longitude.degree) > 180):
            raise ValueError("longitude must be within [-180, 180] degrees")
        self._validate_length()

    @abstractmethod
    def _validate_length(self) -> None:
        """
        Validate the number of coordinates held by this instance.

        Raises
        ------
        ValueError
            If the number of coordinates is not allowed by the subclass.
        """

    def distance_to(self, other: GeoCoordinateBase) -> Length:
        """
        Great-circle distance along the surface, by the haversine formula.

        The Earth is approximated as a sphere of `EARTH_MEAN_RADIUS`, which
        keeps the error within about 0.5 percent. Altitudes are ignored.

        Parameters
        ----------
        other : GeoCoordinateBase
            The coordinates to measure to, element-wise. Either side may hold
            a single coordinate, which is broadcast against the other.

        Returns
        -------
        Length
            The distances in meters.

        Raises
        ------
        ValueError
            If both sides hold more than one coordinate and differ in length.
        """
        self._broadcast_length({"coordinates": len(self), "other": len(other)})
        return self._surface_distance(
            self.latitude.radian,
            self.longitude.radian,
            other.latitude.radian,
            other.longitude.radian,
        )

    def initial_bearing_to(self, other: GeoCoordinateBase) -> Bearing:
        """
        Initial bearing of the great circle towards `other`, clockwise from north.

        The bearing changes along a great circle, so this is the heading at
        the start. Coincident coordinates have a bearing of zero.

        Parameters
        ----------
        other : GeoCoordinateBase
            The coordinates to head to, element-wise. Either side may hold a
            single coordinate, which is broadcast against the other.

        Returns
        -------
        Bearing
            The bearings from true north, in degrees within [0, 360).

        Raises
        ------
        ValueError
            If both sides hold more than one coordinate and differ in length.
        """
        self._broadcast_length({"coordinates": len(self), "other": len(other)})
        return self._initial_bearing(
            self.latitude.radian,
            self.longitude.radian,
            other.latitude.radian,
            other.longitude.radian,
        )

    def destination(self, bearing: Bearing, distance: Length) -> Self:
        """
        Coordinates reached by travelling along a great circle.

        The altitudes, if any, are carried over unchanged.

        Parameters
        ----------
        bearing : Bearing
            The initial bearings, clockwise from true north.
        distance : Length
            The distances to travel along the surface.

        Returns
        -------
        Self
            The destinations, with angles in degrees and longitudes within
            [-180, 180). Each argument may hold a single element, which is
            broadcast against the others.

        Raises
        ------
        ValueError
            If the bearings are measured from magnetic north, whose offset from
            true north is not known here, if the arguments hold more than one
            element and differ in length, or if the destinations do not fit this
            coordinate type.
        """
        if not bearing.is_true_north:
            raise ValueError("destination requires bearings measured from true north")
        length: int = self._broadcast_length(
            {
                "coordinates": len(self),
                "bearing": len(bearing),
                "distance": len(distance.value),
            }
        )
        latitude_from = self.latitude.radian
        angular_distance = distance.meter / self.EARTH_MEAN_RADIUS.meter
        latitude_to = np.arcsin(
            np.clip(
                np.sin(latitude_from) * np.cos(angular_distance)
                + np.cos(latitude_from) * np.sin(angular_distance) * np.cos(bearing.radian),
                -1,
                1,
            )
        )
        longitude_to = self.longitude.radian + np.arctan2(
            np.sin(bearing.radian) * np.sin(angular_distance) * np.cos(latitude_from),
            np.cos(angular_distance) - np.sin(latitude_from) * np.sin(latitude_to),
        )
        longitude_degree: NumericArray = np.mod(np.degrees(longitude_to) + 180, 360) - 180
        latitude_degree: NumericArray = np.degrees(latitude_to)
        altitude: Altitude | None = None
        if self.altitude is not None:
            altitude = Altitude(
                value=np.broadcast_to(self.altitude.value, (length,)).copy(),
                unit=self.altitude.unit,
            )
        return type(self)(
            latitude=Angle(value=latitude_degree, unit=AngleUnit.DEGREE),
            longitude=Angle(value=longitude_degree, unit=AngleUnit.DEGREE),
            altitude=altitude,
        )

    def to_sexagesimal(self, seconds_decimals: int = 2) -> SexagesimalText:
        """
        Write the coordinates in degrees, minutes, seconds and hemisphere letters.

        Altitudes are not written.

        Parameters
        ----------
        seconds_decimals : int
            The number of decimals of the seconds, within [0, 6].

        Returns
        -------
        SexagesimalText
            The latitudes and longitudes, such as `35°40'52.27"N` and
            `139°46'1.56"E`.

        Raises
        ------
        ValueError
            If `seconds_decimals` is outside [0, 6].
        """
        return SexagesimalText(
            latitude=SexagesimalNotation.format_latitudes(self.latitude, seconds_decimals),
            longitude=SexagesimalNotation.format_longitudes(self.longitude, seconds_decimals),
        )

    @staticmethod
    def _broadcast_length(lengths: dict[str, int]) -> int:
        """
        Length that arrays of the given lengths broadcast to.

        Parameters
        ----------
        lengths : dict[str, int]
            The lengths of the arrays, keyed by the names used in errors.

        Returns
        -------
        int
            The common length other than one, or one if all lengths are one.

        Raises
        ------
        ValueError
            If more than one distinct length other than one is given.
        """
        distinct_lengths: set[int] = {length for length in lengths.values() if length != 1}
        if len(distinct_lengths) > 1:
            given: str = ", ".join(f"{name}={length}" for name, length in lengths.items())
            raise ValueError(
                f"{', '.join(lengths)} must have the same length or a single element, "
                + f"given: {given}"
            )
        return distinct_lengths.pop() if distinct_lengths else 1

    @staticmethod
    def _initial_bearing(
        latitude_from: NumericArray,
        longitude_from: NumericArray,
        latitude_to: NumericArray,
        longitude_to: NumericArray,
    ) -> Bearing:
        """
        Initial great-circle bearing between broadcastable arrays of radians.

        Parameters
        ----------
        latitude_from : NumericArray
            The latitudes of the start points in radians.
        longitude_from : NumericArray
            The longitudes of the start points in radians.
        latitude_to : NumericArray
            The latitudes of the end points in radians.
        longitude_to : NumericArray
            The longitudes of the end points in radians.

        Returns
        -------
        Bearing
            The bearings from true north in degrees within [0, 360), in the
            broadcast shape of the inputs.
        """
        longitude_difference = longitude_to - longitude_from
        east_component = np.sin(longitude_difference) * np.cos(latitude_to)
        north_component = np.cos(latitude_from) * np.sin(latitude_to) - (
            np.sin(latitude_from) * np.cos(latitude_to) * np.cos(longitude_difference)
        )
        bearing_degree: NumericArray = np.degrees(np.arctan2(east_component, north_component))
        return Bearing.wrapped(Angle(value=bearing_degree, unit=AngleUnit.DEGREE))

    @classmethod
    def _surface_distance(
        cls,
        latitude_from: NumericArray,
        longitude_from: NumericArray,
        latitude_to: NumericArray,
        longitude_to: NumericArray,
    ) -> Length:
        """
        Haversine distance between broadcastable arrays of radians.

        Parameters
        ----------
        latitude_from : NumericArray
            The latitudes of the start points in radians.
        longitude_from : NumericArray
            The longitudes of the start points in radians.
        latitude_to : NumericArray
            The latitudes of the end points in radians.
        longitude_to : NumericArray
            The longitudes of the end points in radians.

        Returns
        -------
        Length
            The distances in meters, in the broadcast shape of the inputs.
        """
        haversine = (
            np.sin((latitude_to - latitude_from) / 2) ** 2
            + np.cos(latitude_from)
            * np.cos(latitude_to)
            * np.sin((longitude_to - longitude_from) / 2) ** 2
        )
        central_angle = 2 * np.arcsin(np.sqrt(np.clip(haversine, 0, 1)))
        distance: NumericArray = central_angle * cls.EARTH_MEAN_RADIUS.meter
        return Length(value=distance, unit=LengthUnit.M)

    def __len__(self) -> int:
        return len(self.latitude)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return (
            self.latitude == other.latitude
            and self.longitude == other.longitude
            and self.altitude == other.altitude
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(latitude={self.latitude.degree} degree, "
            + f"longitude={self.longitude.degree} degree, altitude={self.altitude})"
        )
