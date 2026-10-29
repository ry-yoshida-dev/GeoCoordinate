from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import NDArray
from pyproj import Transformer

from .geodetic_crs import GeodeticCrs
from .web_mercator import WebMercator

EDGE_TOLERANCE_METRES: Final[float] = 1e-6


class WebMercatorProjection:
    """
    Projects longitudes and latitudes on WGS 84 to Web Mercator meters and back.

    Web maps are drawn on the Web Mercator plane, so anything placed there, such as an
    image warped onto the ground, lies on the map as computed. Distances on that plane
    are stretched by `1 / cos(latitude)`, which `ground_scale` undoes to give meters on
    the ground. Only the world square of the projection is accepted: latitudes within
    `latitude_limit` and points within `half_extent` of the origin.

    Parameters
    ----------
    projection : WebMercator
        The Web Mercator CRS to project onto.
    """

    def __init__(self, projection: WebMercator = WebMercator.PSEUDO_MERCATOR) -> None:
        self._projection: WebMercator = projection
        self._forward: Transformer = Transformer.from_crs(
            GeodeticCrs.WGS84.crs, projection.crs, always_xy=True
        )
        self._inverse: Transformer = Transformer.from_crs(
            projection.crs, GeodeticCrs.WGS84.crs, always_xy=True
        )

    def project(
        self, longitude: NDArray[np.float64], latitude: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """
        Project places onto the Web Mercator plane.

        Parameters
        ----------
        longitude : NDArray[np.float64]
            Longitudes in degrees, of shape (N,).
        latitude : NDArray[np.float64]
            Latitudes in degrees, of shape (N,).

        Returns
        -------
        NDArray[np.float64]
            Eastings and northings in meters, of shape (N, 2).

        Raises
        ------
        ValueError
            If `longitude` and `latitude` are not of the same shape (N,), or a latitude
            lies beyond `latitude_limit`.
        """
        if longitude.ndim != 1 or longitude.shape != latitude.shape:
            raise ValueError(
                "longitude and latitude must be of the same shape (N,): "
                + f"{longitude.shape} and {latitude.shape}"
            )
        latitude_limit: float = self._projection.latitude_limit
        if np.any(np.abs(latitude) > latitude_limit):
            raise ValueError(f"latitudes must lie within {latitude_limit} degrees of the equator")
        easting, northing = self._forward.transform(longitude, latitude)
        return np.column_stack([easting, northing]).astype(np.float64)

    def unproject(self, points: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        Turn points of the Web Mercator plane back into places.

        Parameters
        ----------
        points : NDArray[np.float64]
            Eastings and northings in meters, of shape (N, 2).

        Returns
        -------
        NDArray[np.float64]
            Longitudes and latitudes in degrees, of shape (N, 2).

        Raises
        ------
        ValueError
            If `points` is not of shape (N, 2), or a point lies outside the world square.
        """
        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError(f"points must be of shape (N, 2): {points.shape}")
        half_extent: float = self._projection.half_extent
        if np.any(np.abs(points) > half_extent + EDGE_TOLERANCE_METRES):
            raise ValueError(f"points must lie within {half_extent} meters of the origin")
        longitude, latitude = self._inverse.transform(points[:, 0], points[:, 1])
        return np.column_stack([longitude, latitude]).astype(np.float64)

    @staticmethod
    def ground_scale(latitude: float) -> float:
        """
        Return how many ground meters one Web Mercator metre spans at a latitude.

        The scale is that of the sphere the projection is defined on. Measured on the
        WGS 84 ellipsoid instead, ground distances differ from it by up to about 0.7%,
        depending on latitude and direction.

        Parameters
        ----------
        latitude : float
            The latitude in degrees.

        Returns
        -------
        float
            `cos(latitude)`.
        """
        return float(np.cos(np.radians(latitude)))
