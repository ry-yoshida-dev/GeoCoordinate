from __future__ import annotations

from enum import Enum
from typing import Final

from .geodetic_crs import GeodeticCrs

GRID_HOST: Final[str] = "https://cdn.proj.org"


class GeoidModel(Enum):
    """
    Geoid models, each the name of the grid PROJ publishes it as.

    A geoid model gives the height of the geoid above the ellipsoid, which turns heights
    above the ellipsoid, as GNSS and 3D Tiles give them, into heights above mean sea level
    and back. The Japanese models cover Japan only; the global models cover the whole Earth
    more coarsely.

    Attributes
    ----------
    GSIGEO2011
        The Japanese geoid 2011 (ジオイド2011) of GSI, the reference for heights in Japan
        until March 2025, about 2 cm accurate.
    JPGEO2024
        The Japanese geoid 2024 (ジオイド2024) of GSI, the reference for heights in Japan
        from April 2025, about 3 cm accurate.
    EGM96
        The global Earth Gravitational Model 1996 on a 15' grid, about 1 m accurate.
    EGM2008
        The global Earth Gravitational Model 2008 on a 2.5' grid, about 10 cm accurate.
    """

    GSIGEO2011 = "jp_gsi_gsigeo2011.tif"
    JPGEO2024 = "jp_gsi_jpgeo2024.tif"
    EGM96 = "us_nga_egm96_15.tif"
    EGM2008 = "us_nga_egm08_25.tif"

    @property
    def grid_name(self) -> str:
        """
        Return the file name of the grid of this model.

        Returns
        -------
        str
            The name of the GeoTIFF on the PROJ content delivery network.
        """
        return self.value

    @property
    def grid_url(self) -> str:
        """
        Return where the grid of this model is downloaded from.

        Returns
        -------
        str
            The URL of the GeoTIFF on the PROJ content delivery network.
        """
        return f"{GRID_HOST}/{self.value}"

    @property
    def geodetic_crs(self) -> GeodeticCrs:
        """
        Return the geographic CRS the grid is laid out in.

        Returns
        -------
        GeodeticCrs
            JGD2011 for the Japanese models, WGS 84 for the global ones.
        """
        match self:
            case GeoidModel.GSIGEO2011 | GeoidModel.JPGEO2024:
                return GeodeticCrs.JGD2011
            case GeoidModel.EGM96 | GeoidModel.EGM2008:
                return GeodeticCrs.WGS84

    @property
    def is_global(self) -> bool:
        """
        Return whether the model covers the whole Earth.

        Returns
        -------
        bool
            True for EGM96 and EGM2008, False for the Japanese models.
        """
        return self.geodetic_crs is GeodeticCrs.WGS84

    @property
    def label(self) -> str:
        """
        Return the name of this model.

        Returns
        -------
        str
            A name for messages and listings.
        """
        match self:
            case GeoidModel.GSIGEO2011:
                return "GSIGEO2011"
            case GeoidModel.JPGEO2024:
                return "JPGEO2024"
            case GeoidModel.EGM96:
                return "EGM96"
            case GeoidModel.EGM2008:
                return "EGM2008"
