from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pyproj import Transformer

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
            The heights in metres, of shape (N,), NaN at places outside the grid.

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
