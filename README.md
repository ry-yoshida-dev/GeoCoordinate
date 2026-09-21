# GeoCoordinate

## Overview

GeoCoordinate (`geo_coordinate`) is a Python package for geographic coordinates built on the unit-aware `Angle` and `Length` of [Units](https://github.com/ry-yoshida-dev/Units).
`GeoCoordinate` holds latitudes, longitudes and optional signed `Altitude` as 1D arrays, so a batch of locations is processed with vectorized operations.

For package-level details, see [src/geo_coordinate/README.md](src/geo_coordinate/README.md).

## Installation

From the package root (the directory containing `pyproject.toml`):

```bash
pip install .
```

For development:

```bash
uv sync
```

If you only need dependencies:

```bash
pip install -r requirements.txt
```

## Example

```python
import numpy as np
from units import Length, LengthUnit

from geo_coordinate import Altitude, GeoCoordinate

tokyo = GeoCoordinate.from_degrees(np.array([35.6812]), np.array([139.7671]))
osaka = GeoCoordinate.from_degrees(
    latitude=np.array([34.7025]),
    longitude=np.array([135.4959]),
    altitude=Altitude(value=np.array([5.0]), unit=LengthUnit.M),
)

print(tokyo.distance_to(osaka).km)  # [403.05...]

below_sea_level = Altitude.from_magnitude(
    Length(value=np.array([40.5]), unit=LengthUnit.M),
    is_below_sea_level=np.array([True]),
)
print(below_sea_level.meter)  # [-40.5]
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy
uv run basedpyright
```
