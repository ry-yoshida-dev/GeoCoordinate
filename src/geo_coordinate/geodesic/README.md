# geodesic

## Overview

Distances, bearings, destinations, path lengths, areas and perimeters on a reference ellipsoid, accurate to a few nanometres instead of the about 0.5 percent of the spherical `distance_to`.

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
