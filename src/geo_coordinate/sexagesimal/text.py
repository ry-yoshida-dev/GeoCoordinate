from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SexagesimalText:
    """
    Coordinates written in degrees, minutes, seconds and hemisphere letters.

    Parameters
    ----------
    latitude : tuple[str, ...]
        The latitudes, such as `35°40'52.27"N`.
    longitude : tuple[str, ...]
        The longitudes, such as `139°46'1.56"E`.
    """

    latitude: tuple[str, ...]
    longitude: tuple[str, ...]
