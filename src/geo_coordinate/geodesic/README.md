# geodesic

## Overview

Shortest paths on a reference ellipsoid. `GeoCoordinateBase.distance_to` uses a sphere,
which is off by up to about 0.5 percent; `Geodesic` solves on the ellipsoid of the datum
instead, accurate to a few nanometres, with the algorithms of Karney (2013) as implemented
by PROJ. Altitudes are ignored.

| Member | Description |
|--------|-------------|
| `inverse(start, end)` | `GeodesicInverse`: lengths and the bearings at both ends, broadcast like `distance_to` |
| `distance(start, end)` | Lengths only |
| `direct(start, bearing, distance)` | Places reached, of the type of `start`, with altitudes carried over |
| `segment_distances(path)`, `path_length(path)` | Along a `GeoCoordinates` path |

## Components

| Component | Description |
|-----------|-------------|
| [geodesic.py](./geodesic.py) | `Geodesic`, the inverse and direct problems and path lengths on an `Ellipsoid` |
| [inverse.py](./inverse.py) | `GeodesicInverse`, the distances and initial and final bearings of an inverse problem |

## Examples

```python
from geo_coordinate import GeoCoordinate, Geodesic, GeodeticCrs

geodesic = Geodesic(GeodeticCrs.JGD2011.ellipsoid)
tokyo = GeoCoordinate.from_degrees(35.6812, 139.7671)
osaka = GeoCoordinate.from_degrees(34.7025, 135.4959)

solution = geodesic.inverse(tokyo, osaka)
print(solution.distance.km)  # [403.82...]
print(solution.initial_bearing.degree)  # [255.64...]
```
