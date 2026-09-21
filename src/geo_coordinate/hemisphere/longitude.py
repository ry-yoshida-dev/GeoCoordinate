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
