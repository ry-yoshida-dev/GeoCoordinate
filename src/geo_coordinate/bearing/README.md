# bearing

## Overview

Horizontal directions within [0, 360) degrees, measured clockwise from true or magnetic north, with the `T` / `M` reference letters of Exif.

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
