# GeoCoordinate

## Overview

GeoCoordinate (`geo_coordinate`) is a Python package for geographic coordinates built on the unit-aware `Angle` and `Length` of [Units](https://github.com/ry-yoshida-dev/Units).
`GeoCoordinate` holds a single location and `GeoCoordinates` an ordered batch of latitudes, longitudes and optional signed `Altitude`, so a batch of locations is processed with vectorized operations and measured as a path.
Coordinates are read from and written to sexagesimal text such as `35°40'52.32"N`, and paths are measured by great-circle distances, bearings and altitude profiles.
The coordinate reference systems they are published in and projected to (`GeodeticCrs` such as JGD2011, the `JapanPlaneRectangularZone`s and `WebMercator`) are defined here as well, so that packages handling GIS data share one definition.

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

from geo_coordinate import Altitude, GeoCoordinate, GeoCoordinates

tokyo = GeoCoordinate.from_degrees(35.6812, 139.7671)
osaka = GeoCoordinate.from_degrees(
    34.7025, 135.4959, Altitude(value=np.array([5.0]), unit=LengthUnit.M)
)

print(tokyo.distance_to(osaka).km)  # [403.05...]

print(tokyo.initial_bearing_to(osaka).degree)  # [255.57...]

station = GeoCoordinate.from_sexagesimal("35°40'52.32\"N", "139°46'1.56\"E")
print(station.to_sexagesimal().latitude)  # ('35°40\'52.32"N',)

track = GeoCoordinates.from_degrees(
    latitude=np.array([35.6812, 35.6586, 35.6295]),
    longitude=np.array([139.7671, 139.7454, 139.7387]),
    altitude=Altitude(value=np.array([3.0, 25.0, 12.0]), unit=LengthUnit.M),
)
print(track.segment_distances.meter)  # [3187... 3291...]
print(track.path_length.km)  # [6.47...]
print(track.segment_grades)  # [ 0.0069... -0.0039...]
print(track.total_ascent.meter)  # [22.]

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
