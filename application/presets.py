from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalysisPreset:
    name: str
    styles: tuple[str, ...]
    timeframes: tuple[str, ...] = ()
    mode: str = "manual"


class PresetStore:
    def __init__(self) -> None:
        self._presets: dict[str, dict[str, AnalysisPreset]] = {}

    def save(self, user_id: str, preset: AnalysisPreset) -> None:
        self._presets.setdefault(user_id, {})[preset.name] = preset

    def get(self, user_id: str, name: str) -> AnalysisPreset | None:
        return self._presets.get(user_id, {}).get(name)

    def delete(self, user_id: str, name: str) -> bool:
        return self._presets.get(user_id, {}).pop(name, None) is not None

    def list(self, user_id: str) -> tuple[AnalysisPreset, ...]:
        return tuple(self._presets.get(user_id, {}).values())
