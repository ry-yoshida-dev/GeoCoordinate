from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from ..base import GeoCoordinateBase
from .bounding_box import GeoBoundingBox
from .linear_ring import GeoLinearRing


@dataclass(frozen=True, eq=False)
class GeoPolygon:
    """
    An area bounded by an outline, with optional holes, such as a town or a lake.

    The holes are not checked to lie within the outline or apart from each other, since
    that is costly for the outlines of administrative areas with many vertices.

    Parameters
    ----------
    exterior : GeoLinearRing
        The outline.
    holes : tuple[GeoLinearRing, ...]
        The areas cut out of the outline, such as an enclave.
    """

    exterior: GeoLinearRing
    holes: tuple[GeoLinearRing, ...] = field(default_factory=tuple)

    @property
    def rings(self) -> tuple[GeoLinearRing, ...]:
        """
        Return the outline followed by the holes.

        Returns
        -------
        tuple[GeoLinearRing, ...]
            The rings in the order GeoJSON writes them.
        """
        return (self.exterior, *self.holes)

    @property
    def bounding_box(self) -> GeoBoundingBox:
        """
        Return the smallest box enclosing the outline.

        Returns
        -------
        GeoBoundingBox
            The box of the extreme latitudes and longitudes.
        """
        return self.exterior.bounding_box

    def oriented(self) -> GeoPolygon:
        """
        Return the polygon with rings running as GeoJSON (RFC 7946) requires.

        Returns
        -------
        GeoPolygon
            The polygon with a counterclockwise outline and clockwise holes.
        """
        return GeoPolygon(
            exterior=self.exterior.oriented(is_counterclockwise=True),
            holes=tuple(hole.oriented(is_counterclockwise=False) for hole in self.holes),
        )

    def contains(self, coordinates: GeoCoordinateBase) -> NDArray[np.bool_]:
        """
        Tell whether places lie inside the outline and outside every hole.

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
        is_inside: NDArray[np.bool_] = self.exterior.contains(coordinates)
        for hole in self.holes:
            is_inside &= ~hole.contains(coordinates)
        return is_inside

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoPolygon):
            return False
        return self.exterior == other.exterior and self.holes == other.holes

    def __repr__(self) -> str:
        return (
            f"GeoPolygon(exterior={len(self.exterior)} vertices, holes={len(self.holes)}, "
            + f"bounding_box={self.bounding_box})"
        )
