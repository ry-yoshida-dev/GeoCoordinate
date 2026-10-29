from __future__ import annotations

import warnings
from itertools import pairwise
from typing import Final

import numpy as np
from numpy.typing import NDArray
from pyproj import Transformer
from pyproj._crs import AreaOfUse
from pyproj.transformer import AreaOfInterest, TransformerGroup
from units import Angle, AngleUnit

from ..base import GeoCoordinateBase
from .geodetic_crs import GeodeticCrs

IDENTITY_ACCURACY_METER: Final[float] = 0.0


class DatumTransformation:
    """
    Re-expresses latitudes and longitudes measured on one datum on another.

    The same point has different coordinates on different datums: Tokyo Datum and
    JGD2011 differ by about 400 m around Tokyo. Each step uses the operation PROJ ranks
    first among those of known accuracy, for the area given or else for the whole area
    of use. When no such operation joins the two datums directly, as for Tokyo Datum to
    JGD2011 without the `tky2jgd` grid, which is not openly licensed, the route goes
    through the one other member of `GeodeticCrs` that keeps the summed accuracy
    smallest, and of routes as accurate, the first member in order.

    A step may fall back on a less accurate operation because the grid of a better one
    is not installed, which `missing_grids` names. Without `touhokutaiheiyouoki2011`,
    JGD2000 to JGD2011 is a null operation, exact outside the northern prefectures of
    Honshu but off by up to about 5 m within them, where the 2011 Tohoku earthquake
    moved the ground; its published accuracy of 1 m holds only outside them.

    Only the horizontal position changes; altitudes are carried over unchanged. They do
    not depend on the horizontal datum, although JGD2011 also revised the altitudes of
    the regions the earthquake moved.

    Parameters
    ----------
    source : GeodeticCrs
        The datum the coordinates are measured on.
    target : GeodeticCrs
        The datum to re-express them on.
    area : GeoCoordinateBase | None
        Places around which the coordinates lie, such as a few of them or the corners of
        a dataset. Their extent lets PROJ prefer operations defined for it, such as
        those for Japan over those for Korea. None for the whole area of use.

    Raises
    ------
    ValueError
        If `area` is empty.
    RuntimeError
        If no route of known accuracy joins the two datums.
    """

    def __init__(
        self,
        source: GeodeticCrs,
        target: GeodeticCrs,
        area: GeoCoordinateBase | None = None,
    ) -> None:
        if area is not None and len(area) == 0:
            raise ValueError("area must contain at least one coordinate")
        self._source: GeodeticCrs = source
        self._target: GeodeticCrs = target
        self._area: GeoCoordinateBase | None = area
        self._area_of_interest: AreaOfInterest | None = self._area_of_interest_of(area)
        self._groups: dict[tuple[GeodeticCrs, GeodeticCrs], TransformerGroup] = {}
        self._route: tuple[GeodeticCrs, ...] = self._best_route()
        self._steps: tuple[Transformer, ...] = self._steps_of(self._route)
        self._accuracy_meter: float = sum(
            (step.accuracy for step in self._steps), IDENTITY_ACCURACY_METER
        )
        self._missing_grids: tuple[str, ...] = self._missing_grids_of(self._route)

    @property
    def source(self) -> GeodeticCrs:
        """
        Return the datum the coordinates are measured on.

        Returns
        -------
        GeodeticCrs
            The datum given at construction.
        """
        return self._source

    @property
    def target(self) -> GeodeticCrs:
        """
        Return the datum the coordinates are re-expressed on.

        Returns
        -------
        GeodeticCrs
            The datum given at construction.
        """
        return self._target

    @property
    def route(self) -> tuple[GeodeticCrs, ...]:
        """
        Return the datums the transformation passes through, from source to target.

        Returns
        -------
        tuple[GeodeticCrs, ...]
            `(source, target)` for a direct operation, `(source, via, target)` when it
            goes through another datum, and `(source,)` when both are the same.
        """
        return self._route

    @property
    def accuracy_meter(self) -> float:
        """
        Return the accuracy of the transformation as published in the EPSG database.

        Returns
        -------
        float
            The sum of the accuracies of the steps in meters, an upper bound, zero when
            both datums are the same. It may not hold where `missing_grids` is not
            empty.
        """
        return self._accuracy_meter

    @property
    def missing_grids(self) -> tuple[str, ...]:
        """
        Return the grids of more accurate operations the route could not use.

        Returns
        -------
        tuple[str, ...]
            The file names of the grids, such as `tky2jgd.gsb`, needed by operations
            for the area that are more accurate than the steps taken, sorted. Empty when
            every step is the most accurate operation for the area.
        """
        return self._missing_grids

    def transform[Coordinates: GeoCoordinateBase](self, coordinates: Coordinates) -> Coordinates:
        """
        Re-express coordinates measured on `source` on `target`.

        Parameters
        ----------
        coordinates : Coordinates
            The coordinates on `source`, a `GeoCoordinate` or a `GeoCoordinates`.

        Returns
        -------
        Coordinates
            The coordinates on `target`, of the same type, in degrees, with the
            altitudes carried over.

        Raises
        ------
        ValueError
            If an operation cannot transform a coordinate, such as one outside the
            area its grid covers.
        """
        places: NDArray[np.float64] = np.vstack(
            [coordinates.longitude.degree, coordinates.latitude.degree]
        ).astype(np.float64)
        for step in self._steps:
            places = self._apply(step, places)
        return coordinates.relocated(
            latitude=Angle(value=places[1], unit=AngleUnit.DEGREE),
            longitude=Angle(value=places[0], unit=AngleUnit.DEGREE),
        )

    def inverse(self) -> DatumTransformation:
        """
        Return the transformation from `target` back to `source`.

        Returns
        -------
        DatumTransformation
            The transformation of the swapped datums over the same area.
        """
        return DatumTransformation(source=self._target, target=self._source, area=self._area)

    def _best_route(self) -> tuple[GeodeticCrs, ...]:
        """
        Find the most accurate route of at most two steps between the datums.

        Returns
        -------
        tuple[GeodeticCrs, ...]
            The datums of the route, from source to target.

        Raises
        ------
        RuntimeError
            If no route of known accuracy exists.
        """
        if self._source is self._target:
            return (self._source,)
        direct: tuple[GeodeticCrs, ...] = (self._source, self._target)
        if self._is_available(direct):
            return direct
        routes: list[tuple[GeodeticCrs, ...]] = [
            (self._source, via, self._target)
            for via in GeodeticCrs
            if via is not self._source and via is not self._target
        ]
        available: list[tuple[GeodeticCrs, ...]] = [
            route for route in routes if self._is_available(route)
        ]
        if not available:
            raise RuntimeError(
                f"no transformation of known accuracy joins {self._source.label} "
                + f"and {self._target.label}"
            )
        return min(
            available,
            key=lambda route: sum(step.accuracy for step in self._steps_of(route)),
        )

    def _is_available(self, route: tuple[GeodeticCrs, ...]) -> bool:
        """
        Tell whether every step of a route has an operation of known accuracy.

        Parameters
        ----------
        route : tuple[GeodeticCrs, ...]
            The datums of the route.

        Returns
        -------
        bool
            True when each consecutive pair is joined by such an operation.
        """
        return all(self._operation(start, end) is not None for start, end in pairwise(route))

    def _steps_of(self, route: tuple[GeodeticCrs, ...]) -> tuple[Transformer, ...]:
        """
        Return the operations of an available route.

        Parameters
        ----------
        route : tuple[GeodeticCrs, ...]
            The datums of the route, each step of which is available.

        Returns
        -------
        tuple[Transformer, ...]
            The operation of each consecutive pair.
        """
        steps: list[Transformer] = []
        for start, end in pairwise(route):
            operation: Transformer | None = self._operation(start, end)
            if operation is None:
                raise RuntimeError(f"{start.label} to {end.label} has no operation")
            steps.append(operation)
        return tuple(steps)

    def _missing_grids_of(self, route: tuple[GeodeticCrs, ...]) -> tuple[str, ...]:
        """
        Collect the missing grids of operations more accurate than the steps of a route.

        Parameters
        ----------
        route : tuple[GeodeticCrs, ...]
            The datums of the route, each step of which is available.

        Returns
        -------
        tuple[str, ...]
            The sorted file names of the grids that are not installed.
        """
        grids: set[str] = set()
        for start, end in pairwise(route):
            operation: Transformer | None = self._operation(start, end)
            if operation is None:
                raise RuntimeError(f"{start.label} to {end.label} has no operation")
            for unavailable in self._group(start, end).unavailable_operations:
                if not 0 <= unavailable.accuracy < operation.accuracy:
                    continue
                area_of_use: AreaOfUse | None = unavailable.area_of_use
                if area_of_use is None or self._is_overlapping(
                    west=area_of_use.west,
                    south=area_of_use.south,
                    east=area_of_use.east,
                    north=area_of_use.north,
                ):
                    grids.update(
                        grid.short_name for grid in unavailable.grids if not grid.available
                    )
        return tuple(sorted(grids))

    def _is_overlapping(self, west: float, south: float, east: float, north: float) -> bool:
        """
        Tell whether an extent overlaps the area of interest.

        Parameters
        ----------
        west : float
            The western bound in degrees.
        south : float
            The southern bound in degrees.
        east : float
            The eastern bound in degrees.
        north : float
            The northern bound in degrees.

        Returns
        -------
        bool
            True when the extents overlap, or when there is no area of interest.
        """
        if self._area_of_interest is None:
            return True
        return (
            west <= self._area_of_interest.east_lon_degree
            and self._area_of_interest.west_lon_degree <= east
            and south <= self._area_of_interest.north_lat_degree
            and self._area_of_interest.south_lat_degree <= north
        )

    def _operation(self, start: GeodeticCrs, end: GeodeticCrs) -> Transformer | None:
        """
        Return the operation PROJ ranks first among those of known accuracy.

        Parameters
        ----------
        start : GeodeticCrs
            The datum to transform from.
        end : GeodeticCrs
            The datum to transform to.

        Returns
        -------
        Transformer | None
            The operation, or None when every available one is of unknown accuracy,
            such as a ballpark offset.
        """
        return next(
            (
                operation
                for operation in self._group(start, end).transformers
                if operation.accuracy >= 0
            ),
            None,
        )

    def _group(self, start: GeodeticCrs, end: GeodeticCrs) -> TransformerGroup:
        """
        Return the operations PROJ knows between two datums for the area, cached.

        Parameters
        ----------
        start : GeodeticCrs
            The datum to transform from.
        end : GeodeticCrs
            The datum to transform to.

        Returns
        -------
        TransformerGroup
            The available operations, ranked by PROJ, and the unavailable ones.
        """
        key: tuple[GeodeticCrs, GeodeticCrs] = (start, end)
        if key not in self._groups:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                self._groups[key] = TransformerGroup(
                    start.crs, end.crs, always_xy=True, area_of_interest=self._area_of_interest
                )
        return self._groups[key]

    @staticmethod
    def _area_of_interest_of(area: GeoCoordinateBase | None) -> AreaOfInterest | None:
        """
        Return the extent of the places around which the coordinates lie.

        Parameters
        ----------
        area : GeoCoordinateBase | None
            The places, or None for the whole area of use.

        Returns
        -------
        AreaOfInterest | None
            The bounding box of the places in degrees, or None.
        """
        if area is None:
            return None
        latitude: NDArray[np.float64] = area.latitude.degree.astype(np.float64)
        longitude: NDArray[np.float64] = area.longitude.degree.astype(np.float64)
        return AreaOfInterest(
            west_lon_degree=float(np.min(longitude)),
            south_lat_degree=float(np.min(latitude)),
            east_lon_degree=float(np.max(longitude)),
            north_lat_degree=float(np.max(latitude)),
        )

    @staticmethod
    def _apply(step: Transformer, places: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        Apply one operation to longitudes and latitudes in degrees.

        Parameters
        ----------
        step : Transformer
            The operation.
        places : NDArray[np.float64]
            The longitudes and latitudes, of shape (2, N).

        Returns
        -------
        NDArray[np.float64]
            The transformed longitudes and latitudes, of shape (2, N).

        Raises
        ------
        ValueError
            If any coordinate cannot be transformed.
        """
        longitude, latitude = step.transform(places[0], places[1], errcheck=False)
        transformed: NDArray[np.float64] = np.vstack([longitude, latitude]).astype(np.float64)
        if not np.all(np.isfinite(transformed)):
            raise ValueError(f"{step.description} cannot transform some of the coordinates")
        return transformed
