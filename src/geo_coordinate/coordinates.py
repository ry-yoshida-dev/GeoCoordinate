from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import overload

import numpy as np
from numpy.typing import NDArray
from units import Angle, AngleUnit, Length, LengthUnit, NumericArray

from .altitude import Altitude
from .base import GeoCoordinateBase
from .coordinate import GeoCoordinate
from .sexagesimal import SexagesimalNotation


@dataclass(eq=False, repr=False)
class GeoCoordinates(GeoCoordinateBase):
    """
    A batch of geographic coordinates on the Earth.

    Holds one coordinate per array element, so a batch of locations is
    processed with vectorized operations. The order of the elements is kept,
    so a batch also describes a path such as a GPS track.

    Parameters
    ----------
    latitude : Angle
        The latitudes, positive north of the equator, within [-90, 90] degrees.
    longitude : Angle
        The longitudes, positive east of the prime meridian, within [-180, 180] degrees.
    altitude : Altitude | None
        The heights relative to mean sea level, or None when unknown.
    """

    def _validate_length(self) -> None:
        pass

    @classmethod
    def from_degrees(
        cls,
        latitude: NumericArray,
        longitude: NumericArray,
        altitude: Altitude | None = None,
    ) -> GeoCoordinates:
        """
        Build coordinates from latitudes and longitudes in decimal degrees.

        Parameters
        ----------
        latitude : NumericArray
            The latitudes in degrees.
        longitude : NumericArray
            The longitudes in degrees.
        altitude : Altitude | None
            The heights relative to mean sea level, or None when unknown.

        Returns
        -------
        GeoCoordinates
            The coordinates.
        """
        return cls(
            latitude=Angle(value=latitude, unit=AngleUnit.DEGREE),
            longitude=Angle(value=longitude, unit=AngleUnit.DEGREE),
            altitude=altitude,
        )

    @classmethod
    def from_sexagesimal(
        cls,
        latitude: Sequence[str],
        longitude: Sequence[str],
        altitude: Altitude | None = None,
    ) -> GeoCoordinates:
        """
        Build coordinates from degrees, minutes, seconds and hemisphere letters.

        Parameters
        ----------
        latitude : Sequence[str]
            The latitudes, such as `35°40'52.27"N`.
        longitude : Sequence[str]
            The longitudes, such as `139°46'1.56"E`.
        altitude : Altitude | None
            The heights relative to mean sea level, or None when unknown.

        Returns
        -------
        GeoCoordinates
            The coordinates, with angles in degrees.

        Raises
        ------
        ValueError
            If a text is not valid sexagesimal notation for its axis, if the
            angles are out of range, or if the lists differ in length.
        """
        return cls(
            latitude=SexagesimalNotation.parse_latitudes(latitude),
            longitude=SexagesimalNotation.parse_longitudes(longitude),
            altitude=altitude,
        )

    @classmethod
    def concatenate(cls, parts: Sequence[GeoCoordinateBase]) -> GeoCoordinates:
        """
        Join single coordinates and batches into one batch, keeping their order.

        Parameters
        ----------
        parts : Sequence[GeoCoordinateBase]
            The coordinates to join. Either all or none of them carry an altitude.

        Returns
        -------
        GeoCoordinates
            The joined coordinates, with angles in degrees and altitudes in meters.

        Raises
        ------
        ValueError
            If `parts` is empty, or if only some of them carry an altitude.
        """
        if len(parts) == 0:
            raise ValueError("parts must contain at least one element")
        latitude: NumericArray = np.concatenate([part.latitude.degree for part in parts])
        longitude: NumericArray = np.concatenate([part.longitude.degree for part in parts])
        altitudes: list[Altitude] = [part.altitude for part in parts if part.altitude is not None]
        altitude: Altitude | None = None
        if len(altitudes) == len(parts):
            altitude_meter: NumericArray = np.concatenate([item.meter for item in altitudes])
            altitude = Altitude(value=altitude_meter, unit=LengthUnit.M)
        elif len(altitudes) > 0:
            raise ValueError("either all or none of parts must carry an altitude")
        return cls.from_degrees(latitude=latitude, longitude=longitude, altitude=altitude)

    @property
    def distance_matrix(self) -> Length:
        """
        Great-circle distances between every pair of coordinates in this batch.

        Returns
        -------
        Length
            The distances in meters, of shape (N, N).
        """
        return self.pairwise_distance_to(self)

    def pairwise_distance_to(self, other: GeoCoordinateBase) -> Length:
        """
        Great-circle distances from every coordinate here to every one in `other`.

        Parameters
        ----------
        other : GeoCoordinateBase
            The coordinates to measure to.

        Returns
        -------
        Length
            The distances in meters, of shape (len(self), len(other)).
        """
        return self._surface_distance(
            self.latitude.radian[:, np.newaxis],
            self.longitude.radian[:, np.newaxis],
            other.latitude.radian[np.newaxis, :],
            other.longitude.radian[np.newaxis, :],
        )

    @property
    def segment_distances(self) -> Length:
        """
        Great-circle distances between consecutive coordinates.

        Returns
        -------
        Length
            The distances in meters, of shape (N - 1,), or empty for fewer
            than two coordinates.
        """
        latitude = self.latitude.radian
        longitude = self.longitude.radian
        return self._surface_distance(latitude[:-1], longitude[:-1], latitude[1:], longitude[1:])

    @property
    def cumulative_distances(self) -> Length:
        """
        Distance travelled along the path up to each coordinate.

        Returns
        -------
        Length
            The distances in meters, of shape (N,), starting at zero.
        """
        cumulative: NumericArray = np.concatenate(
            [np.zeros(min(len(self), 1)), np.cumsum(self.segment_distances.meter)]
        )
        return Length(value=cumulative, unit=LengthUnit.M)

    @property
    def path_length(self) -> Length:
        """
        Total distance along the path through the coordinates in order.

        Returns
        -------
        Length
            The total distance in meters, of shape (1,).
        """
        total: NumericArray = np.array([np.sum(self.segment_distances.meter)])
        return Length(value=total, unit=LengthUnit.M)

    @property
    def segment_bearings(self) -> Angle:
        """
        Initial great-circle bearings from each coordinate to the next.

        Returns
        -------
        Angle
            The bearings in degrees within [0, 360), clockwise from north, of
            shape (N - 1,), or empty for fewer than two coordinates.
        """
        latitude = self.latitude.radian
        longitude = self.longitude.radian
        return self._initial_bearing(latitude[:-1], longitude[:-1], latitude[1:], longitude[1:])

    @property
    def segment_altitude_changes(self) -> Altitude:
        """
        Signed altitude changes between consecutive coordinates.

        Returns
        -------
        Altitude
            The changes in meters, positive uphill, of shape (N - 1,).

        Raises
        ------
        ValueError
            If the coordinates carry no altitude.
        """
        altitude_change: NumericArray = np.diff(self._require_altitude().meter)
        return Altitude(value=altitude_change, unit=LengthUnit.M)

    @property
    def segment_slant_distances(self) -> Length:
        """
        Straight distances between consecutive coordinates including altitude changes.

        Each segment is approximated as the hypotenuse of its great-circle
        distance and its altitude change.

        Returns
        -------
        Length
            The distances in meters, of shape (N - 1,).

        Raises
        ------
        ValueError
            If the coordinates carry no altitude.
        """
        slant: NumericArray = np.hypot(
            self.segment_distances.meter, self.segment_altitude_changes.meter
        )
        return Length(value=slant, unit=LengthUnit.M)

    @property
    def segment_grades(self) -> NumericArray:
        """
        Grades of the segments between consecutive coordinates.

        The grade is the altitude change over the great-circle distance, so
        `0.05` is a 5 percent uphill grade. Segments of zero distance have an
        undefined grade of NaN.

        Returns
        -------
        NumericArray
            The signed grades, of shape (N - 1,).

        Raises
        ------
        ValueError
            If the coordinates carry no altitude.
        """
        rise: NumericArray = self.segment_altitude_changes.meter
        run: NumericArray = self.segment_distances.meter
        is_positive_run: NDArray[np.bool_] = run > 0
        grade: NumericArray = np.full(rise.shape, np.nan)
        grade[is_positive_run] = rise[is_positive_run] / run[is_positive_run]
        return grade

    @property
    def total_ascent(self) -> Length:
        """
        Sum of the altitude gains along the path.

        Returns
        -------
        Length
            The total ascent in meters, of shape (1,).

        Raises
        ------
        ValueError
            If the coordinates carry no altitude.
        """
        gain: NumericArray = np.clip(self.segment_altitude_changes.meter, 0, None)
        return Length(value=np.array([np.sum(gain)]), unit=LengthUnit.M)

    @property
    def total_descent(self) -> Length:
        """
        Sum of the altitude losses along the path, as a positive length.

        Returns
        -------
        Length
            The total descent in meters, of shape (1,).

        Raises
        ------
        ValueError
            If the coordinates carry no altitude.
        """
        loss: NumericArray = np.clip(-self.segment_altitude_changes.meter, 0, None)
        return Length(value=np.array([np.sum(loss)]), unit=LengthUnit.M)

    def _require_altitude(self) -> Altitude:
        """
        Return the altitudes, which the calling operation needs.

        Returns
        -------
        Altitude
            The altitudes of the coordinates.

        Raises
        ------
        ValueError
            If the coordinates carry no altitude.
        """
        if self.altitude is None:
            raise ValueError("this operation requires coordinates with an altitude")
        return self.altitude

    @overload
    def __getitem__(self, index: int | np.integer) -> GeoCoordinate: ...

    @overload
    def __getitem__(
        self, index: slice | NDArray[np.bool_] | NDArray[np.integer]
    ) -> GeoCoordinates: ...

    def __getitem__(
        self, index: int | np.integer | slice | NDArray[np.bool_] | NDArray[np.integer]
    ) -> GeoCoordinate | GeoCoordinates:
        if isinstance(index, int | np.integer):
            selector: slice | NDArray[np.bool_] | NDArray[np.integer] = np.array([index])
        else:
            selector = index
        latitude = Angle(value=self.latitude.value[selector], unit=self.latitude.unit)
        longitude = Angle(value=self.longitude.value[selector], unit=self.longitude.unit)
        altitude: Altitude | None = None
        if self.altitude is not None:
            altitude = Altitude(value=self.altitude.value[selector], unit=self.altitude.unit)
        if isinstance(index, int | np.integer):
            return GeoCoordinate(latitude=latitude, longitude=longitude, altitude=altitude)
        return GeoCoordinates(latitude=latitude, longitude=longitude, altitude=altitude)

    def __iter__(self) -> Iterator[GeoCoordinate]:
        for index in range(len(self)):
            yield self[index]
