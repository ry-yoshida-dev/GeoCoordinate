type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None
"""A value of a JSON document, as `json.loads` returns it."""
