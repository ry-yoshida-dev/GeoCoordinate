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
