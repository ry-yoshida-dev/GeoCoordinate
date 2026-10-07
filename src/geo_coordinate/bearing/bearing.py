from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from units import Angle, AngleUnit, NumericArray

from .north_reference import NorthReference


@dataclass(frozen=True)
class Bearing:
    """
    Horizontal directions measured clockwise from north, stored as a 1D array.

    A bearing is meaningful only with the north it is measured from: a compass and
    the magnetometer of a camera measure from magnetic north, while great circles
    and maps are measured from true north.

    Parameters
    ----------
    angle : Angle
        The directions, within [0, 360) degrees.
    reference : NorthReference
        The north the directions are measured from.

    Raises
    ------
    ValueError
        If the angles are not a 1D array, or an angle is not finite or lies
        outside [0, 360) degrees.
    """

    angle: Angle
    reference: NorthReference = NorthReference.TRUE

    FULL_TURN_DEGREE: ClassVar[float] = 360.0

    def __post_init__(self) -> None:
        if self.angle.value.ndim != 1:
            raise ValueError("bearing must be a 1D array")
        degree = self.angle.degree
        if not np.all(np.isfinite(degree)):
            raise ValueError("bearing must be finite")
        if np.any(degree < 0) or np.any(degree >= self.FULL_TURN_DEGREE):
            raise ValueError("bearing must be within [0, 360) degrees")

    @classmethod
    def wrapped(cls, angle: Angle, reference: NorthReference = NorthReference.TRUE) -> Bearing:
        """
        Build bearings from any finite angles, turning them into [0, 360) degrees.

        Parameters
        ----------
        angle : Angle
            The directions clockwise from north, such as -90 or 360 degrees.
        reference : NorthReference
            The north the directions are measured from.

        Returns
        -------
        Bearing
            The same directions in degrees, with -90 as 270 and 360 as 0.

        Raises
        ------
        ValueError
            If an angle is not finite.
        """
        wrapped_degree = np.mod(angle.degree, cls.FULL_TURN_DEGREE)
        degree: NumericArray = np.where(wrapped_degree >= cls.FULL_TURN_DEGREE, 0.0, wrapped_degree)
        return cls(angle=Angle(value=degree, unit=AngleUnit.DEGREE), reference=reference)

    @classmethod
    def from_degrees(
        cls, degree: float, reference: NorthReference = NorthReference.TRUE
    ) -> Bearing:
        """
        Build a single bearing from decimal degrees, wrapped into [0, 360).

        Parameters
        ----------
        degree : float
            The direction clockwise from north.
        reference : NorthReference
            The north the direction is measured from.

        Returns
        -------
        Bearing
            A bearing of one element.

        Raises
        ------
        ValueError
            If `degree` is not finite.
        """
        return cls.wrapped(Angle(value=np.array([degree]), unit=AngleUnit.DEGREE), reference)

    @property
    def degree(self) -> NumericArray:
        """
        Return the directions in degrees.

        Returns
        -------
        NumericArray
            The directions within [0, 360).
        """
        return self.angle.degree

    @property
    def radian(self) -> NumericArray:
        """
        Return the directions in radians.

        Returns
        -------
        NumericArray
            The directions within [0, 2π).
        """
        return self.angle.radian

    @property
    def is_true_north(self) -> bool:
        """
        Whether the directions are measured from true north.

        Returns
        -------
        bool
            True for `NorthReference.TRUE`.
        """
        return self.reference is NorthReference.TRUE

    def __len__(self) -> int:
        return len(self.angle)
