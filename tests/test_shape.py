import json

import numpy as np
import pytest
from pyproj import Geod
from units import LengthUnit

from geo_coordinate import (
    Altitude,
    GeoBoundingBox,
    GeoCoordinate,
    GeoCoordinates,
    Geodesic,
    GeoJsonGeometry,
    GeoLinearRing,
    GeoLineString,
    GeoMultiPolygon,
    GeoPolygon,
)


def coordinates(*longitude_latitude: tuple[float, float]) -> GeoCoordinates:
    """Coordinates from (longitude, latitude) pairs, in the order GeoJSON writes them."""
    return GeoCoordinates.from_degrees(
        latitude=np.array([latitude for _, latitude in longitude_latitude]),
        longitude=np.array([longitude for longitude, _ in longitude_latitude]),
    )


def square(west: float, south: float, size: float) -> GeoLinearRing:
    """A counterclockwise square ring."""
    return GeoLinearRing(
        vertices=coordinates(
            (west, south), (west + size, south), (west + size, south + size), (west, south + size)
        )
    )


OUTER = square(139.0, 35.0, 1.0)
HOLE = square(139.4, 35.4, 0.2).oriented(is_counterclockwise=False)
SQUARE_WITH_HOLE = GeoPolygon(exterior=OUTER, holes=(HOLE,))
ISLAND = GeoPolygon(exterior=square(139.0, 33.0, 0.1))
L_SHAPE = GeoPolygon(
    exterior=GeoLinearRing(
        vertices=coordinates((0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0), (1.0, 2.0), (0.0, 2.0))
    )
)


