# regional_mesh

## Overview

The regional meshes (地域メッシュ) of JIS X 0410, the grid of latitudes and longitudes the
statistics of Japan are tabulated on, such as the census per 1 km mesh. A mesh is named by its
code alone, so its extent is computed from the code instead of read from boundary data.

| Level | Digits | Extent (latitude × longitude) |
| --- | --- | --- |
| `FIRST` 第1次地域区画 | 4 | 40' × 1° |
| `SECOND` 第2次地域区画 | 6 | 5' × 7'30" |
| `THIRD` 基準地域メッシュ | 8 | 30" × 45" |
| `HALF` 2分の1地域メッシュ | 9 | 15" × 22.5" |
| `QUARTER` 4分の1地域メッシュ | 10 | 7.5" × 11.25" |
| `EIGHTH` 8分の1地域メッシュ | 11 | 3.75" × 5.625" |

Edges are kept as exact `Fraction`s of degrees, so `float(bounds.south)` is the floating-point
number nearest to the true edge, and meshes sharing an edge share the same number. The grid
itself is not tied to a datum; the edges are degrees on whichever datum the data is published in.

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
