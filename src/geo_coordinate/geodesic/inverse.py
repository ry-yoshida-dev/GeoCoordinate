from __future__ import annotations

from dataclasses import dataclass

from units import Length

from ..bearing import Bearing


@dataclass(frozen=True)
class GeodesicInverse:
    """
    Solution of the inverse geodesic problem between pairs of places.

    Parameters
    ----------
    distance : Length
        The lengths of the geodesics on the ellipsoid, in meters.
    initial_bearing : Bearing
        The bearings from true north at the start of each geodesic.
    final_bearing : Bearing
        The bearings from true north at the end of each geodesic, facing onwards.
    """

    distance: Length
    initial_bearing: Bearing
    final_bearing: Bearing
