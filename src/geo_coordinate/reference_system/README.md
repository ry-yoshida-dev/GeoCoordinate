# reference_system

## Overview

Coordinate reference systems (CRSs) by EPSG code. Every member is its EPSG code, prints as
`EPSG:<code>`, and satisfies `CoordinateReferenceSystem`: `epsg`, `crs` (a `pyproj.CRS`) and
`geodetic_crs` (the datum it is defined on).

Latitudes and longitudes mean nothing exact without the datum they are measured on: the same
point differs by about 400 m between Tokyo Datum and JGD2011. `GeodeticCrs` names the
geographic CRSs Japanese data is published in. Lengths and areas need a plane instead of
degrees, which `JapanPlaneRectangularZone` provides for surveying in Japan, `UtmZone` anywhere
else, and `WebMercator` for web maps.

Coordinates move between these systems by `DatumTransformation`, from one datum to another,
and `PlaneProjection`, from a datum onto a plane and back. The datum shift from Tokyo Datum to
JGD2011 needs the `tky2jgd` grid, which PROJ does not distribute, so `DatumTransformation`
takes the most accurate route of known accuracy instead, through JGD2000 at about 10 m; it
never falls back to an offset of unknown accuracy. Without the `touhokutaiheiyouoki2011` grid,
JGD2000 to JGD2011 is a null operation, off by up to about 5 m in the northern prefectures of
Honshu that the 2011 Tohoku earthquake moved. `missing_grids` names the grids of more accurate
operations a transformation could not use for its area. Each datum names its `Ellipsoid`.

| CRS | Kind | Defined on |
| --- | --- | --- |
| `GeodeticCrs` | geographic, degrees | its own datum |
| `JapanPlaneRectangularZone` | projected, meters, conformal within ~1/10000 | JGD2011 |
| `UtmZone` | projected, meters, conformal within ~1/1000 | WGS 84 |
| `WebMercator` | projected, meters, for display only | WGS 84 |

Heights come in two kinds. GNSS and 3D Tiles give heights above the ellipsoid, while maps,
DEMs and surveys give heights above mean sea level, whose surface is the geoid. The geoid
lies 30 to 45 m above the ellipsoid in Japan and varies from place to place, so the two are
converted by the height of the geoid at each place. `GeoidModel` names the models PROJ
publishes as grids, and `Geoid` reads one grid, downloaded beforehand from
`GeoidModel.grid_url`, and interpolates its heights.

## Components

| Component | Description |
|-----------|-------------|
| [coordinate_reference_system.py](./coordinate_reference_system.py) | `CoordinateReferenceSystem`: the protocol every CRS here satisfies |
| [geodetic_crs.py](./geodetic_crs.py) | `GeodeticCrs`: Tokyo Datum, JGD2000, JGD2011 and WGS 84, with their ellipsoids |
| [ellipsoid.py](./ellipsoid.py) | `Ellipsoid`: GRS80, WGS 84 and Bessel 1841, their axes, flattening and eccentricity |
| [datum_transformation.py](./datum_transformation.py) | `DatumTransformation`: coordinates from one datum to another by the most accurate route of known accuracy, and the grids it lacks for better ones |
| [plane_coordinates.py](./plane_coordinates.py) | `PlaneCoordinates`: eastings and northings on a projected CRS, with the X and Y of Japanese surveying |
| [plane_projection.py](./plane_projection.py) | `PlaneProjection`: coordinates onto any projected CRS and back, from any datum, with meridian convergence and scale factors |
| [japan_plane_rectangular_zone.py](./japan_plane_rectangular_zone.py) | `JapanPlaneRectangularZone`: the nineteen zones of the Japan Plane Rectangular Coordinate System, their numbers, origins, the zone nearest to a location and whether any zone covers it |
| [utm_zone.py](./utm_zone.py) | `UtmZone`: the zones of the Universal Transverse Mercator system and the zone a location lies in |
| [geoid_model.py](./geoid_model.py) | `GeoidModel`: the Japanese geoids 2011 and 2024 and the global EGM96 and EGM2008, with the grid each is published as |
| [geoid.py](./geoid.py) | `Geoid`: heights of the geoid above the ellipsoid, interpolated from the local grid of a model, and the conversion between altitudes and ellipsoidal heights |
| [web_mercator.py](./web_mercator.py) | `WebMercator`: EPSG:3857 (`PSEUDO_MERCATOR`), the extent of its world square and the latitude where it ends |
| [web_mercator_projection.py](./web_mercator_projection.py) | `WebMercatorProjection`: arrays of WGS 84 longitudes and latitudes to Web Mercator meters and back within the world square, and the ground scale at a latitude on the sphere |

