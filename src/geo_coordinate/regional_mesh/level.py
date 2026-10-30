from __future__ import annotations

from enum import Enum
from fractions import Fraction


class RegionalMeshLevel(Enum):
    """
    The levels of the regional meshes of JIS X 0410 and their divisions into halves.

    Each member is the number of digits of its codes. A mesh of the first level spans
    40 minutes of latitude and 1 degree of longitude; the second level divides it into
    8 by 8, the third into 10 by 10 again, and the half, quarter and eighth levels each
    halve the one above in both directions.

    Attributes
    ----------
    FIRST
        第1次地域区画, about 80 km.
    SECOND
        第2次地域区画, about 10 km.
    THIRD
        基準地域メッシュ (第3次地域区画), about 1 km.
    HALF
        2分の1地域メッシュ, about 500 m.
    QUARTER
        4分の1地域メッシュ, about 250 m.
    EIGHTH
        8分の1地域メッシュ, about 125 m.
    """

    FIRST = 4
    SECOND = 6
    THIRD = 8
    HALF = 9
    QUARTER = 10
    EIGHTH = 11

    @classmethod
    def from_code_length(cls, length: int) -> RegionalMeshLevel:
        """
        Return the level whose codes have a number of digits.

        Parameters
        ----------
        length : int
            The number of digits of a code.

        Returns
        -------
        RegionalMeshLevel
            The level.

        Raises
        ------
        ValueError
            If no level has codes of that many digits.
        """
        level = next((level for level in cls if level.value == length), None)
        if level is None:
            raise ValueError(f"No regional mesh level has codes of {length} digits")
        return level

    @property
    def label(self) -> str:
        """
        Return the name JIS X 0410 and the statistics of Japan give the level.

        Returns
        -------
        str
            The name, such as `基準地域メッシュ`.
        """
        match self:
            case RegionalMeshLevel.FIRST:
                return "第1次地域区画"
            case RegionalMeshLevel.SECOND:
                return "第2次地域区画"
            case RegionalMeshLevel.THIRD:
                return "基準地域メッシュ"
            case RegionalMeshLevel.HALF:
                return "2分の1地域メッシュ"
            case RegionalMeshLevel.QUARTER:
                return "4分の1地域メッシュ"
            case RegionalMeshLevel.EIGHTH:
                return "8分の1地域メッシュ"

    @property
    def latitude_span(self) -> Fraction:
        """
        Return the extent of a mesh from south to north.

        Returns
        -------
        Fraction
            The extent in degrees, exact.
        """
        match self:
            case RegionalMeshLevel.FIRST:
                return Fraction(2, 3)
            case RegionalMeshLevel.SECOND:
                return Fraction(1, 12)
            case RegionalMeshLevel.THIRD:
                return Fraction(1, 120)
            case RegionalMeshLevel.HALF:
                return Fraction(1, 240)
            case RegionalMeshLevel.QUARTER:
                return Fraction(1, 480)
            case RegionalMeshLevel.EIGHTH:
                return Fraction(1, 960)

    @property
    def longitude_span(self) -> Fraction:
        """
        Return the extent of a mesh from west to east.

        Returns
        -------
        Fraction
            The extent in degrees, exact.
        """
        match self:
            case RegionalMeshLevel.FIRST:
                return Fraction(1)
            case RegionalMeshLevel.SECOND:
                return Fraction(1, 8)
            case RegionalMeshLevel.THIRD:
                return Fraction(1, 80)
            case RegionalMeshLevel.HALF:
                return Fraction(1, 160)
            case RegionalMeshLevel.QUARTER:
                return Fraction(1, 320)
            case RegionalMeshLevel.EIGHTH:
                return Fraction(1, 640)

    @property
    def parent(self) -> RegionalMeshLevel | None:
        """
        Return the level a mesh of this level divides.

        Returns
        -------
        RegionalMeshLevel | None
            The coarser level, or None for the first level.
        """
        match self:
            case RegionalMeshLevel.FIRST:
                return None
            case RegionalMeshLevel.SECOND:
                return RegionalMeshLevel.FIRST
            case RegionalMeshLevel.THIRD:
                return RegionalMeshLevel.SECOND
            case RegionalMeshLevel.HALF:
                return RegionalMeshLevel.THIRD
            case RegionalMeshLevel.QUARTER:
                return RegionalMeshLevel.HALF
            case RegionalMeshLevel.EIGHTH:
                return RegionalMeshLevel.QUARTER

    @property
    def child(self) -> RegionalMeshLevel | None:
        """
        Return the level that divides a mesh of this level.

        Returns
        -------
        RegionalMeshLevel | None
            The finer level, or None for the eighth level.
        """
        return next((level for level in RegionalMeshLevel if level.parent is self), None)

    @property
    def divisions(self) -> int:
        """
        Return how many parts the parent level is divided into along each direction.

        Returns
        -------
        int
            8 for the second level, 10 for the third, 2 for the half, quarter and
            eighth levels, and 1 for the first level, which divides nothing.
        """
        parent = self.parent
        if parent is None:
            return 1
        return int(parent.latitude_span / self.latitude_span)
