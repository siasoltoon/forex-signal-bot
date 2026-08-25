from __future__ import annotations

from typing import Any

from .models import TradingSignal


def create_signal_from_analysis(
    analysis_result: Any,
    *,
    symbol: str,
    timeframe: str,
) -> TradingSignal:
    """Convert analysis output into a managed trading signal.

    Keeps the analysis layer independent from signal lifecycle management.
    """
    return TradingSignal(
        symbol=symbol,
        timeframe=timeframe,
        direction=getattr(analysis_result, "signal", "WAIT"),
        entry=getattr(analysis_result, "entry_price", None),
        stop_loss=getattr(analysis_result, "stop_loss", None),
        take_profit=getattr(analysis_result, "take_profit", None),
        confidence=getattr(analysis_result, "confidence", 0),
    )
