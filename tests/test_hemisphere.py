import pytest

from geo_coordinate import LatitudeHemisphere, LongitudeHemisphere


class TestHemisphere:
    @pytest.mark.parametrize(
        ("abbreviation", "is_negative"),
        [("N", False), ("S", True)],
    )
    def test_parses_latitude_abbreviation(self, abbreviation: str, is_negative: bool) -> None:
        assert LatitudeHemisphere(abbreviation).is_negative is is_negative

    @pytest.mark.parametrize(
        ("abbreviation", "is_negative"),
        [("E", False), ("W", True)],
    )
    def test_parses_longitude_abbreviation(self, abbreviation: str, is_negative: bool) -> None:
        assert LongitudeHemisphere(abbreviation).is_negative is is_negative

    def test_rejects_other_axis_abbreviation(self) -> None:
        with pytest.raises(ValueError):
            LatitudeHemisphere("E")

    @pytest.mark.parametrize(
        ("is_negative", "hemisphere"),
        [(False, LatitudeHemisphere.NORTH), (True, LatitudeHemisphere.SOUTH)],
    )
    def test_builds_latitude_hemisphere_from_sign(
        self, is_negative: bool, hemisphere: LatitudeHemisphere
    ) -> None:
        assert LatitudeHemisphere.from_is_negative(is_negative) is hemisphere
        assert hemisphere.is_negative is is_negative

    @pytest.mark.parametrize(
        ("is_negative", "hemisphere"),
        [(False, LongitudeHemisphere.EAST), (True, LongitudeHemisphere.WEST)],
    )
    def test_builds_longitude_hemisphere_from_sign(
        self, is_negative: bool, hemisphere: LongitudeHemisphere
    ) -> None:
        assert LongitudeHemisphere.from_is_negative(is_negative) is hemisphere
        assert hemisphere.is_negative is is_negative
