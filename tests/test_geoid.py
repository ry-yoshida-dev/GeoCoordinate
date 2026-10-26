from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from geo_coordinate import GeodeticCrs, Geoid, GeoidModel

SOUTH = 35.0
WEST = 139.0
SPACING = 0.5


@pytest.fixture
def grid_path(tmp_path: Path) -> Path:
    heights: NDArray[np.float32] = np.array(
        [[30.0, 32.0, 34.0], [36.0, 38.0, 40.0], [42.0, 44.0, 46.0]], dtype=">f4"
    )
    header = (
        np.array([SOUTH, WEST, SPACING, SPACING], dtype=">f8").tobytes()
        + np.array(heights.shape, dtype=">i4").tobytes()
    )
    path = tmp_path / "grid.gtx"
    path.write_bytes(header + heights.tobytes())
    return path


class TestGeoidModel:
    @pytest.mark.parametrize("model", list(GeoidModel), ids=str)
    def test_every_model_is_published_by_proj(self, model: GeoidModel) -> None:
        assert model.grid_url == f"https://cdn.proj.org/{model.grid_name}"

    def test_japanese_models_are_laid_out_in_jgd2011(self) -> None:
        assert GeoidModel.GSIGEO2011.geodetic_crs is GeodeticCrs.JGD2011
        assert GeoidModel.JPGEO2024.geodetic_crs is GeodeticCrs.JGD2011

    def test_only_egm_models_are_global(self) -> None:
        assert not GeoidModel.GSIGEO2011.is_global
        assert not GeoidModel.JPGEO2024.is_global
        assert GeoidModel.EGM96.is_global
        assert GeoidModel.EGM2008.is_global


class TestGeoid:
    def test_heights_on_nodes_are_those_of_the_grid(self, grid_path: Path) -> None:
        geoid = Geoid(GeoidModel.GSIGEO2011, grid_path)
        heights = geoid.interpolate_heights(np.array([139.0, 140.0]), np.array([35.0, 36.0]))
        assert heights == pytest.approx([30.0, 46.0])

    def test_heights_between_nodes_are_interpolated_bilinearly(self, grid_path: Path) -> None:
        geoid = Geoid(GeoidModel.GSIGEO2011, grid_path)
        heights = geoid.interpolate_heights(np.array([139.25]), np.array([35.25]))
        assert heights == pytest.approx([34.0])

    def test_places_outside_the_grid_have_no_height(self, grid_path: Path) -> None:
        geoid = Geoid(GeoidModel.GSIGEO2011, grid_path)
        heights = geoid.interpolate_heights(np.array([2.35, 139.5]), np.array([48.85, 35.5]))
        assert np.isnan(heights[0])
        assert heights[1] == pytest.approx(38.0)

    def test_missing_grid_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            Geoid(GeoidModel.GSIGEO2011, tmp_path / "missing.tif")

    def test_grid_path_with_whitespace_is_refused(self, grid_path: Path) -> None:
        spaced_path = grid_path.with_name("grid with space.gtx")
        spaced_path.write_bytes(grid_path.read_bytes())
        with pytest.raises(ValueError):
            Geoid(GeoidModel.GSIGEO2011, spaced_path)

    def test_arrays_of_different_shapes_are_refused(self, grid_path: Path) -> None:
        geoid = Geoid(GeoidModel.GSIGEO2011, grid_path)
        with pytest.raises(ValueError):
            geoid.interpolate_heights(np.array([139.0, 139.5]), np.array([35.0]))
