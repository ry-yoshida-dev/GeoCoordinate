from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from units import Length, LengthUnit

from ..altitude import Altitude
from .coordinate_reference_system import CoordinateReferenceSystem


@dataclass(frozen=True, eq=False)
class PlaneCoordinates:
    """
    Points on the plane of a projected coordinate reference system, in meters.

    Easting grows to the east and northing to the north. The Japan Plane Rectangular
    Coordinate System names them the other way round, X for northing and Y for easting,
    which `survey_x` and `survey_y` follow.

    Parameters
    ----------
    easting : NDArray[np.float64]
        The eastings in meters, of shape (N,).
    northing : NDArray[np.float64]
        The northings in meters, of shape (N,).
    crs : CoordinateReferenceSystem
        The projected CRS the points lie on.
    altitude : Altitude | None
        The heights relative to mean sea level, or None when unknown.

    Raises
    ------
    ValueError
        If the arrays are not 1D of the same shape, are not finite, or the altitudes
        differ in length.
    """

    easting: NDArray[np.float64]
    northing: NDArray[np.float64]
    crs: CoordinateReferenceSystem
    altitude: Altitude | None = None

    def __post_init__(self) -> None:
        if self.easting.ndim != 1 or self.easting.shape != self.northing.shape:
            raise ValueError(
                "easting and northing must be 1D arrays of the same shape, "
                + f"given: {self.easting.shape} and {self.northing.shape}"
            )
        if not (np.all(np.isfinite(self.easting)) and np.all(np.isfinite(self.northing))):
            raise ValueError("easting and northing must be finite")
        if self.altitude is not None and len(self.altitude) != len(self.easting):
            raise ValueError(
                "altitude must have the same length as easting, "
                + f"given: {len(self.altitude)} and {len(self.easting)}"
            )

    @classmethod
    def from_points(
        cls,
        points: NDArray[np.float64],
        crs: CoordinateReferenceSystem,
        altitude: Altitude | None = None,
    ) -> PlaneCoordinates:
        """
        Build plane coordinates from an array of eastings and northings.

        Parameters
        ----------
        points : NDArray[np.float64]
            Eastings and northings in meters, of shape (N, 2).
        crs : CoordinateReferenceSystem
            The projected CRS the points lie on.
        altitude : Altitude | None
            The heights relative to mean sea level, or None when unknown.

        Returns
        -------
        PlaneCoordinates
            The points.

        Raises
        ------
        ValueError
            If `points` is not of shape (N, 2).
        """
        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError(f"points must be of shape (N, 2): {points.shape}")
        return cls(
            easting=points[:, 0].astype(np.float64),
            northing=points[:, 1].astype(np.float64),
            crs=crs,
            altitude=altitude,
        )

    @property
    def points(self) -> NDArray[np.float64]:
        """
        Return the eastings and northings stacked as columns.

        Returns
        -------
        NDArray[np.float64]
            The points in meters, of shape (N, 2).
        """
        return np.column_stack([self.easting, self.northing]).astype(np.float64)

    @property
    def survey_x(self) -> NDArray[np.float64]:
        """
        Return the X coordinates of Japanese surveying, which point north.

        Returns
        -------
        NDArray[np.float64]
            The northings in meters.
        """
        return self.northing

    @property
    def survey_y(self) -> NDArray[np.float64]:
        """
        Return the Y coordinates of Japanese surveying, which point east.

        Returns
        -------
        NDArray[np.float64]
            The eastings in meters.
        """
        return self.easting

    def distance_to(self, other: PlaneCoordinates) -> Length:
        """
        Straight distances on the plane, element-wise.

        Distances on the plane differ from those on the ground by the scale factor of
        the projection, such as 0.9999 on the central meridian of a Japanese zone.

        Parameters
        ----------
        other : PlaneCoordinates
            The points to measure to, on the same CRS. Either side may hold a single
            point, which is broadcast against the other.

        Returns
        -------
        Length
            The distances in meters.

        Raises
        ------
        ValueError
            If the points lie on different CRSs, or both sides hold more than one point
            and differ in length.
        """
        if other.crs.epsg != self.crs.epsg:
            raise ValueError(f"points must lie on the same CRS, given: {self.crs} and {other.crs}")
        if len(self) != 1 and len(other) != 1 and len(self) != len(other):
            raise ValueError(
                "points must have the same length or a single element, "
                + f"given: {len(self)} and {len(other)}"
            )
        distance: NDArray[np.float64] = np.hypot(
            other.easting - self.easting, other.northing - self.northing
        )
        return Length(value=distance, unit=LengthUnit.M)

    def __len__(self) -> int:
        return len(self.easting)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlaneCoordinates):
            return False
        return (
            other.crs.epsg == self.crs.epsg
            and self.easting.shape == other.easting.shape
            and bool(np.allclose(self.easting, other.easting))
            and bool(np.allclose(self.northing, other.northing))
            and self.altitude == other.altitude
        )

    def __repr__(self) -> str:
        return (
            f"PlaneCoordinates(easting={self.easting}, northing={self.northing}, "
            + f"crs={self.crs}, altitude={self.altitude})"
        )
