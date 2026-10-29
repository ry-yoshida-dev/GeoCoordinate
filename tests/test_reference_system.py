import numpy as np
import pytest
from pyproj import CRS, Transformer

from geo_coordinate import (
    CoordinateReferenceSystem,
    Ellipsoid,
    GeoCoordinate,
    GeodeticCrs,
    JapanPlaneRectangularZone,
    LatitudeHemisphere,
    UtmZone,
    WebMercator,
    WebMercatorProjection,
)

ALL_MEMBERS: list[CoordinateReferenceSystem] = [
    *GeodeticCrs,
    *JapanPlaneRectangularZone,
    *WebMercator,
    UtmZone(number=31, hemisphere=LatitudeHemisphere.NORTH),
    UtmZone(number=56, hemisphere=LatitudeHemisphere.SOUTH),
]


class TestCoordinateReferenceSystem:
    @pytest.mark.parametrize("member", ALL_MEMBERS, ids=str)
    def test_every_member_is_its_own_epsg_code(self, member: CoordinateReferenceSystem) -> None:
        assert member.crs.to_epsg() == member.epsg
        assert str(member) == f"EPSG:{member.epsg}"

    @pytest.mark.parametrize("member", ALL_MEMBERS, ids=str)
    def test_every_member_names_the_datum_it_is_defined_on(
        self, member: CoordinateReferenceSystem
    ) -> None:
        geodetic = member.crs if member.crs.is_geographic else member.crs.geodetic_crs
        assert geodetic is not None
        assert GeodeticCrs.from_crs(geodetic) is member.geodetic_crs


class TestGeodeticCrs:
    def test_identifies_its_members(self) -> None:
        for member in GeodeticCrs:
            assert member.label
            assert member.crs.is_geographic
            assert member.geodetic_crs is member
            assert GeodeticCrs.from_crs(member.crs) is member

    def test_a_projected_crs_is_not_a_geodetic_crs(self) -> None:
        assert GeodeticCrs.from_crs(JapanPlaneRectangularZone.ZONE_9.crs) is None

    def test_a_crs_without_epsg_code_is_not_identified(self) -> None:
        custom = CRS.from_proj4("+proj=longlat +a=6370000 +b=6370000 +no_defs")
        assert GeodeticCrs.from_crs(custom) is None


class TestJapanPlaneRectangularZone:
    def test_central_meridians_follow_the_notice(self) -> None:
        assert JapanPlaneRectangularZone.ZONE_9.central_meridian.degree[0] == pytest.approx(
            139 + 50 / 60
        )
        assert JapanPlaneRectangularZone.ZONE_1.central_meridian.degree[0] == pytest.approx(129.5)
        assert JapanPlaneRectangularZone.ZONE_19.central_meridian.degree[0] == pytest.approx(154.0)

    def test_central_meridians_match_the_epsg_definitions(self) -> None:
        for zone in JapanPlaneRectangularZone:
            operation = zone.crs.coordinate_operation
            assert operation is not None
            longitude = next(
                parameter.value
                for parameter in operation.params
                if parameter.name == "Longitude of natural origin"
            )
            assert zone.central_meridian.degree[0] == pytest.approx(longitude)

    def test_every_zone_is_projected_on_jgd2011(self) -> None:
        for zone in JapanPlaneRectangularZone:
            assert zone.crs.is_projected
            assert zone.geodetic_crs is GeodeticCrs.JGD2011


class TestWebMercator:
    def test_is_epsg_3857_on_wgs84(self) -> None:
        assert WebMercator.PSEUDO_MERCATOR.epsg == 3857
        assert WebMercator.PSEUDO_MERCATOR.geodetic_crs is GeodeticCrs.WGS84

    def test_half_extent_is_reached_at_the_antimeridian(self) -> None:
        projection = WebMercator.PSEUDO_MERCATOR
        transformer = Transformer.from_crs(
            projection.geodetic_crs.crs, projection.crs, always_xy=True
        )
        x, _ = transformer.transform(180.0, 0.0)
        assert x == pytest.approx(projection.half_extent)

    def test_half_extent_is_reached_at_the_latitude_limit(self) -> None:
        projection = WebMercator.PSEUDO_MERCATOR
        transformer = Transformer.from_crs(
            projection.geodetic_crs.crs, projection.crs, always_xy=True
        )
        _, y = transformer.transform(0.0, projection.latitude_limit)
        assert y == pytest.approx(projection.half_extent)


