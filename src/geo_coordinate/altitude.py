from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray
from units import Length, LengthUnit, NumericArray


@dataclass(eq=False)
class Altitude:
    """
    Container class for signed heights relative to mean sea level.

    Unlike `units.Length`, which only holds magnitudes, the value is signed:
    positive above sea level and negative below it.

    Parameters
    ----------
    value : NumericArray
        The signed heights, one per coordinate.
    unit : LengthUnit
        The unit of `value`.
    """

    value: NumericArray
    unit: LengthUnit

    EQUALITY_TOLERANCE_METER: ClassVar[float] = 1e-9

    def __post_init__(self) -> None:
        if self.value.ndim != 1:
            raise ValueError("Altitude must be a 1D array")
        if not np.all(np.isfinite(self.value)):
            raise ValueError("Altitude must be finite")

    @classmethod
    def from_magnitude(cls, magnitude: Length, is_below_sea_level: NDArray[np.bool_]) -> Altitude:
        """
        Build altitudes from unsigned heights and the side of sea level they lie on.

        Parameters
        ----------
        magnitude : Length
            The distances from sea level.
        is_below_sea_level : NDArray[np.bool_]
            Whether each height lies below sea level.

        Returns
        -------
        Altitude
            The signed altitudes, in the unit of `magnitude`.

        Raises
        ------
        ValueError
            If `magnitude` and `is_below_sea_level` differ in shape.
        """
        if magnitude.value.shape != is_below_sea_level.shape:
            raise ValueError(
                "magnitude and is_below_sea_level must have the same shape, "
                + f"given: {magnitude.value.shape} and {is_below_sea_level.shape}"
            )
        signed_value: NumericArray = np.where(is_below_sea_level, -magnitude.value, magnitude.value)
        return cls(value=signed_value, unit=magnitude.unit)

    @property
    def meter(self) -> NumericArray:
        """
        Return the signed altitudes in meters.

        Returns
        -------
        NumericArray
            The altitudes in meters.
        """
        return self.value * self.unit.to_meter

    @property
    def magnitude(self) -> Length:
        """
        Return the distances from sea level.

        Returns
        -------
        Length
            The unsigned heights, in the unit of this altitude.
        """
        return Length(value=np.abs(self.value), unit=self.unit)

    @property
    def is_below_sea_level(self) -> NDArray[np.bool_]:
        """
        Return whether each altitude lies below sea level.

        Returns
        -------
        NDArray[np.bool_]
            True for negative altitudes.
        """
        return np.less(self.value, 0)

    def __len__(self) -> int:
        return len(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Altitude):
            return False
        return self.value.shape == other.value.shape and bool(
            np.allclose(self.meter, other.meter, atol=self.EQUALITY_TOLERANCE_METER)
        )

    def __repr__(self) -> str:
        return f"Altitude(value={self.value}, unit={self.unit})"
