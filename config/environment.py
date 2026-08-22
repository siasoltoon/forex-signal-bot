"""Backward-compatible environment helpers.

The application configuration source of truth is ``config.settings``.
These names remain available for legacy callers while delegating all parsing
and normalization to the central configuration module.
"""

from __future__ import annotations

from .settings import (
    get_bool_env,
    get_env,
    get_float_env,
    get_int_env,
    get_list_env,
    get_required_env,
)

__all__ = [
    "get_env",
    "get_required_env",
    "get_bool_env",
    "get_int_env",
    "get_float_env",
    "get_list_env",
]
