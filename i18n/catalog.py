from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MessageCatalog:
    locale: str
    messages: dict[str, str]

    def get(self, key: str, default: str | None = None) -> str:
        if key in self.messages:
            return self.messages[key]
        if default is not None:
            return default
        return key


PERSIAN = MessageCatalog("fa", {
    "analysis.no_trade": "عدم معامله",
    "analysis.buy": "خرید",
    "analysis.sell": "فروش",
    "analysis.wait": "انتظار",
    "system.error": "خطای سیستمی",
})

ENGLISH = MessageCatalog("en", {
    "analysis.no_trade": "NO TRADE",
    "analysis.buy": "BUY",
    "analysis.sell": "SELL",
    "analysis.wait": "WAIT",
    "system.error": "System error",
})
