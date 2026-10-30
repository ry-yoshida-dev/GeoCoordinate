# tests

## Overview

Pytest suite for `geo_coordinate`.

## Components

| Component | Description |
|-----------|-------------|
| [test_coordinate.py](./test_coordinate.py) | Validation, equality, sexagesimal construction, great-circle distances, bearings and destinations of `GeoCoordinate` |
| [test_coordinates.py](./test_coordinates.py) | Indexing, iteration, concatenation, pairwise and path distances, bearings, destinations and altitude profiles of `GeoCoordinates` |
| [test_altitude.py](./test_altitude.py) | Signed values, magnitudes and validation of `Altitude` |
| [test_hemisphere.py](./test_hemisphere.py) | Parsing and signs of `LatitudeHemisphere` and `LongitudeHemisphere` |
| [test_reference_system.py](./test_reference_system.py) | EPSG codes, datums, ellipsoids and identification of `GeodeticCrs`, `JapanPlaneRectangularZone`, `UtmZone` and `WebMercator`, the numbers, origins, nearest zone and coverage of `JapanPlaneRectangularZone`, and the zone a location lies in of `UtmZone` |
| [test_geoid.py](./test_geoid.py) | Grids of `GeoidModel`, and interpolation, conversion between altitudes and ellipsoidal heights, places outside the grid and validation of `Geoid` |
| [test_datum_transformation.py](./test_datum_transformation.py) | Routes, accuracies, missing grids, round trips and preserved altitudes of `DatumTransformation` |
| [test_plane_projection.py](./test_plane_projection.py) | Projection, round trips, datum shifts, scale factors and meridian convergence of `PlaneProjection`, and `PlaneCoordinates` |
| [test_geodesic.py](./test_geodesic.py) | Ellipsoidal distances, bearings, direct solutions and path lengths of `Geodesic` |
| [test_cartesian.py](./test_cartesian.py) | ECEF conversion of `GeocentricConversion` and east-north-up frames of `LocalTangentPlane` |
| [test_regional_mesh.py](./test_regional_mesh.py) | Levels, exact extents, quarter digits, parents and children, the mesh a place lies in and validation of `RegionalMeshCode` |
| [test_sexagesimal.py](./test_sexagesimal.py) | Parsing, formatting and validation of `SexagesimalNotation` |

## Example

```bash
uv run pytest
```
