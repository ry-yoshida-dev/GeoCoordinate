# reference_system

## Overview

Coordinate reference systems (CRSs) by EPSG code. Every member is its EPSG code, prints as
`EPSG:<code>`, and satisfies `CoordinateReferenceSystem`: `epsg`, `crs` (a `pyproj.CRS`) and
`geodetic_crs` (the datum it is defined on).

Latitudes and longitudes mean nothing exact without the datum they are measured on: the same
point differs by about 400 m between Tokyo Datum and JGD2011. `GeodeticCrs` names the
geographic CRSs Japanese data is published in. Lengths and areas need a plane instead of
degrees, which `JapanPlaneRectangularZone` provides for surveying and `WebMercator` for web maps.

| CRS | Kind | Defined on |
| --- | --- | --- |
| `GeodeticCrs` | geographic, degrees | its own datum |
| `JapanPlaneRectangularZone` | projected, metres, conformal within ~1/10000 | JGD2011 |
| `WebMercator` | projected, metres, for display only | WGS 84 |

## Components

| Component | Description |
|-----------|-------------|
| [coordinate_reference_system.py](./coordinate_reference_system.py) | `CoordinateReferenceSystem`: the protocol every CRS here satisfies |
| [geodetic_crs.py](./geodetic_crs.py) | `GeodeticCrs`: Tokyo Datum, JGD2000, JGD2011 and WGS 84 |
| [japan_plane_rectangular_zone.py](./japan_plane_rectangular_zone.py) | `JapanPlaneRectangularZone`: the nineteen zones of the Japan Plane Rectangular Coordinate System, their origins and the zone nearest to a location |
| [web_mercator.py](./web_mercator.py) | `WebMercator`: EPSG:3857 (`PSEUDO_MERCATOR`) and the extent of its world square |

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
