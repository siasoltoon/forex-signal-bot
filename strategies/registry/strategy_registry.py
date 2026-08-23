from __future__ import annotations

from strategies.contracts.strategy import Strategy


class StrategyRegistry:
    """Explicit registry for strategy plugins."""

    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        strategy_id = strategy.strategy_id
        if not strategy_id:
            raise ValueError("strategy_id cannot be empty")
        if strategy_id in self._strategies:
            raise ValueError(f"strategy already registered: {strategy_id}")
        self._strategies[strategy_id] = strategy

    def unregister(self, strategy_id: str) -> None:
        self._strategies.pop(strategy_id, None)

    def get(self, strategy_id: str) -> Strategy:
        try:
            return self._strategies[strategy_id]
        except KeyError as exc:
            raise KeyError(f"unknown strategy: {strategy_id}") from exc

    def all(self) -> tuple[Strategy, ...]:
        return tuple(self._strategies.values())

    def supported(self, context) -> tuple[Strategy, ...]:
        return tuple(
            strategy
            for strategy in self._strategies.values()
            if strategy.supports(context)
        )
