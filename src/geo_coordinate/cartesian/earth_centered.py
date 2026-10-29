from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from units import Length, LengthUnit


@dataclass(frozen=True, eq=False)
class EarthCenteredCoordinates:
    """
    Earth-centred, Earth-fixed (ECEF) Cartesian coordinates, in meters.

    The origin is the centre of the ellipsoid, X points to latitude 0 and longitude 0,
    Y to latitude 0 and longitude 90 east, and Z to the North Pole.

    Parameters
    ----------
    x : NDArray[np.float64]
        The X coordinates in meters, of shape (N,).
    y : NDArray[np.float64]
        The Y coordinates in meters, of shape (N,).
    z : NDArray[np.float64]
        The Z coordinates in meters, of shape (N,).

    Raises
    ------
    ValueError
        If the arrays are not 1D of the same shape or are not finite.
    """

    x: NDArray[np.float64]
    y: NDArray[np.float64]
    z: NDArray[np.float64]

    def __post_init__(self) -> None:
        if self.x.ndim != 1 or self.x.shape != self.y.shape or self.x.shape != self.z.shape:
            raise ValueError(
                "x, y and z must be 1D arrays of the same shape, "
                + f"given: {self.x.shape}, {self.y.shape} and {self.z.shape}"
            )
        if not np.all(np.isfinite(self.points)):
            raise ValueError("x, y and z must be finite")

    @classmethod
    def from_points(cls, points: NDArray[np.float64]) -> EarthCenteredCoordinates:
        """
        Build coordinates from an array of X, Y and Z.

        Parameters
        ----------
        points : NDArray[np.float64]
            The coordinates in meters, of shape (N, 3).

        Returns
        -------
        EarthCenteredCoordinates
            The coordinates.

        Raises
        ------
        ValueError
            If `points` is not of shape (N, 3).
        """
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError(f"points must be of shape (N, 3): {points.shape}")
        return cls(
            x=points[:, 0].astype(np.float64),
            y=points[:, 1].astype(np.float64),
            z=points[:, 2].astype(np.float64),
        )

    @property
    def points(self) -> NDArray[np.float64]:
        """
        Return X, Y and Z stacked as columns.

        Returns
        -------
        NDArray[np.float64]
            The coordinates in meters, of shape (N, 3).
        """
        return np.column_stack([self.x, self.y, self.z]).astype(np.float64)

    def distance_to(self, other: EarthCenteredCoordinates) -> Length:
        """
        Straight-line distances through space, element-wise.

        Unlike a distance along the surface, this includes the heights and cuts
        through the Earth, as a line of sight or a radio link does.

        Parameters
        ----------
        other : EarthCenteredCoordinates
            The coordinates to measure to. Either side may hold a single point, which
            is broadcast against the other.

        Returns
        -------
        Length
            The distances in meters.

        Raises
        ------
        ValueError
            If both sides hold more than one point and differ in length.
        """
        if len(self) != 1 and len(other) != 1 and len(self) != len(other):
            raise ValueError(
                "points must have the same length or a single element, "
                + f"given: {len(self)} and {len(other)}"
            )
        distance: NDArray[np.float64] = np.linalg.norm(other.points - self.points, axis=1)
        return Length(value=distance, unit=LengthUnit.M)

    def __len__(self) -> int:
        return len(self.x)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EarthCenteredCoordinates):
            return False
        return self.x.shape == other.x.shape and bool(np.allclose(self.points, other.points))

    def __repr__(self) -> str:
        return f"EarthCenteredCoordinates(x={self.x}, y={self.y}, z={self.z})"
