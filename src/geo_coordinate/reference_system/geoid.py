from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pyproj import Transformer
from units import LengthUnit

from ..altitude import Altitude
from ..base import GeoCoordinateBase
from .geoid_model import GeoidModel


class Geoid:
    """
    Heights of the geoid above the ellipsoid, read from the grid of a geoid model.

    The grid is read from a local file, downloaded beforehand from `GeoidModel.grid_url`,
    so that no height is ever looked up over the network. Heights between the nodes of the
    grid are interpolated bilinearly. Places outside the grid, such as places abroad for a
    Japanese model, have no height and come out as NaN.

    Parameters
    ----------
    model : GeoidModel
        The model the grid holds.
    grid_path : Path
        The GeoTIFF of the model, as published at `GeoidModel.grid_url`.

    Raises
    ------
    FileNotFoundError
        If `grid_path` is not a file.
    ValueError
        If `grid_path` contains whitespace, which a PROJ pipeline cannot hold.
    """

    def __init__(self, model: GeoidModel, grid_path: Path) -> None:
        if not grid_path.is_file():
            raise FileNotFoundError(f"The grid of {model.label} is not found: {grid_path}")
        if any(character.isspace() for character in str(grid_path.resolve())):
            raise ValueError(f"The path of a grid must not contain whitespace: {grid_path}")
        self._model: GeoidModel = model
        self._transformer: Transformer = Transformer.from_pipeline(
            "+proj=pipeline"
            + " +step +proj=unitconvert +xy_in=deg +xy_out=rad"
            + f" +step +proj=vgridshift +grids={grid_path.resolve()} +multiplier=1"
            + " +step +proj=unitconvert +xy_in=rad +xy_out=deg"
        )

    @property
    def model(self) -> GeoidModel:
        """
        Return the model the grid holds.

        Returns
        -------
        GeoidModel
            The model given at construction.
        """
        return self._model

    def interpolate_heights(
        self, longitude: NDArray[np.float64], latitude: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """
        Interpolate the heights of the geoid above the ellipsoid at places.

        A height above mean sea level is the height above the ellipsoid less this height.

        Parameters
        ----------
        longitude : NDArray[np.float64]
            Longitudes in degrees in the CRS of the model, of shape (N,).
        latitude : NDArray[np.float64]
            Latitudes in degrees in the CRS of the model, of shape (N,).

        Returns
        -------
        NDArray[np.float64]
            The heights in meters, of shape (N,), NaN at places outside the grid.

        Raises
        ------
        ValueError
            If `longitude` and `latitude` are not 1D arrays of the same shape.
        """
        if longitude.ndim != 1 or longitude.shape != latitude.shape:
            raise ValueError(
                "longitude and latitude must be 1D arrays of the same shape, "
                + f"given: {longitude.shape} and {latitude.shape}"
            )
        _, _, heights = self._transformer.transform(
            longitude, latitude, np.zeros_like(longitude), errcheck=False
        )
        shifted: NDArray[np.float64] = np.asarray(heights, dtype=np.float64)
        return np.where(np.isfinite(shifted), shifted, np.nan)

    def to_altitude(
        self, coordinates: GeoCoordinateBase, ellipsoidal_height: NDArray[np.float64]
    ) -> Altitude:
        """
        Turn heights above the ellipsoid into altitudes above mean sea level.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The places of the heights, in the CRS of the model.
        ellipsoidal_height : NDArray[np.float64]
            The heights above the ellipsoid in meters, as GNSS gives them, of shape (N,).

        Returns
        -------
        Altitude
            The heights above the geoid in meters, of shape (N,).

        Raises
        ------
        ValueError
            If `ellipsoidal_height` differs in shape from the coordinates, or a place lies
            outside the grid.
        """
        if ellipsoidal_height.shape != (len(coordinates),):
            raise ValueError(
                f"ellipsoidal_height must be of shape ({len(coordinates)},), "
                + f"given: {ellipsoidal_height.shape}"
            )
        geoid_height: NDArray[np.float64] = self._heights_within_grid(coordinates)
        altitude: NDArray[np.float64] = ellipsoidal_height - geoid_height
        return Altitude(value=altitude, unit=LengthUnit.M)

    def to_ellipsoidal_height(self, coordinates: GeoCoordinateBase) -> NDArray[np.float64]:
        """
        Turn the altitudes of coordinates into heights above the ellipsoid.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The places with their altitudes above mean sea level, in the CRS of the model.

        Returns
        -------
        NDArray[np.float64]
            The heights above the ellipsoid in meters, of shape (N,).

        Raises
        ------
        ValueError
            If the coordinates carry no altitude, or a place lies outside the grid.
        """
        if coordinates.altitude is None:
            raise ValueError("to_ellipsoidal_height requires coordinates with an altitude")
        geoid_height: NDArray[np.float64] = self._heights_within_grid(coordinates)
        return coordinates.altitude.meter.astype(np.float64) + geoid_height

    def _heights_within_grid(self, coordinates: GeoCoordinateBase) -> NDArray[np.float64]:
        """
        Interpolate the heights of the geoid at places that must lie within the grid.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The places, in the CRS of the model.

        Returns
        -------
        NDArray[np.float64]
            The heights of the geoid in meters, of shape (N,).

        Raises
        ------
        ValueError
            If a place lies outside the grid.
        """
        heights: NDArray[np.float64] = self.interpolate_heights(
            coordinates.longitude.degree.astype(np.float64),
            coordinates.latitude.degree.astype(np.float64),
        )
        if np.any(np.isnan(heights)):
            raise ValueError(f"some of the places lie outside the grid of {self._model.label}")
        return heights
