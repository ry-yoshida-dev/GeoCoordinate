from __future__ import annotations

import re
from collections.abc import Sequence
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray
from units import Angle, AngleUnit, DegreesMinutesSeconds, NumericArray

from ..hemisphere import LatitudeHemisphere, LongitudeHemisphere


class SexagesimalNotation:
    """
    Text notation of latitudes and longitudes in degrees, minutes and seconds.

    Parses and formats strings such as `35°40'52.27"N`, where the magnitude is
    written in sexagesimal components and the sign by a hemisphere letter. The
    letter may lead or trail the components, and only the last component may
    be fractional, so `35.68°N`, `35°40.87'N` and `N35°40'52.27"` are accepted.
    Ranges of latitudes and longitudes are validated by the coordinates built
    from the parsed angles, not here.
    """

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\s*(?P<leading>[NSEW])?\s*"
        + r"(?P<degrees>\d+(?:\.\d+)?)\s*°\s*"
        + r"(?:(?P<minutes>\d+(?:\.\d+)?)\s*['\u2032]\s*)?"
        + r"(?:(?P<seconds>\d+(?:\.\d+)?)\s*[\"\u2033]\s*)?"
        + r"(?P<trailing>[NSEW])?\s*",
        re.IGNORECASE | re.ASCII,
    )
    SEXAGESIMAL_BASE: ClassVar[int] = 60
    SECONDS_PER_DEGREE: ClassVar[int] = 3600
    MAX_SECONDS_DECIMALS: ClassVar[int] = 6

    @classmethod
    def parse_latitudes(cls, texts: Sequence[str]) -> Angle:
        """
        Parse latitudes written with an `N` or `S` letter.

        Parameters
        ----------
        texts : Sequence[str]
            The latitudes, such as `35°40'52.27"N`.

        Returns
        -------
        Angle
            The signed latitudes in degrees, one per text.

        Raises
        ------
        ValueError
            If a text is not in sexagesimal notation, does not carry exactly
            one `N` or `S` letter, has a minute or second of 60 or greater,
            or has a fractional component other than the last.
        """
        return cls._parse(texts, LatitudeHemisphere)

    @classmethod
    def parse_longitudes(cls, texts: Sequence[str]) -> Angle:
        """
        Parse longitudes written with an `E` or `W` letter.

        Parameters
        ----------
        texts : Sequence[str]
            The longitudes, such as `139°46'1.56"E`.

        Returns
        -------
        Angle
            The signed longitudes in degrees, one per text.

        Raises
        ------
        ValueError
            If a text is not in sexagesimal notation, does not carry exactly
            one `E` or `W` letter, has a minute or second of 60 or greater,
            or has a fractional component other than the last.
        """
        return cls._parse(texts, LongitudeHemisphere)

    @classmethod
    def format_latitudes(cls, latitude: Angle, seconds_decimals: int = 2) -> tuple[str, ...]:
        """
        Format latitudes as degrees, minutes, seconds and an `N` or `S` letter.

        Parameters
        ----------
        latitude : Angle
            The signed latitudes.
        seconds_decimals : int
            The number of decimals of the seconds, within [0, 6].

        Returns
        -------
        tuple[str, ...]
            The latitudes, such as `35°40'52.27"N`.

        Raises
        ------
        ValueError
            If `seconds_decimals` is outside [0, 6].
        """
        return cls._format(latitude, seconds_decimals, LatitudeHemisphere)

    @classmethod
    def format_longitudes(cls, longitude: Angle, seconds_decimals: int = 2) -> tuple[str, ...]:
        """
        Format longitudes as degrees, minutes, seconds and an `E` or `W` letter.

        Parameters
        ----------
        longitude : Angle
            The signed longitudes.
        seconds_decimals : int
            The number of decimals of the seconds, within [0, 6].

        Returns
        -------
        tuple[str, ...]
            The longitudes, such as `139°46'1.56"E`.

        Raises
        ------
        ValueError
            If `seconds_decimals` is outside [0, 6].
        """
        return cls._format(longitude, seconds_decimals, LongitudeHemisphere)

    @classmethod
    def _parse(
        cls,
        texts: Sequence[str],
        hemisphere_type: type[LatitudeHemisphere] | type[LongitudeHemisphere],
    ) -> Angle:
        degrees: NumericArray = np.array(
            [cls._parse_degree(text, hemisphere_type) for text in texts], dtype=np.float64
        )
        return Angle(value=degrees, unit=AngleUnit.DEGREE)

    @classmethod
    def _parse_degree(
        cls,
        text: str,
        hemisphere_type: type[LatitudeHemisphere] | type[LongitudeHemisphere],
    ) -> float:
        matched: re.Match[str] | None = cls.PATTERN.fullmatch(text)
        if matched is None:
            raise ValueError(f"invalid sexagesimal notation: {text!r}")
        letters: list[str] = [
            letter
            for letter in (matched.group("leading"), matched.group("trailing"))
            if letter is not None
        ]
        if len(letters) != 1:
            raise ValueError(f"exactly one hemisphere letter is required, given: {text!r}")
        hemisphere: LatitudeHemisphere | LongitudeHemisphere = hemisphere_type(letters[0].upper())
        minutes_text: str | None = matched.group("minutes")
        seconds_text: str | None = matched.group("seconds")
        if seconds_text is not None and minutes_text is None:
            raise ValueError(f"seconds require minutes, given: {text!r}")
        degrees: float = float(matched.group("degrees"))
        minutes: float = 0.0 if minutes_text is None else float(minutes_text)
        seconds: float = 0.0 if seconds_text is None else float(seconds_text)
        is_degrees_fractional_before_minutes: bool = (
            minutes_text is not None and not degrees.is_integer()
        )
        is_minutes_fractional_before_seconds: bool = (
            seconds_text is not None and not minutes.is_integer()
        )
        if is_degrees_fractional_before_minutes or is_minutes_fractional_before_seconds:
            raise ValueError(f"only the last component may be fractional, given: {text!r}")
        if minutes >= cls.SEXAGESIMAL_BASE or seconds >= cls.SEXAGESIMAL_BASE:
            raise ValueError(f"minutes and seconds must be less than 60, given: {text!r}")
        magnitude: float = (
            degrees + minutes / cls.SEXAGESIMAL_BASE + seconds / cls.SECONDS_PER_DEGREE
        )
        return -magnitude if hemisphere.is_negative else magnitude

    @classmethod
    def _format(
        cls,
        angle: Angle,
        seconds_decimals: int,
        hemisphere_type: type[LatitudeHemisphere] | type[LongitudeHemisphere],
    ) -> tuple[str, ...]:
        if not 0 <= seconds_decimals <= cls.MAX_SECONDS_DECIMALS:
            raise ValueError(
                f"seconds_decimals must be within [0, {cls.MAX_SECONDS_DECIMALS}], "
                + f"given: {seconds_decimals}"
            )
        signed_seconds: NumericArray = angle.degree * cls.SECONDS_PER_DEGREE
        magnitude_seconds: NumericArray = np.round(np.abs(signed_seconds), seconds_decimals)
        is_negative: NDArray[np.bool_] = np.logical_and(signed_seconds < 0, magnitude_seconds > 0)
        sexagesimal: DegreesMinutesSeconds = DegreesMinutesSeconds.normalized(
            degrees=np.zeros_like(magnitude_seconds),
            minutes=np.zeros_like(magnitude_seconds),
            seconds=magnitude_seconds,
        )
        return tuple(
            f"{int(degrees)}°{int(minutes)}'{seconds:.{seconds_decimals}f}\""
            + hemisphere_type.from_is_negative(bool(is_element_negative)).value
            for degrees, minutes, seconds, is_element_negative in zip(
                sexagesimal.degrees.tolist(),
                sexagesimal.minutes.tolist(),
                sexagesimal.seconds.tolist(),
                is_negative.tolist(),
                strict=True,
            )
        )
