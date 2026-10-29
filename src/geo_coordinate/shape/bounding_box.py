from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ..base import GeoCoordinateBase
from ..coordinate import GeoCoordinate


@dataclass(frozen=True, eq=False)
class GeoBoundingBox:
    """
    Range of latitudes and longitudes enclosing a set of places.

    The longitudes are compared as plain numbers, so a box does not wrap across the
    antimeridian.

    Parameters
    ----------
    south_west : GeoCoordinate
        The corner of the smallest latitude and longitude.
    north_east : GeoCoordinate
        The corner of the largest latitude and longitude.

    Raises
    ------
    ValueError
        If `north_east` lies south or west of `south_west`.
    """

    south_west: GeoCoordinate
    north_east: GeoCoordinate

    def __post_init__(self) -> None:
        if self.north_degree < self.south_degree or self.east_degree < self.west_degree:
            raise ValueError(
                "north_east must not lie south or west of south_west, "
                + f"given: {self.south_west} and {self.north_east}"
            )

    @classmethod
    def enclosing(cls, coordinates: GeoCoordinateBase) -> GeoBoundingBox:
        """
        Build the smallest box enclosing coordinates.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The places, at least one.

        Returns
        -------
        GeoBoundingBox
            The box of their extreme latitudes and longitudes.

        Raises
        ------
        ValueError
            If `coordinates` is empty.
        """
        if len(coordinates) == 0:
            raise ValueError("coordinates must contain at least one element")
        latitude: NDArray[np.float64] = coordinates.latitude.degree.astype(np.float64)
        longitude: NDArray[np.float64] = coordinates.longitude.degree.astype(np.float64)
        return cls(
            south_west=GeoCoordinate.from_degrees(
                float(np.min(latitude)), float(np.min(longitude))
            ),
            north_east=GeoCoordinate.from_degrees(
                float(np.max(latitude)), float(np.max(longitude))
            ),
        )

    @classmethod
    def union(cls, boxes: Sequence[GeoBoundingBox]) -> GeoBoundingBox:
        """
        Build the smallest box enclosing boxes.

        Parameters
        ----------
        boxes : Sequence[GeoBoundingBox]
            The boxes, at least one.

        Returns
        -------
        GeoBoundingBox
            The box enclosing all of them.

        Raises
        ------
        ValueError
            If `boxes` is empty.
        """
        if len(boxes) == 0:
            raise ValueError("boxes must contain at least one element")
        return cls(
            south_west=GeoCoordinate.from_degrees(
                min(box.south_degree for box in boxes), min(box.west_degree for box in boxes)
            ),
            north_east=GeoCoordinate.from_degrees(
                max(box.north_degree for box in boxes), max(box.east_degree for box in boxes)
            ),
        )

    @property
    def south_degree(self) -> float:
        """
        Return the smallest latitude.

        Returns
        -------
        float
            The latitude of `south_west` in degrees.
        """
        return float(self.south_west.latitude.degree[0])

    @property
    def west_degree(self) -> float:
        """
        Return the smallest longitude.

        Returns
        -------
        float
            The longitude of `south_west` in degrees.
        """
        return float(self.south_west.longitude.degree[0])

    @property
    def north_degree(self) -> float:
        """
        Return the largest latitude.

        Returns
        -------
        float
            The latitude of `north_east` in degrees.
        """
        return float(self.north_east.latitude.degree[0])

    @property
    def east_degree(self) -> float:
        """
        Return the largest longitude.

        Returns
        -------
        float
            The longitude of `north_east` in degrees.
        """
        return float(self.north_east.longitude.degree[0])

    def contains(self, coordinates: GeoCoordinateBase) -> NDArray[np.bool_]:
        """
        Tell whether places lie in the box, its edges included.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The places to test.

        Returns
        -------
        NDArray[np.bool_]
            True for each place within the box, of shape (N,).
        """
        latitude: NDArray[np.float64] = coordinates.latitude.degree.astype(np.float64)
        longitude: NDArray[np.float64] = coordinates.longitude.degree.astype(np.float64)
        return (
            (self.south_degree <= latitude)
            & (latitude <= self.north_degree)
            & (self.west_degree <= longitude)
            & (longitude <= self.east_degree)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoBoundingBox):
            return False
        return self.south_west == other.south_west and self.north_east == other.north_east

    def __repr__(self) -> str:
        return (
            f"GeoBoundingBox(south={self.south_degree}, west={self.west_degree}, "
            + f"north={self.north_degree}, east={self.east_degree})"
        )
