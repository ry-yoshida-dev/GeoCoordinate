import numpy as np
import pytest
from units import Angle, AngleUnit

from geo_coordinate import Bearing, NorthReference


class TestBearing:
    def test_defaults_to_true_north(self) -> None:
        bearing = Bearing(angle=Angle(value=np.array([45.0]), unit=AngleUnit.DEGREE))

        assert bearing.reference is NorthReference.TRUE
        assert bearing.is_true_north

    @pytest.mark.parametrize(
        ("degree", "expected"), [(-90.0, 270.0), (360.0, 0.0), (725.0, 5.0), (90.5, 90.5)]
    )
    def test_wraps_degrees_into_a_turn(self, degree: float, expected: float) -> None:
        bearing = Bearing.from_degrees(degree, NorthReference.MAGNETIC)

        assert bearing.degree == pytest.approx([expected])
        assert bearing.reference is NorthReference.MAGNETIC
        assert not bearing.is_true_north

    def test_wraps_radians(self) -> None:
        angle = Angle(value=np.array([-np.pi / 2]), unit=AngleUnit.RADIAN)

        bearing = Bearing.wrapped(angle)

        assert bearing.degree == pytest.approx([270.0])
        assert bearing.radian == pytest.approx([3 * np.pi / 2])

    @pytest.mark.parametrize("degree", [-1.0, 360.0, np.nan, np.inf])
    def test_rejects_angles_outside_a_turn(self, degree: float) -> None:
        with pytest.raises(ValueError, match="bearing must be"):
            Bearing(angle=Angle(value=np.array([degree]), unit=AngleUnit.DEGREE))

    def test_rejects_angles_that_are_not_1d(self) -> None:
        angle = Angle(value=np.array([0.0, 90.0]), unit=AngleUnit.DEGREE)
        angle.value = np.array([[0.0, 90.0]])

        with pytest.raises(ValueError, match="1D"):
            Bearing(angle=angle)

    @pytest.mark.parametrize("unit", list(AngleUnit))
    def test_accepts_largest_angle_below_a_turn_in_any_unit(self, unit: AngleUnit) -> None:
        full_turn = Angle(value=np.array([360.0]), unit=AngleUnit.DEGREE)
        full_turn.convert_unit(unit)
        largest = np.nextafter(full_turn.value, 0.0)

        bearing = Bearing(angle=Angle(value=largest, unit=unit))

        assert bearing.degree[0] < 360.0

    def test_rejects_non_finite_degrees_when_wrapping(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            Bearing.from_degrees(np.nan)

    @pytest.mark.parametrize(
        ("letter", "reference"), [("T", NorthReference.TRUE), ("M", NorthReference.MAGNETIC)]
    )
    def test_parses_exif_reference_letters(self, letter: str, reference: NorthReference) -> None:
        assert NorthReference(letter) is reference

    def test_counts_its_directions(self) -> None:
        angle = Angle(value=np.array([0.0, 90.0, 180.0]), unit=AngleUnit.DEGREE)

        assert len(Bearing(angle=angle)) == 3
