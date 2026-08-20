from __future__ import annotations

import os


def get_env(
    key: str,
    default: str | None = None,
) -> str | None:
    """
    Read environment variable.
    """

    return os.getenv(
        key,
        default,
    )
