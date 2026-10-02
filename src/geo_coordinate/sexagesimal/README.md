# sexagesimal

## Overview

Text notation of latitudes and longitudes in degrees, minutes and seconds,
with the sign given by a hemisphere letter.

`SexagesimalNotation` accepts:

- a hemisphere letter leading or trailing the components, in either case
  (`35°40'52.27"N`, `N35°40'52.27"`, `35°40'52.27"n`);
- ASCII `'` and `"` or the prime marks `′` and `″`, with optional spaces;
- omitted trailing components, where only the last component may be
  fractional (`35.68°N`, `35°40.87'N`).

It rejects texts without exactly one letter, letters of the other axis,
minutes or seconds of 60 or greater, non-ASCII digits, and signed magnitudes
such as `-35°N`.
Ranges are checked when the parsed angles build a coordinate.

Formatting rounds the seconds to the requested decimals before carrying, so
`59.996"` becomes the next minute, and drops the sign of values that round to
zero.

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
