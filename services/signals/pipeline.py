from __future__ import annotations

from .factory import create_signal_from_analysis
from .manager import SignalManager
from .models import TradingSignal


class SignalPipeline:
    """Bridge analysis results into managed signal lifecycle."""

    def __init__(self, manager: SignalManager | None = None) -> None:
        self.manager = manager or SignalManager()

    def create_and_register(
        self,
        analysis_result,
        *,
        symbol: str,
        timeframe: str,
    ) -> TradingSignal:
        signal = create_signal_from_analysis(
            analysis_result,
            symbol=symbol,
            timeframe=timeframe,
        )
        return self.manager.register(signal)
