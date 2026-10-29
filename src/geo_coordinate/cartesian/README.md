# cartesian

## Overview

Cartesian frames in meters. `GeocentricConversion` turns latitude, longitude and height
above the ellipsoid into Earth-centred, Earth-fixed (ECEF) coordinates and back, and
`LocalTangentPlane` expresses places as east, north and up from an origin, as drones,
robots and AR scenes expect. Both conversions are exact on the `Ellipsoid` given.

Heights here are above the ellipsoid, as GNSS gives them, not above mean sea level as an
`Altitude` is, so they are passed as arrays of meters; `Geoid.to_ellipsoidal_height` and
`Geoid.to_altitude` convert between the two. `GeodeticPosition` pairs coordinates with such
heights.

## Components

| Component | Description |
|-----------|-------------|
| [earth_centered.py](./earth_centered.py) | `EarthCenteredCoordinates`, ECEF X, Y and Z and straight-line distances between them |
| [geocentric_conversion.py](./geocentric_conversion.py) | `GeocentricConversion`, geodetic positions to ECEF and back |
| [geodetic_position.py](./geodetic_position.py) | `GeodeticPosition`, coordinates with heights above the ellipsoid |
| [east_north_up.py](./east_north_up.py) | `EastNorthUp`, local coordinates with horizontal distance, slant range, azimuth and elevation angle |
| [local_tangent_plane.py](./local_tangent_plane.py) | `LocalTangentPlane`, geodetic positions to east-north-up from an origin and back |

## Examples

```python
import numpy as np

from geo_coordinate import GeoCoordinate, LocalTangentPlane

station = GeoCoordinate.from_degrees(35.6812, 139.7671)
plane = LocalTangentPlane(station, origin_ellipsoidal_height=40.0)

drone = plane.to_east_north_up(GeoCoordinate.from_degrees(35.6830, 139.7690), np.array([160.0]))
print(drone.east, drone.north, drone.up)  # [171.99...] [199.72...] [119.99...]
print(drone.azimuth.degree, drone.elevation_angle.degree)  # [40.73...] [24.47...]
```
