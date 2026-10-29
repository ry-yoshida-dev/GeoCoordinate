from .line_string import GeoLineString
from .multi_polygon import GeoMultiPolygon
from .polygon import GeoPolygon

type GeoShape = GeoLineString | GeoPolygon | GeoMultiPolygon
"""A line or an area that GeoJSON geometries are read into."""
