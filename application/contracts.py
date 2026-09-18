from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RequestKind(StrEnum):
    ANALYSIS = "ANALYSIS"
    SCAN = "SCAN"
    BACKTEST = "BACKTEST"
    STATUS = "STATUS"


@dataclass(frozen=True, slots=True)
class ApplicationRequest:
    request_id: str
    user_id: str
    kind: RequestKind
    payload: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ApplicationResponse:
    request_id: str
    status: str
    message_key: str
    payload: tuple[tuple[str, str], ...] = ()
