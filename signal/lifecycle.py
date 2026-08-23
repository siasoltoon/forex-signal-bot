from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


class SignalStatus(str, Enum):
    ACTIVE = "active"
    UPDATED = "updated"
    INVALIDATED = "invalidated"
    TARGET_HIT = "target_hit"
    STOP_HIT = "stop_hit"
    CLOSED = "closed"


@dataclass(frozen=True)
class SignalSnapshot:
    signal_id: str
    symbol: str
    direction: str
    entry: float
    stop_loss: float | None = None
    take_profit: float | None = None
    status: SignalStatus = SignalStatus.ACTIVE
    confidence: float | None = None
    reason: str = ""
    version: int = 1
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, object] = field(default_factory=dict)


class SignalLifecycle:
    """Immutable state transition service for long-lived trading signals."""

    _terminal = {
        SignalStatus.INVALIDATED,
        SignalStatus.TARGET_HIT,
        SignalStatus.STOP_HIT,
        SignalStatus.CLOSED,
    }

    def update(
        self,
        signal: SignalSnapshot,
        *,
        confidence: float | None = None,
        reason: str = "",
        metadata: Mapping[str, object] | None = None,
    ) -> SignalSnapshot:
        if signal.status in self._terminal:
            raise ValueError(f"Cannot update terminal signal: {signal.status.value}")
        return replace(
            signal,
            status=SignalStatus.UPDATED,
            confidence=confidence if confidence is not None else signal.confidence,
            reason=reason or signal.reason,
            version=signal.version + 1,
            updated_at=datetime.now(timezone.utc),
            metadata=metadata if metadata is not None else signal.metadata,
        )

    def transition(
        self,
        signal: SignalSnapshot,
        status: SignalStatus,
        *,
        reason: str = "",
    ) -> SignalSnapshot:
        if signal.status in self._terminal:
            raise ValueError(f"Cannot transition terminal signal: {signal.status.value}")
        return replace(
            signal,
            status=status,
            reason=reason or signal.reason,
            version=signal.version + 1,
            updated_at=datetime.now(timezone.utc),
        )
