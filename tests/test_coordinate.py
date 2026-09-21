import numpy as np
import pytest
from units import Angle, AngleUnit, LengthUnit

from geo_coordinate import Altitude, GeoCoordinate


class TestGeoCoordinate:
    def test_accepts_any_angle_unit(self) -> None:
        coordinate = GeoCoordinate(
            latitude=Angle(value=np.array([np.pi / 4]), unit=AngleUnit.RADIAN),
            longitude=Angle(value=np.array([90.0]), unit=AngleUnit.DEGREE),
        )

        assert coordinate == GeoCoordinate.from_degrees(np.array([45.0]), np.array([90.0]))

    def test_measures_known_distance(self) -> None:
        tokyo = GeoCoordinate.from_degrees(np.array([35.6812]), np.array([139.7671]))
        osaka = GeoCoordinate.from_degrees(np.array([34.7025]), np.array([135.4959]))

        distance = tokyo.distance_to(osaka)

        assert distance.unit == LengthUnit.M
        assert distance.km == pytest.approx(np.array([403.0]), rel=0.01)

    def test_measures_quarter_meridian(self) -> None:
        equator = GeoCoordinate.from_degrees(np.array([0.0]), np.array([0.0]))
        pole = GeoCoordinate.from_degrees(np.array([90.0]), np.array([0.0]))

        distance = equator.distance_to(pole)

        assert distance.meter == pytest.approx(np.pi / 2 * GeoCoordinate.EARTH_MEAN_RADIUS.meter)

    def test_broadcasts_single_coordinate(self) -> None:
        origin = GeoCoordinate.from_degrees(np.array([0.0]), np.array([0.0]))
        targets = GeoCoordinate.from_degrees(np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0]))

        distance = origin.distance_to(targets)

        assert distance.meter.shape == (3,)
        assert distance.meter[0] == pytest.approx(0.0)
        assert distance.meter[1] == pytest.approx(distance.meter[2])

    def test_compares_altitude(self) -> None:
        altitude = Altitude(value=np.array([10.0]), unit=LengthUnit.M)
        with_altitude = GeoCoordinate.from_degrees(np.array([1.0]), np.array([2.0]), altitude)
        without_altitude = GeoCoordinate.from_degrees(np.array([1.0]), np.array([2.0]))

        assert with_altitude != without_altitude

    def test_rejects_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            GeoCoordinate.from_degrees(np.array([1.0, 2.0]), np.array([1.0]))

    def test_rejects_mismatched_altitude(self) -> None:
        altitude = Altitude(value=np.array([1.0, 2.0]), unit=LengthUnit.M)

        with pytest.raises(ValueError, match="altitude"):
            GeoCoordinate.from_degrees(np.array([1.0]), np.array([1.0]), altitude)

    @pytest.mark.parametrize(
        ("latitude", "longitude", "message"),
        [(91.0, 0.0, "latitude"), (0.0, -180.5, "longitude")],
    )
    def test_rejects_out_of_range(self, latitude: float, longitude: float, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            GeoCoordinate.from_degrees(np.array([latitude]), np.array([longitude]))

    @pytest.mark.parametrize(
        ("latitude", "longitude", "message"),
        [(np.nan, 0.0, "latitude"), (0.0, np.nan, "longitude"), (np.inf, 0.0, "latitude")],
    )
    def test_rejects_non_finite(self, latitude: float, longitude: float, message: str) -> None:
        with pytest.raises(ValueError, match=f"{message} must be finite"):
            GeoCoordinate.from_degrees(np.array([latitude]), np.array([longitude]))

    def test_requires_matching_shape_for_equality(self) -> None:
        single = GeoCoordinate.from_degrees(np.array([1.0]), np.array([2.0]))
        repeated = GeoCoordinate.from_degrees(np.array([1.0, 1.0]), np.array([2.0, 2.0]))

        assert single != repeated
