from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
@dataclass(frozen=True, slots=True)
class Asset:
    symbol: str
    market: str
    quote: str
class MultiMarketRegistry:
    def __init__(self, assets: Mapping[str, Asset] | None=None) -> None: self._assets=dict(assets or {})
    def register(self, asset: Asset) -> None: self._assets[asset.symbol]=asset
    def get(self, symbol: str) -> Asset: return self._assets[symbol]
    def symbols(self, market: str|None=None) -> tuple[str,...]:
        return tuple(k for k,v in self._assets.items() if market is None or v.market==market)
