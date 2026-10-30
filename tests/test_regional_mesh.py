from __future__ import annotations

from fractions import Fraction

import pytest

from geo_coordinate import GeoCoordinate, RegionalMeshCode, RegionalMeshLevel


def test_level_spans_divide_their_parents() -> None:
    for level in RegionalMeshLevel:
        parent = level.parent
        if parent is None:
            assert level.divisions == 1
            continue
        assert parent.latitude_span == level.latitude_span * level.divisions
        assert parent.longitude_span == level.longitude_span * level.divisions
        assert parent.child is level
    assert RegionalMeshLevel.EIGHTH.child is None


def test_level_from_code_length_rejects_unknown_lengths() -> None:
    assert RegionalMeshLevel.from_code_length(8) is RegionalMeshLevel.THIRD
    with pytest.raises(ValueError):
        RegionalMeshLevel.from_code_length(7)


def test_bounds_of_a_third_level_mesh_are_exact() -> None:
    bounds = RegionalMeshCode("30365001").bounds
    assert bounds.south == Fraction(30, 1) * Fraction(2, 3) + Fraction(5, 12)
    assert bounds.west == Fraction(136) + Fraction(1, 80)
    assert bounds.north == bounds.south + Fraction(1, 120)
    assert bounds.east == bounds.west + Fraction(1, 80)


@pytest.mark.parametrize(
    ("code", "south", "west"),
    [
        (
            "533935991",
            Fraction(53, 1) * Fraction(2, 3) + Fraction(3, 12) + Fraction(9, 120),
            Fraction(139) + Fraction(5, 8) + Fraction(9, 80),
        ),
        (
            "533935992",
            Fraction(53, 1) * Fraction(2, 3) + Fraction(3, 12) + Fraction(9, 120),
            Fraction(139) + Fraction(5, 8) + Fraction(9, 80) + Fraction(1, 160),
        ),
        (
            "533935993",
            Fraction(53, 1) * Fraction(2, 3)
            + Fraction(3, 12)
            + Fraction(9, 120)
            + Fraction(1, 240),
            Fraction(139) + Fraction(5, 8) + Fraction(9, 80),
        ),
        (
            "5339359944",
            Fraction(53, 1) * Fraction(2, 3)
            + Fraction(3, 12)
            + Fraction(9, 120)
            + Fraction(1, 240)
            + Fraction(1, 480),
            Fraction(139) + Fraction(5, 8) + Fraction(9, 80) + Fraction(1, 160) + Fraction(1, 320),
        ),
    ],
)
def test_quarter_digits_take_the_south_west_south_east_north_west_and_north_east(
    code: str, south: Fraction, west: Fraction
) -> None:
    bounds = RegionalMeshCode(code).bounds
    assert (bounds.south, bounds.west) == (south, west)


@pytest.mark.parametrize(
    "code", ["5339", "533935", "53393599", "533935994", "5339359941", "53393599413"]
)
def test_children_tile_their_parent(code: str) -> None:
    mesh = RegionalMeshCode(code)
    children = mesh.children
    if mesh.level is RegionalMeshLevel.EIGHTH:
        assert children == ()
        return
    assert all(child.parent == mesh for child in children)
    area = sum(
        (child.bounds.north - child.bounds.south) * (child.bounds.east - child.bounds.west)
        for child in children
    )
    assert area == (mesh.bounds.north - mesh.bounds.south) * (mesh.bounds.east - mesh.bounds.west)
    assert min(child.bounds.south for child in children) == mesh.bounds.south
    assert max(child.bounds.east for child in children) == mesh.bounds.east


@pytest.mark.parametrize("level", list(RegionalMeshLevel))
def test_containing_finds_the_mesh_of_a_place(level: RegionalMeshLevel) -> None:
    tokyo_station = GeoCoordinate.from_degrees(35.6812, 139.7671)
    code = RegionalMeshCode.containing(tokyo_station, level)
    assert code.level is level
    assert code.bounds.contains(tokyo_station)
    assert RegionalMeshCode.containing(tokyo_station, RegionalMeshLevel.EIGHTH).value.startswith(
        code.value
    )


def test_containing_puts_a_place_on_an_edge_in_the_mesh_to_its_north_east() -> None:
    place = GeoCoordinate.from_degrees(36.0, 139.0)
    assert RegionalMeshCode.containing(place, RegionalMeshLevel.THIRD) == RegionalMeshCode(
        "54390000"
    )
    assert RegionalMeshCode("54390000").bounds.contains(place)
    assert not RegionalMeshCode("53397799").bounds.contains(place)


def test_containing_rejects_places_outside_the_grid() -> None:
    with pytest.raises(ValueError):
        RegionalMeshCode.containing(
            GeoCoordinate.from_degrees(48.857, 2.352), RegionalMeshLevel.THIRD
        )


@pytest.mark.parametrize(
    "code", ["533", "5339a5", "53398599", "533935995", "5339359", "\uff15\uff13\uff13\uff19"]
)
def test_invalid_codes_are_rejected(code: str) -> None:
    with pytest.raises(ValueError):
        RegionalMeshCode(code)
