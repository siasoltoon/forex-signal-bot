from __future__ import annotations

from analysis.plugins import PluginDescriptor, PluginStatus


STYLE_CATALOG: tuple[PluginDescriptor, ...] = (
    PluginDescriptor("technical", "Technical Analysis", "technical", "Indicator and technical analysis"),
    PluginDescriptor("price_action", "Price Action", "price_action", "Classical and modern price action"),
    PluginDescriptor("smc", "Smart Money Concepts", "structure", "Liquidity and market-structure concepts"),
    PluginDescriptor("supply_demand", "Supply & Demand", "structure", "Supply and demand analysis"),
    PluginDescriptor("wyckoff", "Wyckoff", "structure", "Wyckoff methodology"),
    PluginDescriptor("elliott", "Elliott Wave", "wave", "Elliott wave analysis"),
    PluginDescriptor("harmonic", "Harmonic Trading", "pattern", "Harmonic pattern analysis"),
    PluginDescriptor("volume", "Volume Analysis", "volume", "Volume-based analysis"),
    PluginDescriptor("vwap", "VWAP", "volume", "VWAP analysis"),
    PluginDescriptor("volume_profile", "Volume Profile", "volume", "Volume profile analysis"),
    PluginDescriptor("momentum", "Momentum", "momentum", "Momentum analysis"),
    PluginDescriptor("volatility", "Volatility", "volatility", "Volatility analysis"),
    PluginDescriptor("market_structure", "Market Structure", "structure", "Market structure analysis"),
    PluginDescriptor("time_analysis", "Time Analysis", "time", "Time-based analysis"),
    PluginDescriptor("breakout", "Breakout Analysis", "pattern", "Breakout and false-breakout analysis"),
    PluginDescriptor("al_brooks", "Al Brooks", "price_action", "Al Brooks price-action module"),
    PluginDescriptor("lance_beggs", "Lance Beggs", "price_action", "Lance Beggs price-action module"),
)


def enabled_catalog() -> tuple[PluginDescriptor, ...]:
    return tuple(item for item in STYLE_CATALOG if item.status == PluginStatus.ENABLED)
