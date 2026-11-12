import numpy as np
import pytest
from units import Length, LengthUnit, MetricPrefix

from geo_coordinate import Altitude


class TestAltitude:
    def test_is_not_changed_by_its_source_array(self) -> None:
        value = np.array([1.0, 2.0])
        altitude = Altitude(value=value, unit=LengthUnit.M)

        value[0] = np.inf

        assert altitude.meter.tolist() == [1.0, 2.0]
        with pytest.raises(ValueError, match="read-only"):
            altitude.value[0] = np.inf

    def test_broadcasts_a_single_altitude(self) -> None:
        altitude = Altitude(value=np.array([1.5]), unit=LengthUnit.M, prefix=MetricPrefix.KILO)

        broadcast = altitude.broadcast_to(3)

        assert broadcast.prefix is MetricPrefix.KILO
        assert broadcast.meter.tolist() == [1500.0, 1500.0, 1500.0]

    def test_rejects_broadcast_to_another_length(self) -> None:
        altitude = Altitude(value=np.array([1.0, 2.0]), unit=LengthUnit.M)

        with pytest.raises(ValueError):
            altitude.broadcast_to(3)

    def test_holds_signed_value(self) -> None:
        altitude = Altitude(
            value=np.array([1.5, -0.2]), unit=LengthUnit.M, prefix=MetricPrefix.KILO
        )

        assert np.allclose(altitude.meter, np.array([1500.0, -200.0]))
        assert altitude.is_below_sea_level.tolist() == [False, True]

    def test_builds_from_magnitude(self) -> None:
        magnitude = Length(value=np.array([40.5, 12.0]), unit=LengthUnit.M)

        altitude = Altitude.from_magnitude(magnitude, np.array([True, False]))

        assert altitude == Altitude(value=np.array([-40.5, 12.0]), unit=LengthUnit.M)

    def test_returns_unsigned_magnitude(self) -> None:
        altitude = Altitude(value=np.array([-40.5]), unit=LengthUnit.M)

        assert altitude.magnitude == Length(value=np.array([40.5]), unit=LengthUnit.M)

    def test_keeps_prefix_of_magnitude(self) -> None:
        magnitude = Length(value=np.array([1.5]), unit=LengthUnit.M, prefix=MetricPrefix.KILO)

        altitude = Altitude.from_magnitude(magnitude, np.array([True]))

        assert np.allclose(altitude.meter, np.array([-1500.0]))
        assert altitude.magnitude == magnitude

    def test_rejects_prefix_on_unit_without_prefixes(self) -> None:
        with pytest.raises(ValueError, match="takes no prefix"):
            Altitude(value=np.array([1.0]), unit=LengthUnit.FOOT, prefix=MetricPrefix.KILO)

    def test_rejects_mismatched_shapes(self) -> None:
        magnitude = Length(value=np.array([1.0]), unit=LengthUnit.M)

        with pytest.raises(ValueError, match="same shape"):
            Altitude.from_magnitude(magnitude, np.array([True, False]))

    def test_requires_1d(self) -> None:
        with pytest.raises(ValueError, match="1D"):
            Altitude(value=np.array([[1.0]]), unit=LengthUnit.M)

    @pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
    def test_rejects_non_finite(self, value: float) -> None:
        with pytest.raises(ValueError, match="finite"):
            Altitude(value=np.array([1.0, value]), unit=LengthUnit.M)

    def test_requires_matching_shape_for_equality(self) -> None:
        single = Altitude(value=np.array([1.0]), unit=LengthUnit.M)
        repeated = Altitude(value=np.array([1.0, 1.0]), unit=LengthUnit.M)

        assert single != repeated
