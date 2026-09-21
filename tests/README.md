# tests

## Overview

Pytest suite for `geo_coordinate`.

## Components

| Component | Description |
|-----------|-------------|
| [test_coordinate.py](./test_coordinate.py) | Validation, equality and great-circle distances of `GeoCoordinate` |
| [test_altitude.py](./test_altitude.py) | Signed values, magnitudes and validation of `Altitude` |
| [test_hemisphere.py](./test_hemisphere.py) | Parsing and signs of `LatitudeHemisphere` and `LongitudeHemisphere` |

## Example

```bash
uv run pytest
```
