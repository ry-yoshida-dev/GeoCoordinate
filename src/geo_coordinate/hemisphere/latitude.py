from __future__ import annotations

from enum import Enum


class LatitudeHemisphere(Enum):
    """
    Hemisphere a latitude is measured in, abbreviated as in `35°40'30"N`.

    Attributes
    ----------
    NORTH
        North of the equator.
    SOUTH
        South of the equator.
    """

    NORTH = "N"
    SOUTH = "S"

    @classmethod
    def from_is_negative(cls, is_negative: bool) -> LatitudeHemisphere:
        """
        Return the hemisphere of a signed value from its sign.

        Parameters
        ----------
        is_negative : bool
            Whether the signed value is negative.

        Returns
        -------
        LatitudeHemisphere
            `SOUTH` for negative values, `NORTH` otherwise.
        """
        match is_negative:
            case True:
                return cls.SOUTH
            case False:
                return cls.NORTH

    @property
    def is_negative(self) -> bool:
        """
        Whether a latitude measured in this hemisphere is negative.

        Returns
        -------
        bool
            True for `SOUTH`.
        """
        match self:
            case LatitudeHemisphere.NORTH:
                return False
            case LatitudeHemisphere.SOUTH:
                return True
