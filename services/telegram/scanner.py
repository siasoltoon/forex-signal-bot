from __future__ import annotations

import asyncio
from dataclasses import dataclass

from analysis.full_engine import FullAnalysisEngine
from data.market_data import MarketDataEngine
from .i18n import t

DEFAULT_SCAN_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")
DEFAULT_TIMEFRAME = "M15"
DEFAULT_LIMIT = 300


@dataclass(frozen=True)
class ScanResult:
    symbol: str
    signal: str
    confidence: float
    score: float
    trade_quality: float | None
    trade_grade: str
    trend: str
    risk_reward: float | None
    error: str | None = None


async def scan_market(symbols: tuple[str, ...] = DEFAULT_SCAN_SYMBOLS, timeframe: str = DEFAULT_TIMEFRAME, limit: int = DEFAULT_LIMIT) -> list[ScanResult]:
    """Run the production data-quality-gated analysis pipeline for multiple markets."""
    engine = MarketDataEngine()
    analyzer = FullAnalysisEngine()

    async def scan_one(symbol: str) -> ScanResult:
        try:
            candles = await engine.get_candles_list(symbol, timeframe, limit)
            if not candles:
                raise RuntimeError("empty market data")
            report = await asyncio.to_thread(analyzer.analyze, candles)
            return ScanResult(symbol=symbol, signal=str(report.signal).upper(), confidence=float(report.confidence), score=float(report.score), trade_quality=report.trade_quality, trade_grade=report.trade_grade, trend=report.trend, risk_reward=report.risk_reward)
        except Exception as exc:
            # Keep internal exception details out of Telegram. They remain available
            # to application logs through the data/analyzer layers.
            return ScanResult(symbol=symbol, signal="NO_TRADE", confidence=0.0, score=0.0, trade_quality=None, trade_grade="UNKNOWN", trend="unknown", risk_reward=None, error=type(exc).__name__)

    results = await asyncio.gather(*(scan_one(symbol) for symbol in symbols))
    return sorted(results, key=lambda item: (item.error is None, item.confidence, item.score), reverse=True)


def format_scan(results: list[ScanResult], timeframe: str, language: str = "fa") -> str:
    title = "🔎 <b>Market Scan — {}</b>".format(timeframe) if language == "en" else "🔎 <b>اسکن بازار — {}</b>".format(timeframe)
    lines = [title, ""]
    for item in results:
        if item.error:
            lines.append(f"• {item.symbol}: ⛔ {t(language, 'scan_unavailable')}")
            continue
        confidence = max(0.0, min(1.0, item.confidence)) * 100
        quality = "—" if item.trade_quality is None else f"{item.trade_quality:.0f}"
        rr = "—" if item.risk_reward is None else f"{item.risk_reward:.2f}"
        if language == "en":
            lines.append(f"• <b>{item.symbol}</b> → {item.signal} | confidence {confidence:.0f}% | quality {quality} | RR {rr} | trend {item.trend}")
        else:
            lines.append(f"• <b>{item.symbol}</b> → {item.signal} | اطمینان {confidence:.0f}% | کیفیت {quality} | RR {rr} | روند {item.trend}")
    lines.extend(["", t(language, "scan_note")])
    return "\n".join(lines)


__all__ = ["ScanResult", "scan_market", "format_scan", "DEFAULT_SCAN_SYMBOLS"]
