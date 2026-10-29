import numpy as np
import pytest
from units import LengthUnit

from geo_coordinate import (
    Altitude,
    DatumTransformation,
    GeoCoordinate,
    GeoCoordinates,
    Geodesic,
    GeodeticCrs,
)

TOKYO_STATION = GeoCoordinate.from_degrees(35.6812, 139.7671)


class TestDatumTransformation:
    def test_same_datum_is_an_identity(self) -> None:
        transformation = DatumTransformation(GeodeticCrs.JGD2011, GeodeticCrs.JGD2011)

        assert transformation.route == (GeodeticCrs.JGD2011,)
        assert transformation.accuracy_meter == 0.0
        assert transformation.transform(TOKYO_STATION) == TOKYO_STATION

    def test_tokyo_datum_reaches_jgd2011_through_jgd2000(self) -> None:
        transformation = DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.JGD2011)

        assert transformation.route == (
            GeodeticCrs.TOKYO,
            GeodeticCrs.JGD2000,
            GeodeticCrs.JGD2011,
        )
        assert 0.0 < transformation.accuracy_meter <= 20.0

    def test_tokyo_datum_shifts_by_about_four_hundred_metres_around_tokyo(self) -> None:
        transformation = DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.JGD2011)

        shifted = transformation.transform(TOKYO_STATION)

        shift = Geodesic().distance(TOKYO_STATION, shifted).meter[0]
        assert 400.0 < shift < 500.0
        assert shifted.latitude.degree[0] > TOKYO_STATION.latitude.degree[0]
        assert shifted.longitude.degree[0] < TOKYO_STATION.longitude.degree[0]

    def test_wgs84_and_jgd2011_are_joined_directly(self) -> None:
        transformation = DatumTransformation(GeodeticCrs.WGS84, GeodeticCrs.JGD2011)

        assert transformation.route == (GeodeticCrs.WGS84, GeodeticCrs.JGD2011)

    def test_round_trips_through_the_inverse(self) -> None:
        places = GeoCoordinates.from_degrees(
            latitude=np.array([35.6812, 43.0621, 26.2124]),
            longitude=np.array([139.7671, 141.3544, 127.6809]),
        )
        transformation = DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.JGD2011, area=places)

        restored = transformation.inverse().transform(transformation.transform(places))

        np.testing.assert_allclose(restored.latitude.degree, places.latitude.degree, atol=1e-8)
        np.testing.assert_allclose(restored.longitude.degree, places.longitude.degree, atol=1e-8)

    def test_keeps_the_type_and_altitudes(self) -> None:
        altitude = Altitude(value=np.array([40.0]), unit=LengthUnit.M)
        station = GeoCoordinate.from_degrees(35.6812, 139.7671, altitude)

        shifted = DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.JGD2011).transform(station)

        assert isinstance(shifted, GeoCoordinate)
        assert shifted.altitude == altitude

    def test_inverse_swaps_the_datums(self) -> None:
        inverse = DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.WGS84).inverse()

        assert inverse.source is GeodeticCrs.WGS84
        assert inverse.target is GeodeticCrs.TOKYO

    def test_area_prefers_the_operations_defined_for_it(self) -> None:
        seoul = GeoCoordinate.from_degrees(37.5665, 126.9780)

        for_japan = DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.WGS84, area=TOKYO_STATION)
        for_korea = DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.WGS84, area=seoul)

        assert for_japan.accuracy_meter != for_korea.accuracy_meter

    def test_rejects_an_empty_area(self) -> None:
        empty = GeoCoordinates.from_degrees(latitude=np.zeros(0), longitude=np.zeros(0))
        with pytest.raises(ValueError, match="area"):
            DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.WGS84, area=empty)

    def test_names_the_missing_tohoku_grid_in_northern_honshu(self) -> None:
        sendai = GeoCoordinate.from_degrees(38.2682, 140.8694)
        transformation = DatumTransformation(GeodeticCrs.JGD2000, GeodeticCrs.JGD2011, area=sendai)

        is_grid_missing = transformation.accuracy_meter > 0.2
        assert ("touhokutaiheiyouoki2011.gsb" in transformation.missing_grids) == is_grid_missing

    def test_lacks_no_grid_outside_northern_honshu(self) -> None:
        fukuoka = GeoCoordinate.from_degrees(33.5902, 130.4017)
        transformation = DatumTransformation(GeodeticCrs.JGD2000, GeodeticCrs.JGD2011, area=fukuoka)

        assert transformation.missing_grids == ()

    def test_lacks_no_grid_between_wgs84_and_jgd2011(self) -> None:
        transformation = DatumTransformation(GeodeticCrs.WGS84, GeodeticCrs.JGD2011)

        assert transformation.missing_grids == ()
