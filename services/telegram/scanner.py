from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from analysis.full_engine import FullAnalysisEngine
from core.errors import ApplicationError
from data.factory import ProviderFactory
from data.market_data import MarketDataEngine
from data.provider_manager import ProviderManager
from .market_session import evaluate_market_status
from .i18n import t

logger = logging.getLogger(__name__)

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
    market_status: str = "UNKNOWN"
    last_candle_time: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ScanReadiness:
    configured_providers: tuple[str, ...]
    unavailable_providers: tuple[str, ...]


def _provider_readiness() -> ScanReadiness:
    configured = []
    unavailable = []
    for provider_name in ProviderFactory.available():
        try:
            (configured if ProviderFactory.configured(provider_name) else unavailable).append(provider_name)
        except Exception:
            unavailable.append(provider_name)
    return ScanReadiness(tuple(configured), tuple(unavailable))


def _build_provider_manager() -> ProviderManager:
    readiness = _provider_readiness()
    if not readiness.configured_providers:
        raise ApplicationError("No market-data provider is configured.", {})
    return ProviderManager(providers=readiness.configured_providers)


async def scan_market(symbols=DEFAULT_SCAN_SYMBOLS, timeframe=DEFAULT_TIMEFRAME, limit=DEFAULT_LIMIT):
    provider_manager = _build_provider_manager()
    engine = MarketDataEngine(provider_manager=provider_manager)
    analyzer = FullAnalysisEngine()

    async def scan_one(symbol):
        try:
            candles = await engine.get_candles_list(symbol, timeframe, limit)
            if not candles:
                raise RuntimeError("empty market data")

            status = evaluate_market_status(candles, timeframe)
            if status.status != "OPEN":
                return ScanResult(
                    symbol, "NO_TRADE", 0.0, 0.0, None, "UNKNOWN", "unknown", None,
                    status.status, getattr(status, "last_candle_time", None)
                )

            report = await asyncio.to_thread(analyzer.analyze, candles)
            return ScanResult(
                symbol,
                str(report.signal).upper(),
                float(report.confidence),
                float(report.score),
                report.trade_quality,
                report.trade_grade,
                report.trend,
                report.risk_reward,
                status.status,
                getattr(status, "last_candle_time", None),
            )
        except Exception as exc:
            logger.exception("Market scan failed for %s/%s", symbol, timeframe)
            return ScanResult(symbol, "NO_TRADE", 0.0, 0.0, None, "UNKNOWN", "unknown", None, error=type(exc).__name__)

    return sorted(await asyncio.gather(*(scan_one(s) for s in symbols)), key=lambda x: (x.error is None, x.confidence, x.score), reverse=True)


def _status_text(status: str) -> str:
    mapping = {
        "CLOSED": "بسته",
        "STALE_DATA": "داده قدیمی",
        "NO_DATA": "بدون داده",
        "HOLIDAY": "تعطیل",
        "UNKNOWN": "نامشخص",
    }
    return mapping.get(status, status)


def format_scan(results, timeframe, language="fa"):
    lines = ["🔎 <b>اسکن بازار — {}</b>".format(timeframe), ""]

    for item in results:
        if item.error:
            lines.append(f"• <b>{item.symbol}</b> → ⛔ خطا در دریافت داده")
            continue

        if item.market_status != "OPEN":
            extra = f" | آخرین کندل: {item.last_candle_time}" if item.last_candle_time else ""
            lines.append(f"• <b>{item.symbol}</b> → ⚠️ بازار {_status_text(item.market_status)}{extra}")
            continue

        confidence = max(0, min(1, item.confidence)) * 100
        quality = "—" if item.trade_quality is None else f"{item.trade_quality:.0f}"
        rr = "—" if item.risk_reward is None else f"{item.risk_reward:.2f}"
        lines.append(f"• <b>{item.symbol}</b> → {item.signal} | اطمینان {confidence:.0f}% | کیفیت {quality} | RR {rr} | روند {item.trend}")

    lines.extend(["", t(language, "scan_note")])
    return "\n".join(lines)


__all__ = ["ScanResult", "ScanReadiness", "scan_market", "format_scan", "DEFAULT_SCAN_SYMBOLS"]
