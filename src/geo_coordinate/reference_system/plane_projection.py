from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from pyproj import Proj, Transformer
from pyproj._transformer import Factors
from units import Angle, AngleUnit

from ..base import GeoCoordinateBase
from ..coordinates import GeoCoordinates
from .coordinate_reference_system import CoordinateReferenceSystem
from .datum_transformation import DatumTransformation
from .geodetic_crs import GeodeticCrs
from .plane_coordinates import PlaneCoordinates


class PlaneProjection:
    """
    Projects geographic coordinates onto the plane of a projected CRS and back.

    Any projected member satisfying `CoordinateReferenceSystem` is accepted, such as a
    `JapanPlaneRectangularZone`, a `UtmZone` or `WebMercator`. The coordinates may be
    measured on another datum than the one the plane is defined on, such as WGS 84 from
    GNSS for a zone on JGD2011; they then pass through a `DatumTransformation` first.

    Coordinates are not restricted to the area of use of the plane: PROJ projects a
    place far from a zone, or beyond the world square of Web Mercator, with growing
    distortion instead of failing. `WebMercatorProjection` rejects places outside its
    world square.

    Parameters
    ----------
    plane : CoordinateReferenceSystem
        The projected CRS to project onto.
    source : GeodeticCrs | None
        The datum the geographic coordinates are measured on. None for the datum the
        plane is defined on.
    area : GeoCoordinateBase | None
        Places around which the coordinates lie, passed on to the `DatumTransformation`.
        None for the whole area of use.

    Raises
    ------
    ValueError
        If `plane` is not a projected CRS.
    RuntimeError
        If no datum transformation of known accuracy joins `source` and the plane.
    """

    def __init__(
        self,
        plane: CoordinateReferenceSystem,
        source: GeodeticCrs | None = None,
        area: GeoCoordinateBase | None = None,
    ) -> None:
        if not plane.crs.is_projected:
            raise ValueError(f"plane must be a projected CRS, given: {plane}")
        self._plane: CoordinateReferenceSystem = plane
        self._source: GeodeticCrs = plane.geodetic_crs if source is None else source
        self._datum: DatumTransformation = DatumTransformation(
            source=self._source, target=plane.geodetic_crs, area=area
        )
        self._datum_inverse: DatumTransformation = self._datum.inverse()
        self._forward: Transformer = Transformer.from_crs(
            plane.geodetic_crs.crs, plane.crs, always_xy=True
        )
        self._inverse: Transformer = Transformer.from_crs(
            plane.crs, plane.geodetic_crs.crs, always_xy=True
        )
        self._factors: Proj = Proj(plane.crs)

    @property
    def plane(self) -> CoordinateReferenceSystem:
        """
        Return the projected CRS the coordinates are projected onto.

        Returns
        -------
        CoordinateReferenceSystem
            The CRS given at construction.
        """
        return self._plane

    @property
    def source(self) -> GeodeticCrs:
        """
        Return the datum the geographic coordinates are measured on.

        Returns
        -------
        GeodeticCrs
            The datum given at construction, or the one of the plane.
        """
        return self._source

    @property
    def datum_transformation(self) -> DatumTransformation:
        """
        Return the transformation from `source` to the datum of the plane.

        Returns
        -------
        DatumTransformation
            An identity when `source` is the datum of the plane.
        """
        return self._datum

    def project(self, coordinates: GeoCoordinateBase) -> PlaneCoordinates:
        """
        Project geographic coordinates onto the plane.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The coordinates, measured on `source`.

        Returns
        -------
        PlaneCoordinates
            The eastings and northings in meters on `plane`, with the altitudes carried
            over.

        Raises
        ------
        ValueError
            If a coordinate cannot be transformed or projected.
        """
        on_plane_datum: GeoCoordinateBase = self._datum.transform(coordinates)
        easting, northing = self._forward.transform(
            on_plane_datum.longitude.degree, on_plane_datum.latitude.degree, errcheck=False
        )
        points: NDArray[np.float64] = np.column_stack([easting, northing]).astype(np.float64)
        if not np.all(np.isfinite(points)):
            raise ValueError(f"some of the coordinates cannot be projected onto {self._plane}")
        return PlaneCoordinates.from_points(points, self._plane, coordinates.altitude)

    def unproject(self, points: PlaneCoordinates) -> GeoCoordinates:
        """
        Turn points on the plane back into geographic coordinates.

        Parameters
        ----------
        points : PlaneCoordinates
            The points on `plane`.

        Returns
        -------
        GeoCoordinates
            The coordinates on `source` in degrees, with the altitudes carried over.

        Raises
        ------
        ValueError
            If the points lie on another CRS, or cannot be unprojected.
        """
        if points.crs.epsg != self._plane.epsg:
            raise ValueError(f"points must lie on {self._plane}, given: {points.crs}")
        longitude, latitude = self._inverse.transform(
            points.easting, points.northing, errcheck=False
        )
        places: NDArray[np.float64] = np.vstack([longitude, latitude]).astype(np.float64)
        if not np.all(np.isfinite(places)):
            raise ValueError(f"some of the points cannot be unprojected from {self._plane}")
        on_plane_datum: GeoCoordinates = GeoCoordinates(
            latitude=Angle(value=places[1], unit=AngleUnit.DEGREE),
            longitude=Angle(value=np.mod(places[0] + 180.0, 360.0) - 180.0, unit=AngleUnit.DEGREE),
            altitude=points.altitude,
        )
        return self._datum_inverse.transform(on_plane_datum)

    def meridian_convergence(self, coordinates: GeoCoordinateBase) -> Angle:
        """
        Angle from true north to the grid north of the plane, at each coordinate.

        Positive when grid north lies clockwise of true north, as east of the central
        meridian of a transverse Mercator zone in the northern hemisphere. A bearing
        from true north becomes one from grid north by subtracting this angle.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The coordinates, measured on `source`.

        Returns
        -------
        Angle
            The convergences in degrees, of shape (N,).

        Raises
        ------
        ValueError
            If a coordinate cannot be transformed onto the datum of the plane.
        """
        on_plane_datum: GeoCoordinateBase = self._datum.transform(coordinates)
        factors: Factors = self._factors.get_factors(
            on_plane_datum.longitude.degree, on_plane_datum.latitude.degree
        )
        convergence: NDArray[np.float64] = np.atleast_1d(
            np.asarray(factors.meridian_convergence, dtype=np.float64)
        )
        return Angle(value=convergence, unit=AngleUnit.DEGREE)

    def scale_factors(self, coordinates: GeoCoordinateBase) -> NDArray[np.float64]:
        """
        Ratio of a short length on the plane to the same length on the ellipsoid.

        For a conformal projection such as transverse Mercator the ratio is the same in
        every direction: 0.9999 on the central meridian of a Japanese zone and 0.9996 on
        that of a UTM zone, growing away from it.

        Parameters
        ----------
        coordinates : GeoCoordinateBase
            The coordinates, measured on `source`.

        Returns
        -------
        NDArray[np.float64]
            The scale factors along the meridian, of shape (N,).

        Raises
        ------
        ValueError
            If a coordinate cannot be transformed onto the datum of the plane.
        """
        on_plane_datum: GeoCoordinateBase = self._datum.transform(coordinates)
        factors: Factors = self._factors.get_factors(
            on_plane_datum.longitude.degree, on_plane_datum.latitude.degree
        )
        return np.atleast_1d(np.asarray(factors.meridional_scale, dtype=np.float64))