class TestWebMercatorProjection:
    def test_round_trips_places_through_the_plane(self) -> None:
        projection = WebMercatorProjection()
        longitude = np.array([139.541, -0.1276, 0.0])
        latitude = np.array([35.652, 51.5072, 0.0])

        places = projection.unproject(projection.project(longitude, latitude))

        np.testing.assert_allclose(places, np.column_stack([longitude, latitude]), atol=1e-9)

    def test_puts_the_antimeridian_on_the_edge_of_the_world(self) -> None:
        points = WebMercatorProjection().project(np.array([180.0]), np.array([0.0]))

        assert points[0, 0] == pytest.approx(WebMercator.PSEUDO_MERCATOR.half_extent)
        assert points[0, 1] == pytest.approx(0.0)

    def test_ground_scale_shrinks_towards_the_poles(self) -> None:
        assert WebMercatorProjection.ground_scale(0.0) == pytest.approx(1.0)
        assert WebMercatorProjection.ground_scale(60.0) == pytest.approx(0.5)

    def test_rejects_mismatched_arrays(self) -> None:
        with pytest.raises(ValueError, match="same shape"):
            WebMercatorProjection().project(np.array([0.0, 1.0]), np.array([0.0]))
        with pytest.raises(ValueError, match="same shape"):
            WebMercatorProjection().project(np.zeros((1, 2)), np.zeros((1, 2)))
        with pytest.raises(ValueError, match=r"\(N, 2\)"):
            WebMercatorProjection().unproject(np.zeros((2, 3)))

    def test_rejects_places_outside_the_world_square(self) -> None:
        projection = WebMercatorProjection()
        half_extent = WebMercator.PSEUDO_MERCATOR.half_extent
        with pytest.raises(ValueError, match="latitudes must lie within"):
            projection.project(np.array([0.0]), np.array([89.9]))
        with pytest.raises(ValueError, match="points must lie within"):
            projection.unproject(np.array([[0.0, 1.01 * half_extent]]))

    def test_round_trips_the_corner_of_the_world_square(self) -> None:
        projection = WebMercatorProjection()
        latitude_limit = WebMercator.PSEUDO_MERCATOR.latitude_limit
        longitude = np.array([180.0, -180.0])
        latitude = np.array([latitude_limit, -latitude_limit])

        places = projection.unproject(projection.project(longitude, latitude))

        np.testing.assert_allclose(places, np.column_stack([longitude, latitude]), atol=1e-9)


class TestJapanPlaneRectangularZoneOrigin:
    def test_origin_latitudes_match_the_epsg_definitions(self) -> None:
        for zone in JapanPlaneRectangularZone:
            operation = zone.crs.coordinate_operation
            assert operation is not None
            latitude = next(
                parameter.value
                for parameter in operation.params
                if parameter.name == "Latitude of natural origin"
            )
            assert zone.origin_latitude.degree[0] == pytest.approx(latitude)

    def test_origin_is_on_the_central_meridian(self) -> None:
        origin = JapanPlaneRectangularZone.ZONE_9.origin
        assert origin.latitude.degree[0] == pytest.approx(36.0)
        assert origin.longitude.degree[0] == pytest.approx(139 + 50 / 60)

    @pytest.mark.parametrize(
        ("latitude", "longitude", "zone"),
        [
            (35.652, 139.541, JapanPlaneRectangularZone.ZONE_9),
            (43.062, 141.354, JapanPlaneRectangularZone.ZONE_12),
            (33.590, 130.402, JapanPlaneRectangularZone.ZONE_2),
            (26.212, 127.681, JapanPlaneRectangularZone.ZONE_15),
            (34.686, 135.520, JapanPlaneRectangularZone.ZONE_6),
            (27.094, 142.192, JapanPlaneRectangularZone.ZONE_14),
        ],
        ids=["chofu", "sapporo", "fukuoka", "naha", "osaka", "chichijima"],
    )
    def test_nearest_zone_is_the_one_assigned_to_the_city(
        self, latitude: float, longitude: float, zone: JapanPlaneRectangularZone
    ) -> None:
        location = GeoCoordinate.from_degrees(latitude, longitude)
        assert JapanPlaneRectangularZone.nearest_to(location) is zone

    @pytest.mark.parametrize(
        ("latitude", "longitude", "is_covered"),
        [
            (35.652, 139.541, True),
            (26.212, 127.681, True),
            (37.566, 126.978, False),
            (35.180, 129.076, False),
            (25.033, 121.565, False),
            (48.857, 2.352, False),
        ],
        ids=["chofu", "naha", "seoul", "busan", "taipei", "paris"],
    )
    def test_covers_japan_and_not_its_neighbours(
        self, latitude: float, longitude: float, is_covered: bool
    ) -> None:
        location = GeoCoordinate.from_degrees(latitude, longitude)
        assert JapanPlaneRectangularZone.is_covering(location) is is_covered


