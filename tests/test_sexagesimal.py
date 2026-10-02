import numpy as np
import pytest
from units import Angle, AngleUnit

from geo_coordinate import SexagesimalNotation


class TestSexagesimalNotation:
    @pytest.mark.parametrize(
        ("text", "degree"),
        [
            ("35°40'52.27\"N", 35 + 40 / 60 + 52.27 / 3600),
            ("33°52'7.68\"S", -(33 + 52 / 60 + 7.68 / 3600)),
            ("N35°40'52.27\"", 35 + 40 / 60 + 52.27 / 3600),
            (" 35 ° 40 ' 52.27 \" n ", 35 + 40 / 60 + 52.27 / 3600),
            ("35°40\u203252.27\u2033N", 35 + 40 / 60 + 52.27 / 3600),
            ("35°40.5'N", 35 + 40.5 / 60),
            ("35.5°S", -35.5),
            ("0°0'0\"S", 0.0),
        ],
    )
    def test_parses_latitude(self, text: str, degree: float) -> None:
        latitude = SexagesimalNotation.parse_latitudes([text])

        assert latitude.unit == AngleUnit.DEGREE
        assert latitude.degree == pytest.approx(np.array([degree]))

    def test_parses_longitudes_in_order(self) -> None:
        longitude = SexagesimalNotation.parse_longitudes(["139°46'1.56\"E", "0°30'W"])

        assert longitude.degree == pytest.approx(np.array([139 + 46 / 60 + 1.56 / 3600, -0.5]))

    def test_parses_empty_list(self) -> None:
        assert len(SexagesimalNotation.parse_latitudes([])) == 0

    @pytest.mark.parametrize(
        ("text", "message"),
        [
            ("35°40'52\"", "exactly one hemisphere letter"),
            ("N35°40'52\"S", "exactly one hemisphere letter"),
            ("35°40'52\"E", "LatitudeHemisphere"),
            ("35°60'0\"N", "less than 60"),
            ("35°40'60\"N", "less than 60"),
            ("35.5°40'N", "only the last component"),
            ("35°40.5'10\"N", "only the last component"),
            ('35°10"N', "seconds require minutes"),
            ("-35°40'N", "invalid sexagesimal notation"),
            ("35 40 52 N", "invalid sexagesimal notation"),
            ("\uff13\uff15°N", "invalid sexagesimal notation"),
        ],
    )
    def test_rejects_invalid_latitude(self, text: str, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            SexagesimalNotation.parse_latitudes([text])

    def test_rejects_latitude_letter_on_longitude(self) -> None:
        with pytest.raises(ValueError, match="LongitudeHemisphere"):
            SexagesimalNotation.parse_longitudes(["35°N"])

    def test_formats_latitudes(self) -> None:
        latitude = Angle(value=np.array([35.681186, -33.8688, 0.0]), unit=AngleUnit.DEGREE)

        texts = SexagesimalNotation.format_latitudes(latitude)

        assert texts == ("35°40'52.27\"N", "33°52'7.68\"S", "0°0'0.00\"N")

    def test_formats_longitudes_from_radians(self) -> None:
        longitude = Angle(value=np.array([-np.pi / 2]), unit=AngleUnit.RADIAN)

        assert SexagesimalNotation.format_longitudes(longitude, 0) == ("90°0'0\"W",)

    def test_carries_rounded_seconds(self) -> None:
        latitude = Angle(value=np.array([10 + 59 / 60 + 59.996 / 3600]), unit=AngleUnit.DEGREE)

        assert SexagesimalNotation.format_latitudes(latitude) == ("11°0'0.00\"N",)

    def test_drops_sign_rounded_to_zero(self) -> None:
        latitude = Angle(value=np.array([-1e-9]), unit=AngleUnit.DEGREE)

        assert SexagesimalNotation.format_latitudes(latitude) == ("0°0'0.00\"N",)

    def test_round_trips(self) -> None:
        latitude = Angle(value=np.array([12.3456789, -45.6789]), unit=AngleUnit.DEGREE)

        texts = SexagesimalNotation.format_latitudes(latitude, 6)

        assert SexagesimalNotation.parse_latitudes(texts) == latitude

    @pytest.mark.parametrize("seconds_decimals", [-1, 7])
    def test_rejects_seconds_decimals_out_of_range(self, seconds_decimals: int) -> None:
        latitude = Angle(value=np.array([1.0]), unit=AngleUnit.DEGREE)

        with pytest.raises(ValueError, match="seconds_decimals"):
            SexagesimalNotation.format_latitudes(latitude, seconds_decimals)
