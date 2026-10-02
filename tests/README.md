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
| [test_sexagesimal.py](./test_sexagesimal.py) | Parsing, formatting and validation of `SexagesimalNotation` |

## Example

```bash
uv run pytest
```
