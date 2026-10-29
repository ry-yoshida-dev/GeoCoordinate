import numpy as np
import pytest

from geo_coordinate import (
    EarthCenteredCoordinates,
    EastNorthUp,
    Ellipsoid,
    GeocentricConversion,
    GeoCoordinate,
    GeoCoordinates,
    LocalTangentPlane,
)

TOKYO = GeoCoordinate.from_degrees(35.6812, 139.7671)


class TestGeocentricConversion:
    def test_axes_point_to_the_prime_meridian_and_the_pole(self) -> None:
        ellipsoid = Ellipsoid.GRS80
        places = GeoCoordinates.from_degrees(
            latitude=np.array([0.0, 0.0, 90.0]), longitude=np.array([0.0, 90.0, 0.0])
        )

        points = GeocentricConversion(ellipsoid).to_earth_centered(places, np.zeros(3))

        np.testing.assert_allclose(
            points.points,
            [
                [ellipsoid.semi_major_axis_meter, 0.0, 0.0],
                [0.0, ellipsoid.semi_major_axis_meter, 0.0],
                [0.0, 0.0, ellipsoid.semi_minor_axis_meter],
            ],
            atol=1e-6,
        )

    def test_round_trips_with_heights(self) -> None:
        conversion = GeocentricConversion()
        places = GeoCoordinates.from_degrees(
            latitude=np.array([35.6812, -33.8688]), longitude=np.array([139.7671, 151.2093])
        )
        heights = np.array([40.0, -12.5])

        position = conversion.to_geodetic(conversion.to_earth_centered(places, heights))

        np.testing.assert_allclose(position.coordinates.latitude.degree, [35.6812, -33.8688])
        np.testing.assert_allclose(position.coordinates.longitude.degree, [139.7671, 151.2093])
        np.testing.assert_allclose(position.ellipsoidal_height, heights, atol=1e-6)

    def test_straight_distance_includes_the_height(self) -> None:
        conversion = GeocentricConversion()

        ground = conversion.to_earth_centered(TOKYO, np.array([0.0]))
        above = conversion.to_earth_centered(TOKYO, np.array([100.0]))

        assert ground.distance_to(above).meter[0] == pytest.approx(100.0)

    def test_rejects_heights_of_another_length(self) -> None:
        with pytest.raises(ValueError, match="ellipsoidal_height"):
            GeocentricConversion().to_earth_centered(TOKYO, np.zeros(2))

    def test_rejects_invalid_points(self) -> None:
        with pytest.raises(ValueError, match="same shape"):
            EarthCenteredCoordinates(x=np.zeros(1), y=np.zeros(2), z=np.zeros(1))
        with pytest.raises(ValueError, match=r"\(N, 3\)"):
            EarthCenteredCoordinates.from_points(np.zeros((1, 2)))


class TestLocalTangentPlane:
    def test_origin_is_at_zero(self) -> None:
        plane = LocalTangentPlane(TOKYO, origin_ellipsoidal_height=40.0)

        points = plane.to_east_north_up(TOKYO, np.array([40.0]))

        np.testing.assert_allclose(points.points, [[0.0, 0.0, 0.0]], atol=1e-6)

    def test_axes_point_east_north_and_up(self) -> None:
        plane = LocalTangentPlane(TOKYO)
        places = GeoCoordinates.from_degrees(
            latitude=np.array([35.6812, 35.6912, 35.6812]),
            longitude=np.array([139.7771, 139.7671, 139.7671]),
        )

        points = plane.to_east_north_up(places, np.array([0.0, 0.0, 50.0]))

        assert points.east[0] > 900.0
        assert abs(points.north[0]) < 1.0
        assert points.north[1] > 1100.0
        assert abs(points.east[1]) < 1e-6
        assert points.up[2] == pytest.approx(50.0)
        assert points.azimuth.degree[0] == pytest.approx(90.0, abs=0.1)
        northward = points.azimuth.degree[1]
        assert min(northward, 360.0 - northward) == pytest.approx(0.0, abs=1e-6)
        assert points.elevation_angle.degree[2] == pytest.approx(90.0)

    def test_up_drops_with_the_curvature_of_the_earth(self) -> None:
        plane = LocalTangentPlane(TOKYO)
        far = GeoCoordinate.from_degrees(35.6812 + 0.9, 139.7671)

        points = plane.to_east_north_up(far, np.array([0.0]))

        assert points.up[0] < -700.0

    def test_round_trips(self) -> None:
        plane = LocalTangentPlane(TOKYO, origin_ellipsoidal_height=40.0, ellipsoid=Ellipsoid.WGS84)
        points = EastNorthUp.from_points(np.array([[120.0, -45.0, 30.0], [-3000.0, 2500.0, -5.0]]))

        restored = plane.to_east_north_up(
            (position := plane.to_geodetic(points)).coordinates, position.ellipsoidal_height
        )

        assert restored == points

    def test_measures_ranges(self) -> None:
        points = EastNorthUp(east=np.array([3.0]), north=np.array([4.0]), up=np.array([12.0]))

        assert points.horizontal_distance.meter[0] == pytest.approx(5.0)
        assert points.slant_range.meter[0] == pytest.approx(13.0)

    def test_rejects_a_height_that_is_not_finite(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            LocalTangentPlane(TOKYO, origin_ellipsoidal_height=float("inf"))
