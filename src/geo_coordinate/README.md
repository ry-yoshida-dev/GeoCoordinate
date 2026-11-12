# geo_coordinate

## Overview

Array-based geographic coordinates on top of `units.Angle` and `units.Length`. Every public name is re-exported from the package root.

## Components

| Component | Description |
|-----------|-------------|
| [base.py](./base.py) | `GeoCoordinateBase`, shared validation into read-only copies, broadcasting of lengths, haversine `distance_to`, bearings, destinations, `relocated` and sexagesimal output |
| [coordinate.py](./coordinate.py) | `GeoCoordinate`, a single latitude, longitude and optional altitude |
| [coordinates.py](./coordinates.py) | `GeoCoordinates`, an ordered batch with indexing, concatenation, path distances, bearings and altitude profiles |
| [altitude.py](./altitude.py) | `Altitude`, read-only signed heights relative to mean sea level, broadcast to a length |
| [cartesian/](./cartesian/README.md) | `GeocentricConversion` and `LocalTangentPlane`, Earth-centred (ECEF) and east-north-up coordinates in meters |
| [geodesic/](./geodesic/README.md) | `Geodesic`, distances, bearings, destinations and path lengths on a reference ellipsoid |
| [bearing/](./bearing/README.md) | `Bearing` and `NorthReference`, directions clockwise from true or magnetic north |
| [hemisphere/](./hemisphere/README.md) | `LatitudeHemisphere` and `LongitudeHemisphere` enums of the `N` / `S` and `E` / `W` abbreviations |
| [reference_system/](./reference_system/README.md) | `GeodeticCrs`, `Ellipsoid`, `JapanPlaneRectangularZone`, `UtmZone` and `WebMercator`, the datums and planar projections coordinates are measured in, `DatumTransformation` and `PlaneProjection` between them, and `Geoid`, the heights of geoid models above the ellipsoid |
| [regional_mesh/](./regional_mesh/README.md) | `RegionalMeshLevel`, `RegionalMeshCode` and `RegionalMeshBounds`, the regional meshes of JIS X 0410 and their extents computed from their codes |
| [shape/](./shape/README.md) | `GeoLineString`, `GeoLinearRing`, `GeoPolygon`, `GeoMultiPolygon` and `GeoBoundingBox`, lines and areas with point-in-polygon tests, and `GeoJsonGeometry`, their GeoJSON geometries |
| [sexagesimal/](./sexagesimal/README.md) | `SexagesimalNotation` parsing and formatting of texts such as `35°40'52.27"N` |

## Examples

```python
import numpy as np

from geo_coordinate import GeoCoordinate, GeoCoordinates

track = GeoCoordinates.from_degrees(
    latitude=np.array([35.6812, 35.6586, 35.6295]),
    longitude=np.array([139.7671, 139.7454, 139.7387]),
)
station = GeoCoordinate.from_degrees(35.6812, 139.7671)

station.distance_to(track).meter  # [0. 3187... 6295...]
track[track.latitude.degree < 35.66]  # GeoCoordinates of the last two
```
