import numpy as np
import pytest
from units import Angle, AngleUnit, Length, LengthUnit

from geo_coordinate import Altitude, GeoCoordinate, GeoCoordinates, SexagesimalText


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

    def test_builds_from_sexagesimal(self) -> None:
        coordinates = GeoCoordinates.from_sexagesimal(
            latitude=["0°0'0\"N", "1°0'0\"S"], longitude=["1°30'E", "180°W"]
        )

        assert coordinates == GeoCoordinates.from_degrees(
            np.array([0.0, -1.0]), np.array([1.5, -180.0])
        )

    def test_rejects_out_of_range_sexagesimal(self) -> None:
        with pytest.raises(ValueError, match="latitude must be within"):
            GeoCoordinates.from_sexagesimal(latitude=["90°0'1\"N"], longitude=["0°E"])

    def test_writes_sexagesimal(self) -> None:
        text = make_track().to_sexagesimal(0)

        assert text == SexagesimalText(
            latitude=("0°0'0\"N", "0°0'0\"N", "1°0'0\"N"),
            longitude=("0°0'0\"E", "1°0'0\"E", "1°0'0\"E"),
        )

    def test_measures_segment_bearings(self) -> None:
        bearings = make_track().segment_bearings

        assert bearings.unit == AngleUnit.DEGREE
        assert bearings.degree == pytest.approx([90.0, 0.0])

    def test_measures_bearings_of_single_coordinate(self) -> None:
        assert make_track()[:1].segment_bearings.degree.shape == (0,)

    def test_measures_altitude_profile(self) -> None:
        track = make_track()

        assert track.segment_altitude_changes == Altitude(
            value=np.array([1.0, 1.0]), unit=LengthUnit.KM
        )
        assert track.segment_slant_distances.meter == pytest.approx(
            [np.hypot(ONE_DEGREE_METER, 1000.0)] * 2
        )
        assert track.segment_grades == pytest.approx([1000.0 / ONE_DEGREE_METER] * 2)

    def test_measures_ascent_and_descent(self) -> None:
        track = GeoCoordinates.from_degrees(
            latitude=np.array([0.0, 0.001, 0.002, 0.003]),
            longitude=np.zeros(4),
            altitude=Altitude(value=np.array([10.0, 15.0, 12.0, -2.0]), unit=LengthUnit.M),
        )

        assert track.total_ascent.meter.tolist() == pytest.approx([5.0])
        assert track.total_descent.meter.tolist() == pytest.approx([17.0])

    def test_marks_grade_of_zero_distance_as_nan(self) -> None:
        track = GeoCoordinates.from_degrees(
            latitude=np.array([0.0, 0.0]),
            longitude=np.array([0.0, 0.0]),
            altitude=Altitude(value=np.array([0.0, 5.0]), unit=LengthUnit.M),
        )

        assert np.isnan(track.segment_grades).tolist() == [True]
        assert track.segment_slant_distances.meter == pytest.approx([5.0])

    def test_requires_altitude_for_profile(self) -> None:
        track = GeoCoordinates.from_degrees(np.array([0.0, 1.0]), np.array([0.0, 0.0]))

        with pytest.raises(ValueError, match="requires coordinates with an altitude"):
            _ = track.segment_grades

    def test_moves_each_coordinate_to_destination(self) -> None:
        track = make_track()
        bearing = Angle(value=np.array([0.0, 90.0, 180.0]), unit=AngleUnit.DEGREE)
        distance = Length(value=np.array([ONE_DEGREE_METER]), unit=LengthUnit.M)

        destination = track.destination(bearing, distance)

        assert isinstance(destination, GeoCoordinates)
        assert destination.latitude.degree == pytest.approx([1.0, 0.0, 0.0])
        assert destination.longitude.degree == pytest.approx([0.0, 2.0, 1.0])
        assert destination.altitude == track.altitude

    def test_rejects_mismatched_lengths_on_destination(self) -> None:
        bearing = Angle(value=np.array([0.0, 90.0]), unit=AngleUnit.DEGREE)
        distance = Length(value=np.array([1.0]), unit=LengthUnit.M)

        with pytest.raises(ValueError, match="same length"):
            make_track().destination(bearing, distance)