class TestUtmZone:
    @pytest.mark.parametrize(
        ("latitude", "longitude", "epsg"),
        [
            (48.857, 2.352, 32631),
            (40.713, -74.006, 32618),
            (-33.869, 151.209, 32756),
            (-22.907, -43.173, 32723),
            (0.0, 180.0, 32660),
            (0.0, -180.0, 32601),
        ],
        ids=["paris", "new-york", "sydney", "rio", "antimeridian-east", "antimeridian-west"],
    )
    def test_contains_the_location_in_its_band(
        self, latitude: float, longitude: float, epsg: int
    ) -> None:
        zone = UtmZone.containing(GeoCoordinate.from_degrees(latitude, longitude))
        assert zone.epsg == epsg

    def test_central_meridian_matches_the_epsg_definition(self) -> None:
        for zone in (
            UtmZone(number=number, hemisphere=LatitudeHemisphere.NORTH) for number in (1, 31, 60)
        ):
            operation = zone.crs.coordinate_operation
            assert operation is not None
            longitude = next(
                parameter.value
                for parameter in operation.params
                if parameter.name == "Longitude of natural origin"
            )
            assert zone.central_meridian.degree[0] == pytest.approx(longitude)

    def test_identifies_its_zones_only(self) -> None:
        zone = UtmZone(number=54, hemisphere=LatitudeHemisphere.NORTH)
        assert UtmZone.from_crs(zone.crs) == zone
        assert UtmZone.from_crs(CRS.from_epsg(32754)) == UtmZone(
            number=54, hemisphere=LatitudeHemisphere.SOUTH
        )
        assert UtmZone.from_crs(JapanPlaneRectangularZone.ZONE_9.crs) is None
        assert UtmZone.from_crs(CRS.from_epsg(25831)) is None

    def test_rejects_numbers_outside_the_sixty_zones(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 60"):
            UtmZone(number=0, hemisphere=LatitudeHemisphere.NORTH)

    def test_rejects_the_polar_regions(self) -> None:
        with pytest.raises(ValueError, match="UTM covers latitudes"):
            UtmZone.containing(GeoCoordinate.from_degrees(85.0, 0.0))


class TestEllipsoid:
    @pytest.mark.parametrize("datum", list(GeodeticCrs), ids=str)
    def test_every_datum_names_the_ellipsoid_of_its_epsg_definition(
        self, datum: GeodeticCrs
    ) -> None:
        ellipsoid = datum.crs.ellipsoid
        assert ellipsoid is not None
        assert datum.ellipsoid.semi_major_axis_meter == pytest.approx(ellipsoid.semi_major_metre)
        assert datum.ellipsoid.inverse_flattening == pytest.approx(ellipsoid.inverse_flattening)

    def test_derived_constants(self) -> None:
        grs80 = Ellipsoid.GRS80
        assert grs80.semi_minor_axis_meter == pytest.approx(6_356_752.314140, abs=1e-6)
        assert grs80.eccentricity_squared == pytest.approx(0.00669438002290)
        assert grs80.semi_major_axis.meter[0] == pytest.approx(6_378_137.0)
        assert grs80.mean_radius_meter == pytest.approx(6_371_008.7714, abs=1e-4)


class TestJapanPlaneRectangularZoneNumber:
    def test_numbers_and_numerals(self) -> None:
        assert JapanPlaneRectangularZone.ZONE_9.number == 9
        assert JapanPlaneRectangularZone.ZONE_9.roman_numeral == "IX"
        assert JapanPlaneRectangularZone.ZONE_4.roman_numeral == "IV"
        assert JapanPlaneRectangularZone.ZONE_14.roman_numeral == "XIV"
        assert JapanPlaneRectangularZone.ZONE_19.roman_numeral == "XIX"

    def test_from_number_round_trips(self) -> None:
        for zone in JapanPlaneRectangularZone:
            assert JapanPlaneRectangularZone.from_number(zone.number) is zone

    def test_rejects_numbers_outside_the_nineteen_zones(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 19"):
            JapanPlaneRectangularZone.from_number(20)