## Examples

```python
import geopandas as gpd

from geo_coordinate import CoordinateReferenceSystem, GeodeticCrs, JapanPlaneRectangularZone


def measure_on(frame: gpd.GeoDataFrame, plane: CoordinateReferenceSystem) -> float:
    return float(frame.to_crs(plane.crs).length.sum())


zone = JapanPlaneRectangularZone.ZONE_9
print(zone, zone.geodetic_crs.label)  # EPSG:6677 JGD2011
print(GeodeticCrs.from_crs(zone.crs))  # None: a plane is not a geodetic CRS
```

A dataset is measured with little distortion in the zone whose origin is nearest to it.
`nearest_to` chooses that zone, which near the border of a prefecture may differ from the zone
the Survey Act assigns:

```python
from geo_coordinate import GeoCoordinate, JapanPlaneRectangularZone

chofu = GeoCoordinate.from_degrees(35.652, 139.541)
print(JapanPlaneRectangularZone.nearest_to(chofu))  # EPSG:6677
```

Outside the areas the zones are meant for, a dataset is measured in the UTM zone it lies in:

```python
from geo_coordinate import GeoCoordinate, JapanPlaneRectangularZone, UtmZone

paris = GeoCoordinate.from_degrees(48.857, 2.352)
print(JapanPlaneRectangularZone.is_covering(paris))  # False
print(UtmZone.containing(paris))  # EPSG:32631
```

GNSS coordinates on WGS 84 are projected onto a zone on JGD2011 with the datum shift included.
Japanese surveying names the northing X and the easting Y, and a bearing from true north
becomes one from grid north by subtracting the meridian convergence:

```python
from geo_coordinate import GeoCoordinate, GeodeticCrs, JapanPlaneRectangularZone, PlaneProjection

station = GeoCoordinate.from_degrees(35.6812, 139.7671)
projection = PlaneProjection(JapanPlaneRectangularZone.ZONE_9, source=GeodeticCrs.WGS84)
points = projection.project(station)
print(points.survey_x, points.survey_y)  # [-35367.23...] [-5995.18...]
print(projection.meridian_convergence(station).degree)  # [-0.0386...]
print(projection.unproject(points)[0] == station)  # True
```

Coordinates published on Tokyo Datum are moved onto JGD2011:

```python
from geo_coordinate import DatumTransformation, GeoCoordinate, GeodeticCrs

transformation = DatumTransformation(GeodeticCrs.TOKYO, GeodeticCrs.JGD2011)
print([datum.label for datum in transformation.route])  # ['Tokyo Datum', 'JGD2000', 'JGD2011']
print(transformation.accuracy_meter)  # 10.0
print(transformation.missing_grids)  # ('tky2jgd.gsb', 'touhokutaiheiyouoki2011.gsb')
print(
    transformation.transform(GeoCoordinate.from_degrees(35.6812, 139.7671))
)  # 35.6844..., 139.7638...
```

Heights above the ellipsoid become heights above mean sea level by subtracting the geoid:

```python
from pathlib import Path

import numpy as np

from geo_coordinate import GeoCoordinate, Geoid, GeoidModel

geoid = Geoid(GeoidModel.GSIGEO2011, Path("jp_gsi_gsigeo2011.tif"))
heights = geoid.interpolate_heights(np.array([139.76, 2.35]), np.array([35.68, 48.85]))
print(heights)  # [36.68...  nan]: Paris lies outside the Japanese grid

station = GeoCoordinate.from_degrees(35.68, 139.76)
print(geoid.to_altitude(station, np.array([76.68])).meter)  # [40.0...]
```
