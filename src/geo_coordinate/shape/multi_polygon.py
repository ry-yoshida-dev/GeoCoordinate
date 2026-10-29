from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ..base import GeoCoordinateBase
from .bounding_box import GeoBoundingBox
from .polygon import GeoPolygon


@dataclass(frozen=True, eq=False)
class GeoMultiPolygon:
    """
    An area made of separate polygons, such as a prefecture with its islands.

    Parameters
    ----------
    polygons : tuple[GeoPolygon, ...]
        The parts, at least one. They are not checked to be apart from each other.

    Raises
    ------
    ValueError
        If no polygon is given.
    """

    polygons: tuple[GeoPolygon, ...]

    def __post_init__(self) -> None:
        if len(self.polygons) == 0:
            raise ValueError("a multi polygon needs at least one polygon")

    @property
    def bounding_box(self) -> GeoBoundingBox:
        """
        Return the smallest box enclosing every part.

        Returns
        -------
        GeoBoundingBox
            The box of the extreme latitudes and longitudes.
        """
        return GeoBoundingBox.union([polygon.bounding_box for polygon in self.polygons])

    def oriented(self) -> GeoMultiPolygon:
        """
        Return the parts with rings running as GeoJSON (RFC 7946) requires.

        Returns
        -------
        GeoMultiPolygon
            The parts with counterclockwise outlines and clockwise holes.
        """
        return GeoMultiPolygon(polygons=tuple(polygon.oriented() for polygon in self.polygons))

    def contains(self, coordinates: GeoCoordinateBase) -> NDArray[np.bool_]:
        """
        Tell whether places lie inside any part.

        Places exactly on an edge may be reported either way.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The places to test.

        Returns
        -------
        NDArray[np.bool_]
            True for each place inside, of shape (N,).
        """
        is_inside: NDArray[np.bool_] = np.zeros(len(coordinates), dtype=np.bool_)
        for polygon in self.polygons:
            is_inside |= polygon.contains(coordinates)
        return is_inside

    def __len__(self) -> int:
        return len(self.polygons)

    def __iter__(self) -> Iterator[GeoPolygon]:
        return iter(self.polygons)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoMultiPolygon):
            return False
        return self.polygons == other.polygons

    def __repr__(self) -> str:
        return f"GeoMultiPolygon(polygons={len(self.polygons)}, bounding_box={self.bounding_box})"
