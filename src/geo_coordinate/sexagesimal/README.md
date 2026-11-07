# sexagesimal

## Overview

Text notation of latitudes and longitudes in degrees, minutes and seconds, such as `35°40'52.27"N`, with the sign given by a hemisphere letter.

## Components

| Component | Description |
|-----------|-------------|
| [notation.py](./notation.py) | `SexagesimalNotation`, parsing and formatting of latitudes and longitudes |
| [text.py](./text.py) | `SexagesimalText`, the latitude and longitude texts of a set of coordinates |

## Examples

```python
import numpy as np
from units import Angle, AngleUnit

from geo_coordinate import SexagesimalNotation

latitude = SexagesimalNotation.parse_latitudes(["35°40'52.27\"N", "33°52′7.68″S"])
print(latitude.degree)  # [ 35.68118... -33.8688]

longitude = Angle(value=np.array([-0.5]), unit=AngleUnit.DEGREE)
print(SexagesimalNotation.format_longitudes(longitude, 0))  # ('0°30\'0"W',)
```
