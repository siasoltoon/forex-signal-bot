from __future__ import annotations

from dataclasses import dataclass

from analysis.regime import MarketRegime, RegimeResult
from analysis.scenario import Scenario


@dataclass(frozen=True, slots=True)
class IntelligenceSnapshot:
    data_valid: bool
    data_quality: float
    regime: RegimeResult
    decision_signal: str
    decision_confidence: float
    scenarios: tuple[Scenario, ...] = ()
    no_trade: bool = False
    no_trade_reason: str | None = None


class IntelligenceFlow:
    """Final safety boundary for composing existing intelligence outputs.

    This class consumes results from other engines. It never fabricates market
    data, predictions, or confidence values.
    """

    def compose(
        self,
        *,
        data_valid: bool,
        data_quality: float,
        regime: RegimeResult,
        decision_signal: str,
        decision_confidence: float,
        scenarios: tuple[Scenario, ...] = (),
        minimum_data_quality: float = 0.70,
        minimum_confidence: float = 0.40,
    ) -> IntelligenceSnapshot:
        quality = max(0.0, min(1.0, data_quality))
        confidence = max(0.0, min(1.0, decision_confidence))
        reasons: list[str] = []

        if not data_valid:
            reasons.append("invalid_data")
        if quality < minimum_data_quality:
            reasons.append("low_data_quality")
        if regime.regime is MarketRegime.UNKNOWN:
            reasons.append("unknown_market_regime")
        if confidence < minimum_confidence:
            reasons.append("low_confidence")

        signal = decision_signal.upper()
        if signal not in {"BUY", "SELL", "WAIT", "NO_TRADE"}:
            reasons.append("invalid_decision")
        if signal == "NO_TRADE":
            reasons.append("decision_engine_no_trade")

        no_trade = bool(reasons)
        return IntelligenceSnapshot(
            data_valid=data_valid,
            data_quality=quality,
            regime=regime,
            decision_signal="NO_TRADE" if no_trade else signal,
            decision_confidence=0.0 if no_trade and not data_valid else confidence,
            scenarios=scenarios,
            no_trade=no_trade,
            no_trade_reason=", ".join(reasons) if reasons else None,
        )
