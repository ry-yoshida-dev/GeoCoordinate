# reference_system

## Overview

Coordinate reference systems by EPSG code (`GeodeticCrs`, `JapanPlaneRectangularZone`, `UtmZone`, `WebMercator`), the ellipsoids they are defined on, and the conversions between them: datum transformations, plane projections and geoid heights.

## Components

| Component | Description |
|-----------|-------------|
| [coordinate_reference_system.py](./coordinate_reference_system.py) | `CoordinateReferenceSystem`: the protocol every CRS here satisfies |
| [geodetic_crs.py](./geodetic_crs.py) | `GeodeticCrs`: Tokyo Datum, JGD2000, JGD2011 and WGS 84, with their ellipsoids |
| [ellipsoid.py](./ellipsoid.py) | `Ellipsoid`: GRS80, WGS 84 and Bessel 1841, their axes, flattening and eccentricity |
| [datum_transformation.py](./datum_transformation.py) | `DatumTransformation`: coordinates from one datum to another by the most accurate route of known accuracy, and the grids it lacks for better ones |
| [plane_coordinates.py](./plane_coordinates.py) | `PlaneCoordinates`: eastings and northings on a projected CRS, with the X and Y of Japanese surveying |
| [plane_projection.py](./plane_projection.py) | `PlaneProjection`: coordinates onto any projected CRS and back, from any datum, with meridian convergence and scale factors |
| [japan_plane_rectangular_zone.py](./japan_plane_rectangular_zone.py) | `JapanPlaneRectangularZone`: the nineteen zones of the Japan Plane Rectangular Coordinate System on JGD2011 or Tokyo Datum, their numbers, origins, the zone nearest to a location and whether any zone covers it |
| [utm_zone.py](./utm_zone.py) | `UtmZone`: the zones of the Universal Transverse Mercator system and the zone a location lies in |
| [geoid_model.py](./geoid_model.py) | `GeoidModel`: the Japanese geoids 2011 and 2024 and the global EGM96 and EGM2008, with the grid each is published as |
| [geoid.py](./geoid.py) | `Geoid`: heights of the geoid above the ellipsoid, interpolated from the local grid of a model, and the conversion between altitudes and ellipsoidal heights |
| [web_mercator.py](./web_mercator.py) | `WebMercator`: EPSG:3857 (`PSEUDO_MERCATOR`), the extent of its world square and the latitude where it ends |
| [web_mercator_projection.py](./web_mercator_projection.py) | `WebMercatorProjection`: arrays of WGS 84 longitudes and latitudes to Web Mercator meters and back within the world square, and the ground scale at a latitude on the sphere |

## Examples

```python
from geo_coordinate import GeoCoordinate, GeodeticCrs, JapanPlaneRectangularZone, UtmZone

zone = JapanPlaneRectangularZone.nearest_to(GeoCoordinate.from_degrees(35.652, 139.541))
print(zone, zone.geodetic_crs.label)  # EPSG:6677 JGD2011
print(GeodeticCrs.from_crs(zone.crs))  # None: a plane is not a geodetic CRS
print(UtmZone.containing(GeoCoordinate.from_degrees(48.857, 2.352)))  # EPSG:32631
```

GNSS coordinates on WGS 84 projected onto a zone on JGD2011, with the datum shift included:

```python
from geo_coordinate import GeoCoordinate, GeodeticCrs, JapanPlaneRectangularZone, PlaneProjection

station = GeoCoordinate.from_degrees(35.6812, 139.7671)
projection = PlaneProjection(JapanPlaneRectangularZone(9), source=GeodeticCrs.WGS84)
points = projection.project(station)
print(points.survey_x, points.survey_y)  # [-35367.23...] [-5995.18...]
print(projection.meridian_convergence(station).degree)  # [-0.0386...]
print(projection.unproject(points)[0] == station)  # True
```

Plane coordinates surveyed on Tokyo Datum before 2002, re-expressed on JGD2011:

```python
import numpy as np
from geo_coordinate import GeodeticCrs, JapanPlaneRectangularZone, PlaneCoordinates, PlaneProjection

survey_points = np.array([[-6450.0, -35720.0]])  # eastings and northings in meters
old_zone = JapanPlaneRectangularZone(9, GeodeticCrs.TOKYO)  # EPSG:30169
old_points = PlaneCoordinates.from_points(survey_points, old_zone)
on_jgd2011 = PlaneProjection(old_zone, source=GeodeticCrs.JGD2011).unproject(old_points)
new_points = PlaneProjection(JapanPlaneRectangularZone(9)).project(on_jgd2011)
```
