# regional_mesh

## Overview

The regional meshes (地域メッシュ) of JIS X 0410, from the first level (4 digits) to the eighth (11 digits), the grid the statistics of Japan are tabulated on. The extent of a mesh is computed from its code in exact degrees.

## Components

| Component | Description |
|-----------|-------------|
| [level.py](./level.py) | `RegionalMeshLevel`: the levels, their names, extents and how they divide one another |
| [code.py](./code.py) | `RegionalMeshCode`: a validated code, its level, extent, parent and children, and the code of the mesh a place lies in |
| [bounds.py](./bounds.py) | `RegionalMeshBounds`: the edges of a mesh in exact degrees, and whether a place lies in it |

## Examples

```python
from geo_coordinate import GeoCoordinate, RegionalMeshCode, RegionalMeshLevel

code = RegionalMeshCode("533935991")
print(code.level.label)  # 2分の1地域メッシュ
print(float(code.bounds.south), float(code.bounds.west))  # 35.65833333333333 139.7375
print(code.parent)  # 53393599

tokyo_station = GeoCoordinate.from_degrees(35.6812, 139.7671)
print(RegionalMeshCode.containing(tokyo_station, RegionalMeshLevel.THIRD))  # 53394611
```
