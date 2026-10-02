# geo_coordinate

## Overview

Array-based geographic coordinates on top of `units.Angle` and `units.Length`.

## Components

| Component | Description |
|-----------|-------------|
| [base.py](./base.py) | `GeoCoordinateBase`, shared validation, haversine `distance_to`, bearings, destinations and sexagesimal output |
| [coordinate.py](./coordinate.py) | `GeoCoordinate`, a single latitude, longitude and optional altitude |
| [coordinates.py](./coordinates.py) | `GeoCoordinates`, an ordered batch with indexing, concatenation, path distances, bearings and altitude profiles |
| [altitude.py](./altitude.py) | `Altitude`, signed heights relative to mean sea level |
| [hemisphere/](./hemisphere/) | `LatitudeHemisphere` and `LongitudeHemisphere` enums of the `N` / `S` and `E` / `W` abbreviations |
| [reference_system/](./reference_system/README.md) | `GeodeticCrs`, `JapanPlaneRectangularZone` and `WebMercator`, the datums and planar projections coordinates are measured in |
| [sexagesimal/](./sexagesimal/) | `SexagesimalNotation` parsing and formatting of texts such as `35°40'52.27"N` |

## Altitude

`units.Length` rejects negative values, since it represents magnitudes.
`Altitude` is signed instead, positive above sea level and negative below it,
and converts to and from a `Length` magnitude with `magnitude` and
`from_magnitude`.

## Single Coordinate and Batch

`GeoCoordinate` holds exactly one location and `GeoCoordinates` holds an
ordered batch of them, mirroring `Point2D` and `Points2D` of Geometry. Both
store 1D arrays, so a `GeoCoordinate` broadcasts against a batch.

Indexing a batch with an `int` returns a `GeoCoordinate`; a slice, boolean mask
or integer array returns a `GeoCoordinates`. Iteration yields `GeoCoordinate`s,
and `GeoCoordinates.concatenate` joins singles and batches in order.

## Distance

All distances are great-circle distances along the surface, returned as a
`Length` in meters, by the haversine formula on a sphere of
`EARTH_MEAN_RADIUS`. The error against the WGS84 ellipsoid stays within about
0.5 percent, and altitudes are ignored.

| Member | Shape | Description |
|--------|-------|-------------|
| `distance_to(other)` | (N,) | Element-wise; either side may hold a single coordinate |
| `GeoCoordinates.pairwise_distance_to(other)` | (N, M) | Every coordinate here to every one in `other` |
| `GeoCoordinates.distance_matrix` | (N, N) | Every pair within the batch |
| `GeoCoordinates.segment_distances` | (N - 1,) | Between consecutive coordinates |
| `GeoCoordinates.cumulative_distances` | (N,) | Along the path up to each coordinate, starting at zero |
| `GeoCoordinates.path_length` | (1,) | Total along the path |

```python
import numpy as np

from geo_coordinate import GeoCoordinate, GeoCoordinates

track = GeoCoordinates.from_degrees(
    latitude=np.array([35.6812, 35.6586, 35.6295]),
    longitude=np.array([139.7671, 139.7454, 139.7387]),
)
station = GeoCoordinate.from_degrees(35.6812, 139.7671)

print(track.path_length.km)  # [6.47...]
print(station.distance_to(track).meter)  # [0. 3187... 6295...]
print(track[track.latitude.degree < 35.66])  # GeoCoordinates of the last two
```

## Bearing and Destination

`initial_bearing_to(other)` returns the heading at the start of the great
circle towards `other`, as an `Angle` in degrees within [0, 360) clockwise from
north, broadcast like `distance_to`. `GeoCoordinates.segment_bearings` gives
the heading of each segment of a path, of shape (N - 1,).

`destination(bearing, distance)` is the inverse: it travels the given distance
along the great circle starting at the given bearing, and returns coordinates
of the same type with longitudes wrapped to [-180, 180) and altitudes carried
over.

```python
import numpy as np
from units import Angle, AngleUnit, Length, LengthUnit

from geo_coordinate import GeoCoordinate

tokyo = GeoCoordinate.from_degrees(35.6812, 139.7671)
osaka = GeoCoordinate.from_degrees(34.7025, 135.4959)

print(tokyo.initial_bearing_to(osaka).degree)  # [255.57...]
east = tokyo.destination(
    Angle(value=np.array([90.0]), unit=AngleUnit.DEGREE),
    Length(value=np.array([1.0]), unit=LengthUnit.KM),
)
```

## Altitude Profile

When a `GeoCoordinates` path carries an altitude, its segments are also
measured vertically. These members raise `ValueError` without an altitude.

| Member | Shape | Description |
|--------|-------|-------------|
| `segment_altitude_changes` | (N - 1,) | Signed `Altitude` changes in meters, positive uphill |
| `segment_slant_distances` | (N - 1,) | Hypotenuse of the great-circle distance and altitude change |
| `segment_grades` | (N - 1,) | Altitude change over great-circle distance, NaN for zero distance |
| `total_ascent` | (1,) | Sum of altitude gains |
| `total_descent` | (1,) | Sum of altitude losses, as a positive `Length` |

## Sexagesimal Text

`GeoCoordinate.from_sexagesimal` and `GeoCoordinates.from_sexagesimal` parse
texts such as `35°40'52.27"N` and `139°46'1.56"E`, and `to_sexagesimal`
writes them back as a `SexagesimalText`. See
[sexagesimal/README.md](./sexagesimal/README.md) for the accepted notation.

```python
from geo_coordinate import GeoCoordinate

station = GeoCoordinate.from_sexagesimal("35°40'52.32\"N", "139°46'1.56\"E")
print(station.latitude.degree)  # [35.6812]
print(station.to_sexagesimal().longitude)  # ('139°46\'1.56"E',)
```

## Hemisphere

Sources such as Exif and NMEA store latitude and longitude as unsigned values
with a separate `N` / `S` or `E` / `W` letter. `LatitudeHemisphere` and
`LongitudeHemisphere` parse that letter, `from_is_negative` derives it from a
sign, and `is_negative` feeds `units.DegreesMinutesSeconds`:

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
