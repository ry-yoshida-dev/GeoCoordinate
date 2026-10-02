import pytest
from pyproj import CRS, Transformer

from geo_coordinate import (
    CoordinateReferenceSystem,
    GeodeticCrs,
    JapanPlaneRectangularZone,
    WebMercator,
)

ALL_MEMBERS: list[CoordinateReferenceSystem] = [
    *GeodeticCrs,
    *JapanPlaneRectangularZone,
    *WebMercator,
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
