from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..coordinate import GeoCoordinate


@dataclass(frozen=True)
class RegionalMeshBounds:
    """
    The extent of a regional mesh, in exact degrees.

    A mesh holds the places on its southern and western edges, and leaves those on its
    northern and eastern edges to its neighbours, so every place lies in exactly one
    mesh of a level.

    Parameters
    ----------
    south : Fraction
        The latitude of the southern edge.
    west : Fraction
        The longitude of the western edge.
    north : Fraction
        The latitude of the northern edge.
    east : Fraction
        The longitude of the eastern edge.
    """

    south: Fraction
    west: Fraction
    north: Fraction
    east: Fraction

    def __post_init__(self) -> None:
        if self.south >= self.north:
            raise ValueError(f"The south {self.south} must lie below the north {self.north}")
        if self.west >= self.east:
            raise ValueError(f"The west {self.west} must lie west of the east {self.east}")

    def contains(self, coordinate: GeoCoordinate) -> bool:
        """
        Tell whether a place lies in the mesh.

        Parameters
        ----------
        coordinate : GeoCoordinate
            The place.

        Returns
        -------
        bool
            True when it lies inside or on the southern or western edge.
        """
        latitude = Fraction(float(coordinate.latitude.degree[0]))
        longitude = Fraction(float(coordinate.longitude.degree[0]))
        is_within_latitudes = self.south <= latitude < self.north
        is_within_longitudes = self.west <= longitude < self.east
        return is_within_latitudes and is_within_longitudes
