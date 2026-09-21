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
