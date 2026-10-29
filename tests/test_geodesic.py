import numpy as np
import pytest
from pyproj import Geod
from units import Length, LengthUnit

from geo_coordinate import (
    Altitude,
    Bearing,
    Ellipsoid,
    GeoCoordinate,
    GeoCoordinates,
    Geodesic,
    NorthReference,
)

TOKYO = GeoCoordinate.from_degrees(35.6812, 139.7671)
OSAKA = GeoCoordinate.from_degrees(34.7025, 135.4959)


class TestGeodesic:
    def test_distance_matches_pyproj_on_grs80(self) -> None:
        _, _, expected = Geod(ellps="GRS80").inv(139.7671, 35.6812, 135.4959, 34.7025)

        distance = Geodesic().distance(TOKYO, OSAKA)

        assert distance.meter[0] == pytest.approx(expected, abs=1e-6)

    def test_ellipsoid_differs_from_the_sphere_by_less_than_half_a_percent(self) -> None:
        ellipsoidal = Geodesic().distance(TOKYO, OSAKA).meter[0]
        spherical = TOKYO.distance_to(OSAKA).meter[0]

        assert ellipsoidal != pytest.approx(spherical, abs=1.0)
        assert ellipsoidal == pytest.approx(spherical, rel=5e-3)

    def test_inverse_gives_bearings_at_both_ends(self) -> None:
        solution = Geodesic().inverse(TOKYO, OSAKA)

        assert 250.0 < solution.initial_bearing.degree[0] < 260.0
        assert solution.final_bearing.degree[0] < solution.initial_bearing.degree[0]
        assert solution.initial_bearing.is_true_north

    def test_inverse_broadcasts_a_single_coordinate(self) -> None:
        targets = GeoCoordinates.concatenate([TOKYO, OSAKA])

        distance = Geodesic().distance(TOKYO, targets)

        assert distance.meter[0] == pytest.approx(0.0)
        assert distance.meter[1] == pytest.approx(Geodesic().distance(TOKYO, OSAKA).meter[0])

    def test_direct_inverts_inverse(self) -> None:
        geodesic = Geodesic(Ellipsoid.WGS84)
        solution = geodesic.inverse(TOKYO, OSAKA)

        reached = geodesic.direct(TOKYO, solution.initial_bearing, solution.distance)

        assert isinstance(reached, GeoCoordinate)
        assert geodesic.distance(reached, OSAKA).meter[0] == pytest.approx(0.0, abs=1e-6)

    def test_direct_carries_altitudes_and_wraps_longitudes(self) -> None:
        altitude = Altitude(value=np.array([12.0]), unit=LengthUnit.M)
        start = GeoCoordinate.from_degrees(0.0, 179.9, altitude)

        reached = Geodesic().direct(
            start, Bearing.from_degrees(90.0), Length(value=np.array([50_000.0]), unit=LengthUnit.M)
        )

        assert reached.longitude.degree[0] < -179.0
        assert reached.altitude == altitude

    def test_direct_rejects_magnetic_bearings(self) -> None:
        with pytest.raises(ValueError, match="true north"):
            Geodesic().direct(
                TOKYO,
                Bearing.from_degrees(90.0, NorthReference.MAGNETIC),
                Length(value=np.array([1.0]), unit=LengthUnit.M),
            )

    def test_rejects_mismatched_lengths(self) -> None:
        two = GeoCoordinates.concatenate([TOKYO, OSAKA])
        three = GeoCoordinates.concatenate([TOKYO, OSAKA, TOKYO])
        with pytest.raises(ValueError, match="same length"):
            Geodesic().distance(two, three)

    def test_path_length_sums_the_segments(self) -> None:
        path = GeoCoordinates.concatenate([TOKYO, OSAKA, TOKYO])
        geodesic = Geodesic()

        segments = geodesic.segment_distances(path)

        assert len(segments.meter) == 2
        assert geodesic.path_length(path).meter[0] == pytest.approx(np.sum(segments.meter))
        assert geodesic.segment_distances(path[:1]).meter.shape == (0,)
