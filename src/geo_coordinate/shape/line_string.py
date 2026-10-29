from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from units import Length

from ..coordinates import GeoCoordinates
from .bounding_box import GeoBoundingBox


@dataclass(frozen=True, eq=False)
class GeoLineString:
    """
    A line through places in order, such as a road, a river or a GPS track.

    Consecutive vertices are joined by great circles when the line is measured.

    Parameters
    ----------
    vertices : GeoCoordinates
        The places the line passes through, at least two, with optional altitudes.

    Raises
    ------
    ValueError
        If fewer than two vertices are given.
    """

    MINIMUM_VERTICES: ClassVar[int] = 2

    vertices: GeoCoordinates

    def __post_init__(self) -> None:
        if len(self.vertices) < self.MINIMUM_VERTICES:
            raise ValueError(
                f"a line string needs at least {self.MINIMUM_VERTICES} vertices, "
                + f"given: {len(self.vertices)}"
            )

    @property
    def length(self) -> Length:
        """
        Return the length along the line on a sphere.

        `Geodesic.path_length` of `vertices` measures it on an ellipsoid instead.

        Returns
        -------
        Length
            The total great-circle distance in meters, of shape (1,).
        """
        return self.vertices.path_length

    @property
    def bounding_box(self) -> GeoBoundingBox:
        """
        Return the smallest box enclosing the vertices.

        Returns
        -------
        GeoBoundingBox
            The box of the extreme latitudes and longitudes.
        """
        return GeoBoundingBox.enclosing(self.vertices)

    def reversed(self) -> GeoLineString:
        """
        Return the line running the other way.

        Returns
        -------
        GeoLineString
            The line with its vertices in reverse order.
        """
        return GeoLineString(vertices=self.vertices[::-1])

    def __len__(self) -> int:
        return len(self.vertices)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoLineString):
            return False
        return self.vertices == other.vertices

    def __repr__(self) -> str:
        return f"GeoLineString(vertices={len(self.vertices)}, bounding_box={self.bounding_box})"
