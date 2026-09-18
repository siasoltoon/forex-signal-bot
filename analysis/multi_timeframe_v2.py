from __future__ import annotations

from dataclasses import dataclass


DEFAULT_TIMEFRAMES: tuple[str, ...] = ("1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w")


@dataclass(frozen=True, slots=True)
class TimeframeRole:
    timeframe: str
    role: str  # context, structure, entry, or custom


@dataclass(frozen=True, slots=True)
class TimeframePlan:
    roles: tuple[TimeframeRole, ...]

    @property
    def timeframes(self) -> tuple[str, ...]:
        return tuple(item.timeframe for item in self.roles)

    def role_for(self, timeframe: str) -> str | None:
        for item in self.roles:
            if item.timeframe == timeframe:
                return item.role
        return None


class MultiTimeframePlanner:
    def build(self, timeframes: tuple[str, ...]) -> TimeframePlan:
        normalized = tuple(dict.fromkeys(value.strip().lower() for value in timeframes if value.strip()))
        if not normalized:
            raise ValueError("at least one timeframe is required")
        roles: list[TimeframeRole] = []
        for index, timeframe in enumerate(normalized):
            if index == 0:
                role = "context"
            elif index == len(normalized) - 1 and len(normalized) > 1:
                role = "entry"
            else:
                role = "structure"
            roles.append(TimeframeRole(timeframe, role))
        return TimeframePlan(tuple(roles))

    def alignment(self, directions: dict[str, str]) -> str:
        values = {value.upper() for value in directions.values() if value}
        if not values:
            return "UNKNOWN"
        if len(values) == 1:
            return "ALIGNED"
        if "NEUTRAL" in values and len(values) == 2:
            return "MIXED"
        return "CONFLICT"
