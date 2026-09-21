from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from units import Angle, AngleUnit, Length, LengthUnit, NumericArray

from .altitude import Altitude


@dataclass(eq=False)
class GeoCoordinate:
    """
    Container class for geographic coordinates on the Earth.

    Holds one coordinate per array element, so a batch of locations is
    processed with vectorized operations.

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
        if np.any(np.abs(self.latitude.degree) > 90):
            raise ValueError("latitude must be within [-90, 90] degrees")
        if np.any(np.abs(self.longitude.degree) > 180):
            raise ValueError("longitude must be within [-180, 180] degrees")

    @classmethod
    def from_degrees(
        cls,
        latitude: NumericArray,
        longitude: NumericArray,
        altitude: Altitude | None = None,
    ) -> GeoCoordinate:
        """
        Build coordinates from latitudes and longitudes in decimal degrees.

        Parameters
        ----------
        latitude : NumericArray
            The latitudes in degrees.
        longitude : NumericArray
            The longitudes in degrees.
        altitude : Altitude | None
            The heights relative to mean sea level, or None when unknown.

        Returns
        -------
        GeoCoordinate
            The coordinates.
        """
        return cls(
            latitude=Angle(value=latitude, unit=AngleUnit.DEGREE),
            longitude=Angle(value=longitude, unit=AngleUnit.DEGREE),
            altitude=altitude,
        )

    def distance_to(self, other: GeoCoordinate) -> Length:
        """
        Great-circle distance along the surface, by the haversine formula.

        The Earth is approximated as a sphere of `EARTH_MEAN_RADIUS`, which
        keeps the error within about 0.5 percent. Altitudes are ignored.

        Parameters
        ----------
        other : GeoCoordinate
            The coordinates to measure to, element-wise. Either side may hold
            a single coordinate, which is broadcast against the other.

        Returns
        -------
        Length
            The distances in meters.
        """
        latitude_difference = other.latitude.radian - self.latitude.radian
        longitude_difference = other.longitude.radian - self.longitude.radian
        haversine = (
            np.sin(latitude_difference / 2) ** 2
            + np.cos(self.latitude.radian)
            * np.cos(other.latitude.radian)
            * np.sin(longitude_difference / 2) ** 2
        )
        central_angle = 2 * np.arcsin(np.sqrt(np.clip(haversine, 0, 1)))
        distance: NumericArray = central_angle * self.EARTH_MEAN_RADIUS.meter
        return Length(value=distance, unit=LengthUnit.M)

    def __len__(self) -> int:
        return len(self.latitude)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoCoordinate):
            return False
        return (
            self.latitude == other.latitude
            and self.longitude == other.longitude
            and self.altitude == other.altitude
        )

    def __repr__(self) -> str:
        return (
            f"GeoCoordinate(latitude={self.latitude.degree} degree, "
            + f"longitude={self.longitude.degree} degree, altitude={self.altitude})"
        )
