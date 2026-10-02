from __future__ import annotations

from enum import Enum


class LongitudeHemisphere(Enum):
    """
    Hemisphere a longitude is measured in, abbreviated as in `139°45'0"E`.

    Attributes
    ----------
    EAST
        East of the prime meridian.
    WEST
        West of the prime meridian.
    """

    EAST = "E"
    WEST = "W"

    @classmethod
    def from_is_negative(cls, is_negative: bool) -> LongitudeHemisphere:
        """
        Return the hemisphere of a signed value from its sign.

        Parameters
        ----------
        is_negative : bool
            Whether the signed value is negative.

        Returns
        -------
        LongitudeHemisphere
            `WEST` for negative values, `EAST` otherwise.
        """
        match is_negative:
            case True:
                return cls.WEST
            case False:
                return cls.EAST

    @property
    def is_negative(self) -> bool:
        """
        Whether a longitude measured in this hemisphere is negative.

        Returns
        -------
        bool
            True for `WEST`.
        """
        match self:
            case LongitudeHemisphere.EAST:
                return False
            case LongitudeHemisphere.WEST:
                return True
