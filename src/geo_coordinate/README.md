# geo_coordinate

## Overview

Array-based geographic coordinates on top of `units.Angle` and `units.Length`.

## Components

| Component | Description |
|-----------|-------------|
| [coordinate.py](./coordinate.py) | `GeoCoordinate`, latitudes, longitudes and optional altitudes, with great-circle distances |
| [altitude.py](./altitude.py) | `Altitude`, signed heights relative to mean sea level |
| [hemisphere/](./hemisphere/) | `LatitudeHemisphere` and `LongitudeHemisphere` enums of the `N` / `S` and `E` / `W` abbreviations |

## Altitude

`units.Length` rejects negative values, since it represents magnitudes.
`Altitude` is signed instead, positive above sea level and negative below it,
and converts to and from a `Length` magnitude with `magnitude` and
`from_magnitude`.

## Distance

`GeoCoordinate.distance_to` returns the great-circle distance along the
surface as a `Length` in meters, by the haversine formula on a sphere of
`GeoCoordinate.EARTH_MEAN_RADIUS`. The error against the WGS84 ellipsoid stays
within about 0.5 percent, and altitudes are ignored. Either side may hold a
single coordinate, which is broadcast against the other.

## Hemisphere

Sources such as Exif and NMEA store latitude and longitude as unsigned values
with a separate `N` / `S` or `E` / `W` letter. `LatitudeHemisphere` and
`LongitudeHemisphere` parse that letter, and `is_negative` feeds
`units.DegreesMinutesSeconds`:

```python
import numpy as np
from units import Angle, DegreesMinutesSeconds

from geo_coordinate import LatitudeHemisphere

latitude = Angle.from_degrees_minutes_seconds(
    DegreesMinutesSeconds.normalized(
        degrees=np.array([33.0]),
        minutes=np.array([52.0]),
        seconds=np.array([7.68]),
        is_negative=np.array([LatitudeHemisphere("S").is_negative]),
    )
)
print(latitude.degree)  # [-33.8688]
```
