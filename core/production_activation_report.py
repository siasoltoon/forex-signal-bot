"""Deterministic production activation reporting.

No external data is fabricated here. This module only evaluates explicit
runtime signals supplied by real integrations and fails closed otherwise.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ActivationReport:
    ready: bool
    missing: tuple[str, ...]


REQUIRED_REAL_INTEGRATIONS = (
    "market_data",
    "telegram",
    "database",
    "worker",
    "news_macro",
)


def build_activation_report(status: Mapping[str, bool]) -> ActivationReport:
    missing = tuple(name for name in REQUIRED_REAL_INTEGRATIONS if not status.get(name, False))
    return ActivationReport(ready=not missing, missing=missing)
