from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray
from units import Length

from ..base import GeoCoordinateBase
from ..coordinates import GeoCoordinates
from .bounding_box import GeoBoundingBox


@dataclass(frozen=True, eq=False)
class GeoLinearRing:
    """
    A closed line bounding an area, the outline or a hole of a polygon.

    The ring is stored open: a last vertex repeating the first, as GeoJSON writes it, is
    dropped, and `closed_vertices` adds it back. The edges are straight lines in latitude
    and longitude when testing which places lie inside, as in GeoJSON, so rings must not
    cross the antimeridian.

    Parameters
    ----------
    vertices : GeoCoordinates
        The corners in order, at least three after dropping a repeated last vertex.

    Raises
    ------
    ValueError
        If fewer than three distinct corners are given.
    """

    MINIMUM_VERTICES: ClassVar[int] = 3
    CONTAINS_CHUNK_SIZE: ClassVar[int] = 1_000_000

    vertices: GeoCoordinates

    def __post_init__(self) -> None:
        if self._is_closed(self.vertices):
            object.__setattr__(self, "vertices", self.vertices[:-1])
        if len(self.vertices) < self.MINIMUM_VERTICES:
            raise ValueError(
                f"a linear ring needs at least {self.MINIMUM_VERTICES} corners, "
                + f"given: {len(self.vertices)}"
            )

    @property
    def closed_vertices(self) -> GeoCoordinates:
        """
        Return the corners with the first one repeated at the end.

        Returns
        -------
        GeoCoordinates
            The corners as GeoJSON and shapefiles write them, of length N + 1.
        """
        return GeoCoordinates.concatenate([self.vertices, self.vertices[0]])

    @property
    def perimeter(self) -> Length:
        """
        Return the length around the ring on a sphere.

        `Geodesic.perimeter` measures it on an ellipsoid instead.

        Returns
        -------
        Length
            The total great-circle distance in meters, of shape (1,).
        """
        return self.closed_vertices.path_length

    @property
    def bounding_box(self) -> GeoBoundingBox:
        """
        Return the smallest box enclosing the corners.

        Returns
        -------
        GeoBoundingBox
            The box of the extreme latitudes and longitudes.
        """
        return GeoBoundingBox.enclosing(self.vertices)

    @property
    def is_counterclockwise(self) -> bool:
        """
        Return whether the corners run counterclockwise seen from above.

        GeoJSON (RFC 7946) runs outlines counterclockwise and holes clockwise.

        Returns
        -------
        bool
            True when the signed area in latitude and longitude is positive.
        """
        longitude, latitude = self._corners()
        signed_double_area: float = float(
            np.sum(longitude * np.roll(latitude, -1) - np.roll(longitude, -1) * latitude)
        )
        return signed_double_area > 0

    def oriented(self, is_counterclockwise: bool) -> GeoLinearRing:
        """
        Return the ring running in a given direction.

        Parameters
        ----------
        is_counterclockwise : bool
            Whether the result runs counterclockwise.

        Returns
        -------
        GeoLinearRing
            This ring, reversed if it runs the other way.
        """
        if self.is_counterclockwise == is_counterclockwise:
            return self
        return GeoLinearRing(vertices=self.vertices[::-1])

    def contains(self, coordinates: GeoCoordinateBase) -> NDArray[np.bool_]:
        """
        Tell whether places lie inside the ring, by the even-odd rule.

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
        is_inside: NDArray[np.bool_] = self.bounding_box.contains(coordinates)
        candidates: NDArray[np.intp] = np.flatnonzero(is_inside)
        if len(candidates) == 0:
            return is_inside
        start_longitude, start_latitude = self._corners()
        end_longitude: NDArray[np.float64] = np.roll(start_longitude, -1)
        end_latitude: NDArray[np.float64] = np.roll(start_latitude, -1)
        point_longitude: NDArray[np.float64] = coordinates.longitude.degree.astype(np.float64)
        point_latitude: NDArray[np.float64] = coordinates.latitude.degree.astype(np.float64)
        chunk_size: int = max(1, self.CONTAINS_CHUNK_SIZE // len(self.vertices))
        for chunk_start in range(0, len(candidates), chunk_size):
            chunk: NDArray[np.intp] = candidates[chunk_start : chunk_start + chunk_size]
            longitude: NDArray[np.float64] = point_longitude[chunk][:, np.newaxis]
            latitude: NDArray[np.float64] = point_latitude[chunk][:, np.newaxis]
            is_straddling: NDArray[np.bool_] = (start_latitude > latitude) != (
                end_latitude > latitude
            )
            latitude_span: NDArray[np.float64] = np.where(
                is_straddling, end_latitude - start_latitude, 1.0
            )
            crossing_longitude: NDArray[np.float64] = (
                start_longitude
                + (end_longitude - start_longitude) * (latitude - start_latitude) / latitude_span
            )
            crossings: NDArray[np.intp] = np.count_nonzero(
                is_straddling & (longitude < crossing_longitude), axis=1
            )
            is_inside[chunk] = crossings % 2 == 1
        return is_inside

    @staticmethod
    def _is_closed(vertices: GeoCoordinates) -> bool:
        """
        Tell whether the last vertex repeats the first exactly.

        The comparison is exact rather than within the tolerance of `GeoCoordinate`
        equality, so that close but distinct corners of a small ring are kept.

        Parameters
        ----------
        vertices : GeoCoordinates
            The vertices of the ring.

        Returns
        -------
        bool
            True when the first and last latitude, longitude and altitude are identical.
        """
        if len(vertices) < 2:
            return False
        columns: list[NDArray[np.float64]] = [
            vertices.latitude.degree.astype(np.float64),
            vertices.longitude.degree.astype(np.float64),
        ]
        if vertices.altitude is not None:
            columns.append(vertices.altitude.meter.astype(np.float64))
        return all(bool(column[0] == column[-1]) for column in columns)

    def _corners(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Longitudes and latitudes of the corners in degrees.

        Returns
        -------
        tuple[NDArray[np.float64], NDArray[np.float64]]
            The longitudes and the latitudes, each of shape (N,).
        """
        return (
            self.vertices.longitude.degree.astype(np.float64),
            self.vertices.latitude.degree.astype(np.float64),
        )

    def __len__(self) -> int:
        return len(self.vertices)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoLinearRing):
            return False
        return self.vertices == other.vertices

    def __repr__(self) -> str:
        return f"GeoLinearRing(vertices={len(self.vertices)}, bounding_box={self.bounding_box})"
