import numpy as np
import pytest
from units import LengthUnit

from geo_coordinate import Altitude, GeoCoordinate, GeoCoordinates


def make_track() -> GeoCoordinates:
    return GeoCoordinates.from_degrees(
        latitude=np.array([0.0, 0.0, 1.0]),
        longitude=np.array([0.0, 1.0, 1.0]),
        altitude=Altitude(value=np.array([1.0, 2.0, 3.0]), unit=LengthUnit.KM),
    )


ONE_DEGREE_METER = np.pi / 180 * GeoCoordinates.EARTH_MEAN_RADIUS.meter[0]


class TestGeoCoordinates:
    def test_returns_single_coordinate_for_integer_index(self) -> None:
        track = make_track()

        coordinate = track[-1]

        assert coordinate == GeoCoordinate.from_degrees(
            1.0, 1.0, Altitude(value=np.array([3.0]), unit=LengthUnit.KM)
        )

    def test_returns_single_coordinate_for_numpy_integer_index(self) -> None:
        track = make_track()

        coordinate = track[np.int64(1)]

        assert coordinate == track[1]

    def test_returns_batch_for_slice(self) -> None:
        track = make_track()

        assert track[1:] == GeoCoordinates.from_degrees(
            latitude=np.array([0.0, 1.0]),
            longitude=np.array([1.0, 1.0]),
            altitude=Altitude(value=np.array([2.0, 3.0]), unit=LengthUnit.KM),
        )

    def test_returns_batch_for_mask(self) -> None:
        track = make_track()

        selected = track[track.latitude.degree > 0.5]

        assert len(selected) == 1
        assert isinstance(selected, GeoCoordinates)

    def test_raises_for_index_out_of_range(self) -> None:
        with pytest.raises(IndexError):
            make_track()[3]

    def test_iterates_single_coordinates(self) -> None:
        coordinates = list(make_track())

        assert len(coordinates) == 3
        assert all(isinstance(coordinate, GeoCoordinate) for coordinate in coordinates)
        assert coordinates[1] == make_track()[1]

    def test_concatenates_in_order(self) -> None:
        track = make_track()

        joined = GeoCoordinates.concatenate([track[0], track[1:]])

        assert joined == track

    def test_rejects_partial_altitude_on_concatenate(self) -> None:
        with pytest.raises(ValueError, match="altitude"):
            GeoCoordinates.concatenate([make_track(), GeoCoordinate.from_degrees(0.0, 0.0)])

    def test_rejects_empty_concatenate(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            GeoCoordinates.concatenate([])

    def test_measures_distance_matrix(self) -> None:
        matrix = make_track().distance_matrix

        assert matrix.meter.shape == (3, 3)
        assert np.allclose(np.diag(matrix.meter), 0.0)
        assert np.allclose(matrix.meter, matrix.meter.T)
        assert matrix.meter[0, 1] == pytest.approx(ONE_DEGREE_METER)

    def test_measures_pairwise_distance_to_other(self) -> None:
        others = GeoCoordinates.from_degrees(np.array([0.0, 2.0]), np.array([0.0, 0.0]))

        distance = make_track().pairwise_distance_to(others)

        assert distance.meter.shape == (3, 2)
        assert distance.meter[0, 1] == pytest.approx(2 * ONE_DEGREE_METER)

    def test_measures_path(self) -> None:
        track = make_track()

        assert track.segment_distances.meter == pytest.approx([ONE_DEGREE_METER] * 2)
        assert track.cumulative_distances.meter == pytest.approx(
            [0.0, ONE_DEGREE_METER, 2 * ONE_DEGREE_METER]
        )
        assert track.path_length.meter == pytest.approx([2 * ONE_DEGREE_METER])

    def test_measures_path_of_single_coordinate(self) -> None:
        track = make_track()[:1]

        assert track.segment_distances.meter.shape == (0,)
        assert track.cumulative_distances.meter.tolist() == [0.0]
        assert track.path_length.meter.tolist() == [0.0]

    def test_rejects_mismatched_lengths_on_distance_to(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            make_track().distance_to(make_track()[:2])

    def test_rejects_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            GeoCoordinates.from_degrees(np.array([1.0, 2.0]), np.array([1.0]))

    def test_requires_matching_shape_for_equality(self) -> None:
        single = GeoCoordinates.from_degrees(np.array([1.0]), np.array([2.0]))
        repeated = GeoCoordinates.from_degrees(np.array([1.0, 1.0]), np.array([2.0, 2.0]))

        assert single != repeated
