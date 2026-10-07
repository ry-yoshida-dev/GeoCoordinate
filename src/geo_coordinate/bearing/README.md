# bearing

## Overview

Horizontal directions measured clockwise from north. A `Bearing` holds a 1D `units.Angle`
within [0, 360) degrees together with the `NorthReference` it is measured from: true north,
as great circles and maps are, or magnetic north, as a compass and the magnetometer of a camera
are. The reference letters are those of Exif (`GPSImgDirectionRef`, `GPSTrackRef`,
`GPSDestBearingRef`): `T` and `M`.

`Bearing.wrapped` and `Bearing.from_degrees` turn any finite angle into [0, 360), so -90 becomes
270 and 360 becomes 0; the constructor rejects angles outside that range.

## Components

| Component | Description |
|-----------|-------------|
| [bearing.py](./bearing.py) | `Bearing`, directions clockwise from north with their reference |
| [north_reference.py](./north_reference.py) | `NorthReference` enum (`TRUE` / `MAGNETIC`) of the `T` / `M` letters |

## Examples

```python
from geo_coordinate import Bearing, NorthReference

facing = Bearing.from_degrees(-90.0, NorthReference.MAGNETIC)
print(facing.degree, facing.reference)  # [270.] NorthReference.MAGNETIC
```
