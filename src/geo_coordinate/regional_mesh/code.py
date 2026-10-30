from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from ..coordinate import GeoCoordinate
from .bounds import RegionalMeshBounds
from .level import RegionalMeshLevel

FIRST_LEVEL_WEST_ORIGIN: Final[int] = 100
FIRST_LEVEL_INDEX_LIMIT: Final[int] = 100
QUADRANT_DIGIT_OFFSET: Final[int] = 1


@dataclass(frozen=True)
class RegionalMeshCode:
    """
    The code of a regional mesh of JIS X 0410, such as `53393599` or `533935991`.

    The first two digits are the latitude of the first level mesh times 1.5, and the next
    two its longitude less 100. The second and third levels each add a digit of the row,
    counted from the south, and one of the column, counted from the west. The half,
    quarter and eighth levels each add one digit for the quarter they take: 1 south-west,
    2 south-east, 3 north-west and 4 north-east.

    Parameters
    ----------
    value : str
        The digits of the code.

    Raises
    ------
    ValueError
        If the code has a number of digits no level has, or a digit out of its range.
    """

    value: str

    def __post_init__(self) -> None:
        if not (self.value.isascii() and self.value.isdigit()):
            raise ValueError(f"A regional mesh code holds digits only, given: {self.value!r}")
        level = RegionalMeshLevel.from_code_length(len(self.value))
        for step in self._steps(level):
            parent = step.parent
            if parent is None:
                continue
            digits = self.value[parent.value : step.value]
            if len(digits) == 1:
                if not 1 <= int(digits) <= 4:
                    raise ValueError(
                        f"The quarter digit of {step.label} must be 1 to 4: {self.value}"
                    )
                continue
            if max(int(digit) for digit in digits) >= step.divisions:
                raise ValueError(
                    f"The digits of {step.label} must be below {step.divisions}: {self.value}"
                )

    def __str__(self) -> str:
        return self.value

    @classmethod
    def containing(cls, coordinate: GeoCoordinate, level: RegionalMeshLevel) -> RegionalMeshCode:
        """
        Return the code of the mesh of a level that a place lies in.

        A place on an edge lies in the mesh to its north or east, as `RegionalMeshBounds`
        tells. The place is taken as the exact value of its floating-point degrees.

        Parameters
        ----------
        coordinate : GeoCoordinate
            The place.
        level : RegionalMeshLevel
            The level of the mesh.

        Returns
        -------
        RegionalMeshCode
            The code of the mesh.

        Raises
        ------
        ValueError
            If the place lies outside the area codes can be given for, from latitude 0 to
            66°40' and longitude 100 to 180.
        """
        latitude = Fraction(float(coordinate.latitude.degree[0]))
        longitude = Fraction(float(coordinate.longitude.degree[0])) - FIRST_LEVEL_WEST_ORIGIN
        first = RegionalMeshLevel.FIRST
        is_within_rows = 0 <= latitude < first.latitude_span * FIRST_LEVEL_INDEX_LIMIT
        is_within_columns = 0 <= longitude < first.longitude_span * FIRST_LEVEL_INDEX_LIMIT
        if not (is_within_rows and is_within_columns):
            raise ValueError(f"No regional mesh code is given for {coordinate}")
        digits = ""
        for step in cls._steps(level):
            row = math.floor(latitude / step.latitude_span)
            column = math.floor(longitude / step.longitude_span)
            latitude -= row * step.latitude_span
            longitude -= column * step.longitude_span
            digits += cls._digits_of(step, row, column)
        return cls(digits)

    @property
    def level(self) -> RegionalMeshLevel:
        """
        Return the level of the mesh.

        Returns
        -------
        RegionalMeshLevel
            The level, told by the number of digits.
        """
        return RegionalMeshLevel.from_code_length(len(self.value))

    @property
    def bounds(self) -> RegionalMeshBounds:
        """
        Return the extent of the mesh.

        Returns
        -------
        RegionalMeshBounds
            The edges in exact degrees.
        """
        level = self.level
        south = Fraction(0)
        west = Fraction(FIRST_LEVEL_WEST_ORIGIN)
        for step in self._steps(level):
            row, column = self._position_in_parent(step)
            south += row * step.latitude_span
            west += column * step.longitude_span
        return RegionalMeshBounds(
            south=south,
            west=west,
            north=south + level.latitude_span,
            east=west + level.longitude_span,
        )

    @property
    def parent(self) -> RegionalMeshCode | None:
        """
        Return the code of the mesh this one divides.

        Returns
        -------
        RegionalMeshCode | None
            The code of the coarser mesh, or None for a first level mesh.
        """
        parent = self.level.parent
        if parent is None:
            return None
        return RegionalMeshCode(self.value[: parent.value])

    @property
    def children(self) -> tuple[RegionalMeshCode, ...]:
        """
        Return the codes of the meshes dividing this one.

        Returns
        -------
        tuple[RegionalMeshCode, ...]
            The codes of the finer meshes, row by row from the south-west, or none for an
            eighth level mesh.
        """
        child = self.level.child
        if child is None:
            return ()
        return tuple(
            RegionalMeshCode(self.value + self._digits_of(child, row, column))
            for row in range(child.divisions)
            for column in range(child.divisions)
        )

    @staticmethod
    def _steps(level: RegionalMeshLevel) -> tuple[RegionalMeshLevel, ...]:
        return tuple(step for step in RegionalMeshLevel if step.value <= level.value)

    def _position_in_parent(self, step: RegionalMeshLevel) -> tuple[int, int]:
        parent = step.parent
        if parent is None:
            return int(self.value[0:2]), int(self.value[2:4])
        digits = self.value[parent.value : step.value]
        if len(digits) == 1:
            quadrant = int(digits) - QUADRANT_DIGIT_OFFSET
            return quadrant // 2, quadrant % 2
        return int(digits[0]), int(digits[1])

    @staticmethod
    def _digits_of(step: RegionalMeshLevel, row: int, column: int) -> str:
        if step.parent is None:
            return f"{row:02d}{column:02d}"
        if step.divisions == 2:
            return str(row * 2 + column + QUADRANT_DIGIT_OFFSET)
        return f"{row}{column}"
