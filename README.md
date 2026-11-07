# GeoCoordinate

## Overview

GeoCoordinate (`geo_coordinate`) handles geographic coordinates built on the unit-aware `Angle` and `Length` of [Units](https://github.com/ry-yoshida-dev/Units).
`GeoCoordinate` holds one location and `GeoCoordinates` a vectorized batch or path, with optional signed `Altitude`.
The package measures great-circle and ellipsoidal distances, bearings and altitude profiles, reads and writes sexagesimal text and GeoJSON, and converts between the coordinate reference systems used in Japan and worldwide (JGD2011, the Japan Plane Rectangular zones, UTM, Web Mercator, geoid heights and ECEF / east-north-up frames).

## Installation

Python 3.12 or newer.

```bash
pip install .
```

## Usage

```python
import numpy as np
from units import LengthUnit

from geo_coordinate import Altitude, GeoCoordinate, GeoCoordinates

tokyo = GeoCoordinate.from_degrees(35.6812, 139.7671)
osaka = GeoCoordinate.from_degrees(34.7025, 135.4959)

tokyo.distance_to(osaka).km  # [403.05...]
tokyo.initial_bearing_to(osaka).degree  # [255.57...]

station = GeoCoordinate.from_sexagesimal("35°40'52.32\"N", "139°46'1.56\"E")
station.to_sexagesimal().latitude  # ('35°40\'52.32"N',)

track = GeoCoordinates.from_degrees(
    latitude=np.array([35.6812, 35.6586, 35.6295]),
    longitude=np.array([139.7671, 139.7454, 139.7387]),
    altitude=Altitude(value=np.array([3.0, 25.0, 12.0]), unit=LengthUnit.M),
)
track.path_length.km  # [6.47...]
track.total_ascent.meter  # [22.]
```
