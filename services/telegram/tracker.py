from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from analysis.full_engine import FullAnalysisEngine
from data.market_data import MarketDataEngine


@dataclass
class TrackedSignal:
    user_id: int
    symbol: str
    timeframe: str
    signal: str
    entry: float | None
    stop_loss: float | None
    take_profit_1: float | None
    take_profit_2: float | None
    take_profit_3: float | None
    status: str = "ACTIVE"
    last_signal: str = ""
    last_price: float | None = None
    updated_at: str = ""


ACTIVE_TRACKS: dict[tuple[int, str, str], TrackedSignal] = {}


def track_report(user_id: int, symbol: str, timeframe: str, report) -> TrackedSignal:
    item = TrackedSignal(user_id, symbol, timeframe, str(report.signal).upper(), report.entry_price, report.stop_loss, report.take_profit_1, report.take_profit_2, report.take_profit_3, last_signal=str(report.signal).upper(), updated_at=datetime.now(timezone.utc).isoformat())
    ACTIVE_TRACKS[(user_id, symbol, timeframe)] = item
    return item


def stop_tracking(user_id: int, symbol: str, timeframe: str) -> bool:
    return ACTIVE_TRACKS.pop((user_id, symbol, timeframe), None) is not None


def list_tracking(user_id: int) -> list[TrackedSignal]:
    return [x for x in ACTIVE_TRACKS.values() if x.user_id == user_id]


def _target_event(item: TrackedSignal, high: float, low: float) -> str | None:
    if item.signal in {"BUY", "STRONG_BUY"}:
        if item.stop_loss is not None and low <= item.stop_loss:
            return "🛑 حد ضرر لمس شد"
        targets = (("TP1", item.take_profit_1), ("TP2", item.take_profit_2), ("TP3", item.take_profit_3))
        for label, target in targets:
            if target is not None and high >= target:
                return f"🎯 {label} لمس شد"
    elif item.signal in {"SELL", "STRONG_SELL"}:
        if item.stop_loss is not None and high >= item.stop_loss:
            return "🛑 حد ضرر لمس شد"
        targets = (("TP1", item.take_profit_1), ("TP2", item.take_profit_2), ("TP3", item.take_profit_3))
        for label, target in targets:
            if target is not None and low <= target:
                return f"🎯 {label} لمس شد"
    return None


async def refresh_tracking(item: TrackedSignal, notify: Callable[[str], Awaitable[None]]) -> TrackedSignal:
    candles = await MarketDataEngine().get_candles_list(item.symbol, item.timeframe, 300)
    if not candles:
        return item
    latest = candles[-1]
    high, low, close = float(latest.high), float(latest.low), float(latest.close)
    item.last_price = close
    target_event = _target_event(item, high, low)
    if target_event:
        item.status = "TARGET_REACHED" if "TP" in target_event else "STOPPED"
        await notify(f"📢 <b>به‌روزرسانی {item.symbol}</b>\n\n{target_event}\nقیمت فعلی: <b>{close}</b>")
        ACTIVE_TRACKS.pop((item.user_id, item.symbol, item.timeframe), None)
        return item

    report = await asyncio.to_thread(FullAnalysisEngine().analyze, candles)
    new_signal = str(report.signal).upper()
    old_signal = item.last_signal
    item.last_signal = new_signal
    item.updated_at = datetime.now(timezone.utc).isoformat()
    if new_signal != old_signal:
        item.status = "CHANGED" if new_signal != "NO_TRADE" else "INVALIDATED"
        await notify(f"📢 <b>به‌روزرسانی سیگنال {item.symbol}</b>\n\nسیگنال قبلی: <b>{old_signal}</b>\nسیگنال فعلی: <b>{new_signal}</b>\nقیمت: <b>{close}</b>")
    return item


__all__ = ["TrackedSignal", "track_report", "stop_tracking", "list_tracking", "refresh_tracking"]
