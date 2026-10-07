from __future__ import annotations

from enum import Enum


class NorthReference(Enum):
    """
    North a bearing is measured from, abbreviated as in Exif `GPSImgDirectionRef`.

    Attributes
    ----------
    TRUE
        Geographic north, towards the North Pole along the meridian.
    MAGNETIC
        Magnetic north, where a compass points, apart from true north by the local
        magnetic declination.
    """

    TRUE = "T"
    MAGNETIC = "M"
