# shape

## Overview

Lines and areas whose vertices are `GeoCoordinates`, such as GPS tracks and administrative areas, with vectorized point-in-polygon tests and GeoJSON (RFC 7946) reading and writing.

## Components

| Component | Description |
|-----------|-------------|
| [line_string.py](./line_string.py) | `GeoLineString`, an open line with its length, bounding box and reversal |
| [linear_ring.py](./linear_ring.py) | `GeoLinearRing`, a closed ring with orientation, perimeter and point-in-ring tests |
| [polygon.py](./polygon.py) | `GeoPolygon`, an outline with holes and point-in-polygon tests |
| [multi_polygon.py](./multi_polygon.py) | `GeoMultiPolygon`, separate polygons treated as one area |
| [bounding_box.py](./bounding_box.py) | `GeoBoundingBox`, the extreme latitudes and longitudes of places or boxes |
| [geojson.py](./geojson.py) | `GeoJsonGeometry`, reading and writing GeoJSON geometry objects |
| [geojson_type.py](./geojson_type.py) | `GeoJsonType`, the geometry types read and written |
| [geo_shape.py](./geo_shape.py) | `GeoShape`, the union of the shapes a geometry is read into |
| [json_value.py](./json_value.py) | `JsonValue`, the type of a parsed JSON value |

## Examples

```python
import json

import numpy as np

from geo_coordinate import (
    GeoCoordinates,
    Geodesic,
    GeodeticCrs,
    GeoJsonGeometry,
    GeoMultiPolygon,
    GeoPolygon,
)

with open("N03-20250101_13.geojson", encoding="utf-8") as stream:
    features = json.load(stream)["features"]
polygons = [GeoJsonGeometry.decode(feature["geometry"]) for feature in features]
tokyo = GeoMultiPolygon(
    polygons=tuple(polygon for polygon in polygons if isinstance(polygon, GeoPolygon))
)

print(Geodesic(GeodeticCrs.JGD2011.ellipsoid).area(tokyo).square_kilometer)  # [2198.97...]
places = GeoCoordinates.from_degrees(
    latitude=np.array([35.6812, 35.4437]), longitude=np.array([139.7671, 139.6380])
)
print(tokyo.contains(places))  # [ True False]
print(json.dumps(GeoJsonGeometry.encode(tokyo.oriented()))[:40])
```
