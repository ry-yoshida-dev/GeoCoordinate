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

| CRS | Kind | Defined on |
| --- | --- | --- |
| `GeodeticCrs` | geographic, degrees | its own datum |
| `JapanPlaneRectangularZone` | projected, metres, conformal within ~1/10000 | JGD2011 |
| `UtmZone` | projected, metres, conformal within ~1/1000 | WGS 84 |
| `WebMercator` | projected, metres, for display only | WGS 84 |

## Components

| Component | Description |
|-----------|-------------|
| [coordinate_reference_system.py](./coordinate_reference_system.py) | `CoordinateReferenceSystem`: the protocol every CRS here satisfies |
| [geodetic_crs.py](./geodetic_crs.py) | `GeodeticCrs`: Tokyo Datum, JGD2000, JGD2011 and WGS 84 |
| [japan_plane_rectangular_zone.py](./japan_plane_rectangular_zone.py) | `JapanPlaneRectangularZone`: the nineteen zones of the Japan Plane Rectangular Coordinate System, their origins, the zone nearest to a location and whether any zone covers it |
| [utm_zone.py](./utm_zone.py) | `UtmZone`: the zones of the Universal Transverse Mercator system and the zone a location lies in |
| [web_mercator.py](./web_mercator.py) | `WebMercator`: EPSG:3857 (`PSEUDO_MERCATOR`), the extent of its world square and the latitude where it ends |
| [web_mercator_projection.py](./web_mercator_projection.py) | `WebMercatorProjection`: arrays of WGS 84 longitudes and latitudes to Web Mercator metres and back within the world square, and the ground scale at a latitude on the sphere |

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
