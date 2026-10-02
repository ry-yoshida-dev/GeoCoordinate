from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from units import Angle, AngleUnit

from .altitude import Altitude
from .base import GeoCoordinateBase


@dataclass(eq=False, repr=False)
class GeoCoordinate(GeoCoordinateBase):
    """
    A single geographic coordinate on the Earth.

    The latitude, longitude and optional altitude each hold exactly one
    element, so the coordinate broadcasts against a `GeoCoordinates` batch.

    Parameters
    ----------
    latitude : Angle
        The latitude, positive north of the equator, within [-90, 90] degrees.
    longitude : Angle
        The longitude, positive east of the prime meridian, within [-180, 180] degrees.
    altitude : Altitude | None
        The height relative to mean sea level, or None when unknown.
    """

    def _validate_length(self) -> None:
        if len(self) != 1:
            raise ValueError(f"GeoCoordinate must hold exactly one element, given: {len(self)}")

    @classmethod
    def from_degrees(
        cls,
        latitude: float,
        longitude: float,
        altitude: Altitude | None = None,
    ) -> GeoCoordinate:
        """
        Build a coordinate from a latitude and longitude in decimal degrees.

        Parameters
        ----------
        latitude : float
            The latitude in degrees.
        longitude : float
            The longitude in degrees.
        altitude : Altitude | None
            The height relative to mean sea level, or None when unknown.

        Returns
        -------
        GeoCoordinate
            The coordinate.
        """
        return cls(
            latitude=Angle(value=np.array([latitude]), unit=AngleUnit.DEGREE),
            longitude=Angle(value=np.array([longitude]), unit=AngleUnit.DEGREE),
            altitude=altitude,
        )
