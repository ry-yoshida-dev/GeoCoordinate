from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from units import Angle, AngleUnit, Length, LengthUnit

from ..bearing import Bearing


@dataclass(frozen=True, eq=False)
class EastNorthUp:
    """
    Cartesian coordinates in a local tangent plane, in meters.

    East and north span the plane tangent to the ellipsoid at the origin, and up
    follows its normal. The frame suits short ranges such as a drone flight or a
    construction site, where the curvature of the Earth may be ignored around the
    origin.

    Parameters
    ----------
    east : NDArray[np.float64]
        The distances east of the origin in meters, of shape (N,).
    north : NDArray[np.float64]
        The distances north of the origin in meters, of shape (N,).
    up : NDArray[np.float64]
        The distances above the tangent plane in meters, of shape (N,).

    Raises
    ------
    ValueError
        If the arrays are not 1D of the same shape or are not finite.
    """

    east: NDArray[np.float64]
    north: NDArray[np.float64]
    up: NDArray[np.float64]

    def __post_init__(self) -> None:
        if (
            self.east.ndim != 1
            or self.east.shape != self.north.shape
            or self.east.shape != self.up.shape
        ):
            raise ValueError(
                "east, north and up must be 1D arrays of the same shape, "
                + f"given: {self.east.shape}, {self.north.shape} and {self.up.shape}"
            )
        if not np.all(np.isfinite(self.points)):
            raise ValueError("east, north and up must be finite")

    @classmethod
    def from_points(cls, points: NDArray[np.float64]) -> EastNorthUp:
        """
        Build coordinates from an array of east, north and up.

        Parameters
        ----------
        points : NDArray[np.float64]
            The coordinates in meters, of shape (N, 3).

        Returns
        -------
        EastNorthUp
            The coordinates.

        Raises
        ------
        ValueError
            If `points` is not of shape (N, 3).
        """
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError(f"points must be of shape (N, 3): {points.shape}")
        return cls(
            east=points[:, 0].astype(np.float64),
            north=points[:, 1].astype(np.float64),
            up=points[:, 2].astype(np.float64),
        )

    @property
    def points(self) -> NDArray[np.float64]:
        """
        Return east, north and up stacked as columns.

        Returns
        -------
        NDArray[np.float64]
            The coordinates in meters, of shape (N, 3).
        """
        return np.column_stack([self.east, self.north, self.up]).astype(np.float64)

    @property
    def horizontal_distance(self) -> Length:
        """
        Return the distances from the origin within the tangent plane.

        Returns
        -------
        Length
            `hypot(east, north)` in meters.
        """
        return Length(value=np.hypot(self.east, self.north), unit=LengthUnit.M)

    @property
    def slant_range(self) -> Length:
        """
        Return the straight-line distances from the origin.

        Returns
        -------
        Length
            The norm of east, north and up in meters.
        """
        return Length(value=np.linalg.norm(self.points, axis=1), unit=LengthUnit.M)

    @property
    def azimuth(self) -> Bearing:
        """
        Return the directions from the origin, clockwise from true north.

        Returns
        -------
        Bearing
            The azimuths in degrees within [0, 360), zero straight above the origin.
        """
        degree: NDArray[np.float64] = np.degrees(np.arctan2(self.east, self.north))
        return Bearing.wrapped(Angle(value=degree, unit=AngleUnit.DEGREE))

    @property
    def elevation_angle(self) -> Angle:
        """
        Return the angles above the tangent plane, as seen from the origin.

        Returns
        -------
        Angle
            The angles in degrees within [-90, 90], positive above the horizon and
            zero at the origin itself.
        """
        degree: NDArray[np.float64] = np.degrees(
            np.arctan2(self.up, np.hypot(self.east, self.north))
        )
        return Angle(value=degree, unit=AngleUnit.DEGREE)

    def __len__(self) -> int:
        return len(self.east)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EastNorthUp):
            return False
        return self.east.shape == other.east.shape and bool(np.allclose(self.points, other.points))

    def __repr__(self) -> str:
        return f"EastNorthUp(east={self.east}, north={self.north}, up={self.up})"
