import numpy as np
import pytest
from pyproj import Transformer
from units import LengthUnit

from geo_coordinate import (
    Altitude,
    GeoCoordinate,
    GeoCoordinates,
    GeodeticCrs,
    JapanPlaneRectangularZone,
    LatitudeHemisphere,
    PlaneCoordinates,
    PlaneProjection,
    UtmZone,
    WebMercator,
)

ZONE_9 = JapanPlaneRectangularZone.ZONE_9


class TestPlaneProjection:
    def test_origin_of_a_zone_projects_to_zero(self) -> None:
        points = PlaneProjection(ZONE_9).project(ZONE_9.origin)

        assert points.easting[0] == pytest.approx(0.0, abs=1e-6)
        assert points.northing[0] == pytest.approx(0.0, abs=1e-6)
        assert points.crs is ZONE_9

    def test_matches_pyproj(self) -> None:
        places = GeoCoordinates.from_degrees(
            latitude=np.array([35.6812, 35.652]), longitude=np.array([139.7671, 139.541])
        )
        transformer = Transformer.from_crs(GeodeticCrs.JGD2011.crs, ZONE_9.crs, always_xy=True)
        easting, northing = transformer.transform(places.longitude.degree, places.latitude.degree)

        points = PlaneProjection(ZONE_9).project(places)

        np.testing.assert_allclose(points.easting, easting, atol=1e-6)
        np.testing.assert_allclose(points.northing, northing, atol=1e-6)
        np.testing.assert_allclose(points.survey_x, northing, atol=1e-6)
        np.testing.assert_allclose(points.survey_y, easting, atol=1e-6)

    @pytest.mark.parametrize(
        "plane",
        [
            ZONE_9,
            UtmZone(number=54, hemisphere=LatitudeHemisphere.NORTH),
            WebMercator.PSEUDO_MERCATOR,
        ],
        ids=str,
    )
    def test_round_trips_through_the_plane(self, plane: JapanPlaneRectangularZone) -> None:
        projection = PlaneProjection(plane, source=GeodeticCrs.WGS84)
        altitude = Altitude(value=np.array([3.0, 25.0]), unit=LengthUnit.M)
        places = GeoCoordinates.from_degrees(
            latitude=np.array([35.6812, 35.652]),
            longitude=np.array([139.7671, 139.541]),
            altitude=altitude,
        )

        restored = projection.unproject(projection.project(places))

        np.testing.assert_allclose(restored.latitude.degree, places.latitude.degree, atol=1e-9)
        np.testing.assert_allclose(restored.longitude.degree, places.longitude.degree, atol=1e-9)
        assert restored.altitude == altitude

    def test_tokyo_datum_coordinates_are_shifted_before_projecting(self) -> None:
        station = GeoCoordinate.from_degrees(35.6812, 139.7671)

        on_jgd2011 = PlaneProjection(ZONE_9).project(station)
        on_tokyo = PlaneProjection(ZONE_9, source=GeodeticCrs.TOKYO).project(station)

        assert 400.0 < on_tokyo.distance_to(on_jgd2011).meter[0] < 500.0

    def test_scale_factor_is_that_of_the_central_meridian_at_the_origin(self) -> None:
        projection = PlaneProjection(ZONE_9)
        east_of_origin = GeoCoordinate.from_degrees(36.0, 141.5)

        assert projection.scale_factors(ZONE_9.origin)[0] == pytest.approx(0.9999, abs=1e-9)
        assert projection.scale_factors(east_of_origin)[0] > 0.9999

    def test_meridian_convergence_grows_east_of_the_central_meridian(self) -> None:
        projection = PlaneProjection(ZONE_9)

        on_meridian = projection.meridian_convergence(ZONE_9.origin).degree[0]
        east = projection.meridian_convergence(GeoCoordinate.from_degrees(36.0, 140.5)).degree[0]
        west = projection.meridian_convergence(GeoCoordinate.from_degrees(36.0, 139.0)).degree[0]

        assert on_meridian == pytest.approx(0.0, abs=1e-9)
        assert east > 0.0
        assert west < 0.0

    def test_meridian_convergence_is_the_angle_from_true_to_grid_north(self) -> None:
        projection = PlaneProjection(ZONE_9)
        places = GeoCoordinates.from_degrees(
            latitude=np.array([36.0, 36.0001]), longitude=np.array([140.5, 140.5])
        )

        points = projection.project(places)
        true_north_on_grid = np.degrees(
            np.arctan2(np.diff(points.easting)[0], np.diff(points.northing)[0])
        )

        convergence = projection.meridian_convergence(places[0]).degree[0]
        assert convergence == pytest.approx(-true_north_on_grid, abs=1e-5)

    def test_rejects_a_geographic_crs_as_plane(self) -> None:
        with pytest.raises(ValueError, match="projected"):
            PlaneProjection(GeodeticCrs.JGD2011)

    def test_rejects_points_of_another_plane(self) -> None:
        points = PlaneCoordinates(
            easting=np.zeros(1), northing=np.zeros(1), crs=JapanPlaneRectangularZone.ZONE_8
        )
        with pytest.raises(ValueError, match="must lie on"):
            PlaneProjection(ZONE_9).unproject(points)


class TestPlaneCoordinates:
    def test_distances_are_straight_on_the_plane(self) -> None:
        start = PlaneCoordinates(easting=np.array([0.0]), northing=np.array([0.0]), crs=ZONE_9)
        end = PlaneCoordinates.from_points(np.array([[3.0, 4.0], [6.0, 8.0]]), ZONE_9)

        assert start.distance_to(end).meter.tolist() == [5.0, 10.0]
        np.testing.assert_array_equal(end.points, [[3.0, 4.0], [6.0, 8.0]])

    def test_rejects_distances_across_planes(self) -> None:
        start = PlaneCoordinates(easting=np.zeros(1), northing=np.zeros(1), crs=ZONE_9)
        other = PlaneCoordinates(
            easting=np.zeros(1), northing=np.zeros(1), crs=JapanPlaneRectangularZone.ZONE_8
        )
        with pytest.raises(ValueError, match="same CRS"):
            start.distance_to(other)

    def test_rejects_invalid_arrays(self) -> None:
        with pytest.raises(ValueError, match="same shape"):
            PlaneCoordinates(easting=np.zeros(2), northing=np.zeros(1), crs=ZONE_9)
        with pytest.raises(ValueError, match="finite"):
            PlaneCoordinates(easting=np.array([np.nan]), northing=np.zeros(1), crs=ZONE_9)
        with pytest.raises(ValueError, match=r"\(N, 2\)"):
            PlaneCoordinates.from_points(np.zeros((2, 3)), ZONE_9)
        with pytest.raises(ValueError, match="altitude"):
            PlaneCoordinates(
                easting=np.zeros(2),
                northing=np.zeros(2),
                crs=ZONE_9,
                altitude=Altitude(value=np.zeros(1), unit=LengthUnit.M),
            )
