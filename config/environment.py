
from __future__ import annotations

import os
from typing import TypeVar


T = TypeVar("T")


def get_env(
    key: str,
    default: str | None = None,
) -> str | None:
    """
    Read an environment variable.

    Returns:
        The stripped environment value, or the supplied default.
    """

    if not isinstance(key, str):
        raise TypeError("Environment key must be a string.")

    key = key.strip()

    if not key:
        raise ValueError("Environment key cannot be empty.")

    value = os.getenv(key)

    if value is None:
        return default

    value = value.strip()

    if not value:
        return default

    return value


def get_required_env(key: str) -> str:
    """
    Read a required environment variable.

    Raises:
        RuntimeError: If the variable is missing or empty.
    """

    value = get_env(key)

    if value is None:
        raise RuntimeError(
            f"Required environment variable '{key}' "
            "is not configured."
        )

    return value


def get_bool_env(
    key: str,
    default: bool = False,
) -> bool:
    """
    Read a boolean environment variable.

    Accepted true values:
        1, true, yes, y, on, enabled

    Accepted false values:
        0, false, no, n, off, disabled
    """

    value = get_env(key)

    if value is None:
        return default

    normalized = value.lower()

    if normalized in {
        "1",
        "true",
        "yes",
        "y",
        "on",
        "enabled",
    }:
        return True

    if normalized in {
        "0",
        "false",
        "no",
        "n",
        "off",
        "disabled",
    }:
        return False

    raise ValueError(
        f"Invalid boolean value for '{key}': {value}"
    )


def get_int_env(
    key: str,
    default: int,
) -> int:
    """
    Read an integer environment variable.
    """

    value = get_env(key)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"Invalid integer value for '{key}': {value}"
        ) from error


def get_float_env(
    key: str,
    default: float,
) -> float:
    """
    Read a floating-point environment variable.
    """

    value = get_env(key)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError as error:
        raise ValueError(
            f"Invalid float value for '{key}': {value}"
        ) from error


def get_list_env(
    key: str,
    default: list[str] | None = None,
    separator: str = ",",
) -> list[str]:
    """
    Read a comma-separated environment variable.

    Example:
        SYMBOLS=EURUSD,GBPUSD,USDJPY

    Returns:
        A normalized list of strings.
    """

    fallback = list(default or [])

    value = get_env(key)

    if value is None:
        return fallback

    if not separator:
        raise ValueError(
            "Environment list separator cannot be empty."
        )

    items = [
        item.strip()
        for item in value.split(separator)
    ]

    return [
        item
        for item in items
        if item
    ]

