from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ..coordinates import GeoCoordinates


@dataclass(frozen=True, eq=False)
class GeodeticPosition:
    """
    Places in space given by latitude, longitude and height above the ellipsoid.

    The height is measured along the normal of the ellipsoid, as GNSS gives it, not
    above mean sea level as an `Altitude` is; a `Geoid` converts between the two.

    Parameters
    ----------
    coordinates : GeoCoordinates
        The latitudes and longitudes, without altitudes.
    ellipsoidal_height : NDArray[np.float64]
        The heights above the ellipsoid in meters, of shape (N,).

    Raises
    ------
    ValueError
        If the heights differ in length from the coordinates or are not finite.
    """

    coordinates: GeoCoordinates
    ellipsoidal_height: NDArray[np.float64]

    def __post_init__(self) -> None:
        if self.ellipsoidal_height.shape != (len(self.coordinates),):
            raise ValueError(
                f"ellipsoidal_height must be of shape ({len(self.coordinates)},), "
                + f"given: {self.ellipsoidal_height.shape}"
            )
        if not np.all(np.isfinite(self.ellipsoidal_height)):
            raise ValueError("ellipsoidal_height must be finite")

    def __len__(self) -> int:
        return len(self.coordinates)
