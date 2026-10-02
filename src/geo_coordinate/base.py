from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from units import Angle, Length, LengthUnit, NumericArray

from .altitude import Altitude


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
        if len(self) != len(other) and 1 not in (len(self), len(other)):
            raise ValueError(
                "coordinates must have the same length or a single element, "
                + f"given: {len(self)} and {len(other)}"
            )
        return self._surface_distance(
            self.latitude.radian,
            self.longitude.radian,
            other.latitude.radian,
            other.longitude.radian,
        )

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