class TestGeoLineString:
    def test_length_matches_the_path_of_its_vertices(self) -> None:
        vertices = coordinates((139.7671, 35.6812), (139.7454, 35.6586), (139.7387, 35.6295))

        line = GeoLineString(vertices=vertices)

        assert line.length.meter[0] == pytest.approx(vertices.path_length.meter[0])
        assert len(line) == 3

    def test_needs_two_vertices(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            _ = GeoLineString(vertices=coordinates((139.0, 35.0)))

    def test_reversed_runs_the_other_way(self) -> None:
        line = GeoLineString(vertices=coordinates((139.0, 35.0), (140.0, 36.0)))

        reversed_line = line.reversed()

        assert reversed_line.vertices[0] == line.vertices[-1]
        assert reversed_line.reversed() == line

    def test_bounding_box_encloses_the_vertices(self) -> None:
        line = GeoLineString(vertices=coordinates((140.0, 35.0), (139.0, 36.0)))

        box = line.bounding_box

        assert (box.south_degree, box.west_degree, box.north_degree, box.east_degree) == (
            35.0,
            139.0,
            36.0,
            140.0,
        )


class TestGeoLinearRing:
    def test_repeated_closing_vertex_is_dropped(self) -> None:
        closed = GeoLinearRing(vertices=OUTER.closed_vertices)

        assert closed == OUTER
        assert len(closed) == 4
        assert len(closed.closed_vertices) == 5

    def test_close_corners_of_a_small_ring_are_kept(self) -> None:
        small = GeoLinearRing(
            vertices=coordinates(
                (139.917107432, 31.886805315),
                (139.917087639, 31.886788919),
                (139.917083061, 31.886814613),
                (139.917107432, 31.886805315),
            )
        )

        assert len(small) == 3
        assert len(small.oriented(is_counterclockwise=not small.is_counterclockwise)) == 3

    def test_needs_three_corners(self) -> None:
        with pytest.raises(ValueError, match="at least 3"):
            _ = GeoLinearRing(vertices=coordinates((0.0, 0.0), (1.0, 0.0), (0.0, 0.0)))

    def test_orientation(self) -> None:
        clockwise = OUTER.oriented(is_counterclockwise=False)

        assert OUTER.is_counterclockwise
        assert not clockwise.is_counterclockwise
        assert OUTER.oriented(is_counterclockwise=True) is OUTER

    def test_perimeter_on_a_sphere(self) -> None:
        assert OUTER.perimeter.meter[0] == pytest.approx(OUTER.closed_vertices.path_length.meter[0])

    def test_contains_in_chunks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(GeoLinearRing, "CONTAINS_CHUNK_SIZE", 4)
        axis = np.linspace(-0.45, 2.55, 13)
        longitude, latitude = np.meshgrid(axis, axis)
        grid = GeoCoordinates.from_degrees(latitude=latitude.ravel(), longitude=longitude.ravel())
        expected = (
            (grid.longitude.degree > 0)
            & (grid.latitude.degree > 0)
            & (grid.longitude.degree < 2)
            & (grid.latitude.degree < 2)
            & ~((grid.longitude.degree > 1) & (grid.latitude.degree > 1))
        )

        assert np.array_equal(L_SHAPE.exterior.contains(grid), expected)


class TestGeoPolygon:
    def test_contains_excludes_holes(self) -> None:
        places = coordinates((139.1, 35.1), (139.5, 35.5), (138.9, 35.5), (139.9, 35.9))

        assert SQUARE_WITH_HOLE.contains(places).tolist() == [True, False, False, True]

    def test_contains_a_single_coordinate(self) -> None:
        tokyo = GeoCoordinate.from_degrees(35.6812, 139.7671)

        assert SQUARE_WITH_HOLE.contains(tokyo).tolist() == [True]

    def test_concave_outline(self) -> None:
        places = coordinates((0.5, 1.5), (1.5, 1.5), (1.5, 0.5))

        assert L_SHAPE.contains(places).tolist() == [True, False, True]

    def test_oriented_follows_rfc_7946(self) -> None:
        polygon = GeoPolygon(
            exterior=OUTER.oriented(is_counterclockwise=False),
            holes=(HOLE.oriented(is_counterclockwise=True),),
        )

        oriented = polygon.oriented()

        assert oriented.exterior.is_counterclockwise
        assert not oriented.holes[0].is_counterclockwise
        assert oriented.rings == (oriented.exterior, *oriented.holes)


class TestGeoMultiPolygon:
    def test_contains_any_part(self) -> None:
        prefecture = GeoMultiPolygon(polygons=(SQUARE_WITH_HOLE, ISLAND))
        places = coordinates((139.1, 35.1), (139.05, 33.05), (139.5, 35.5), (139.5, 34.0))

        assert prefecture.contains(places).tolist() == [True, True, False, False]

    def test_bounding_box_encloses_every_part(self) -> None:
        box = GeoMultiPolygon(polygons=(SQUARE_WITH_HOLE, ISLAND)).bounding_box

        assert box == GeoBoundingBox(
            south_west=GeoCoordinate.from_degrees(33.0, 139.0),
            north_east=GeoCoordinate.from_degrees(36.0, 140.0),
        )

    def test_needs_a_polygon(self) -> None:
        with pytest.raises(ValueError, match="at least one polygon"):
            _ = GeoMultiPolygon(polygons=())


class TestGeoBoundingBox:
    def test_rejects_inverted_corners(self) -> None:
        with pytest.raises(ValueError, match="must not lie south or west"):
            _ = GeoBoundingBox(
                south_west=GeoCoordinate.from_degrees(36.0, 139.0),
                north_east=GeoCoordinate.from_degrees(35.0, 140.0),
            )

    def test_contains_edges(self) -> None:
        box = OUTER.bounding_box

        assert box.contains(coordinates((139.0, 35.0), (140.0, 36.0), (140.1, 35.5))).tolist() == [
            True,
            True,
            False,
        ]


class TestGeodesicArea:
    def test_area_matches_pyproj(self) -> None:
        expected, _ = Geod(ellps="GRS80").polygon_area_perimeter(
            [139.0, 140.0, 140.0, 139.0], [35.0, 35.0, 36.0, 36.0]
        )

        assert Geodesic().area(GeoPolygon(exterior=OUTER)).square_meter[0] == pytest.approx(
            expected
        )

    def test_area_ignores_orientation_and_subtracts_holes(self) -> None:
        geodesic = Geodesic()
        clockwise = GeoPolygon(exterior=OUTER.oriented(is_counterclockwise=False))
        hole_area = geodesic.area(GeoPolygon(exterior=HOLE)).square_meter[0]

        assert geodesic.area(clockwise).square_meter[0] == pytest.approx(
            geodesic.area(GeoPolygon(exterior=OUTER)).square_meter[0]
        )
        assert geodesic.area(SQUARE_WITH_HOLE).square_meter[0] == pytest.approx(
            geodesic.area(clockwise).square_meter[0] - hole_area
        )

    def test_area_of_a_multi_polygon_sums_its_parts(self) -> None:
        geodesic = Geodesic()

        area = geodesic.area(GeoMultiPolygon(polygons=(SQUARE_WITH_HOLE, ISLAND))).square_meter[0]

        assert area == pytest.approx(
            geodesic.area(SQUARE_WITH_HOLE).square_meter[0] + geodesic.area(ISLAND).square_meter[0]
        )

    def test_perimeter_counts_holes(self) -> None:
        geodesic = Geodesic()

        perimeter = geodesic.perimeter(SQUARE_WITH_HOLE)

        assert perimeter.meter[0] == pytest.approx(
            geodesic.perimeter(OUTER).meter[0] + geodesic.perimeter(HOLE).meter[0]
        )
        assert perimeter.meter[0] == pytest.approx(
            geodesic.perimeter(GeoMultiPolygon(polygons=(SQUARE_WITH_HOLE,))).meter[0]
        )


class TestGeoJsonGeometry:
    def test_polygon_round_trip(self) -> None:
        encoded = GeoJsonGeometry.encode(SQUARE_WITH_HOLE)

        decoded = GeoJsonGeometry.decode(json.loads(json.dumps(encoded)))

        assert encoded["type"] == "Polygon"
        assert decoded == SQUARE_WITH_HOLE

    def test_writes_closed_rings(self) -> None:
        encoded = GeoJsonGeometry.encode(GeoPolygon(exterior=OUTER))

        assert encoded["coordinates"] == [
            [[139.0, 35.0], [140.0, 35.0], [140.0, 36.0], [139.0, 36.0], [139.0, 35.0]]
        ]

    def test_multi_polygon_round_trip(self) -> None:
        prefecture = GeoMultiPolygon(polygons=(SQUARE_WITH_HOLE, ISLAND))

        assert GeoJsonGeometry.decode(GeoJsonGeometry.encode(prefecture)) == prefecture

    def test_line_string_keeps_altitudes(self) -> None:
        track = GeoLineString(
            vertices=GeoCoordinates.from_degrees(
                latitude=np.array([35.0, 36.0]),
                longitude=np.array([139.0, 140.0]),
                altitude=Altitude(value=np.array([3.0, -2.5]), unit=LengthUnit.M),
            )
        )

        encoded = GeoJsonGeometry.encode(track)

        assert encoded["coordinates"] == [[139.0, 35.0, 3.0], [140.0, 36.0, -2.5]]
        assert GeoJsonGeometry.decode(encoded) == track

    def test_reads_integer_coordinates(self) -> None:
        line = GeoJsonGeometry.decode({"type": "LineString", "coordinates": [[139, 35], [140, 36]]})

        assert isinstance(line, GeoLineString)
        assert line.vertices.longitude.degree.tolist() == [139.0, 140.0]

    @pytest.mark.parametrize(
        "geometry",
        [
            [],
            {"coordinates": [[0, 0], [1, 1]]},
            {"type": "Point", "coordinates": [0, 0]},
            {"type": "LineString", "coordinates": [[0, 0], [1, 1, 2]]},
            {"type": "LineString", "coordinates": [[0, 0], [True, 1]]},
            {"type": "LineString", "coordinates": [[0, 0], [1]]},
            {"type": "LineString", "coordinates": [[0, 0]]},
            {"type": "LineString", "coordinates": [[0, 0], [1, 91]]},
            {"type": "Polygon", "coordinates": []},
            {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [0, 0]]]},
            {"type": "MultiPolygon", "coordinates": []},
        ],
    )
    def test_rejects_malformed_geometries(self, geometry: object) -> None:
        with pytest.raises(ValueError):
            _ = GeoJsonGeometry.decode(json.loads(json.dumps(geometry)))
