from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class AnalysisMode(StrEnum):
    SMART = "SMART"
    MANUAL = "MANUAL"
    HYBRID = "HYBRID"


@dataclass(frozen=True, slots=True)
class AnalysisSelection:
    mode: AnalysisMode
    styles: tuple[str, ...] = ()
    suggested_styles: tuple[str, ...] = ()

    def effective_styles(self) -> tuple[str, ...]:
        if self.mode == AnalysisMode.SMART:
            return self.suggested_styles
        if self.mode == AnalysisMode.MANUAL:
            return self.styles
        return tuple(dict.fromkeys((*self.styles, *self.suggested_styles)))


@dataclass(slots=True)
class PresetStore:
    _presets: dict[str, AnalysisSelection] = field(default_factory=dict)

    def save(self, name: str, selection: AnalysisSelection) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("preset name cannot be empty")
        self._presets[normalized] = selection

    def get(self, name: str) -> AnalysisSelection:
        return self._presets[name]

    def delete(self, name: str) -> None:
        self._presets.pop(name, None)

    def names(self) -> tuple[str, ...]:
        return tuple(self._presets)


def validate_selection(selection: AnalysisSelection, available: set[str]) -> None:
    requested = set(selection.styles) | set(selection.suggested_styles)
    unknown = requested - available
    if unknown:
        raise ValueError(f"unknown analysis styles: {sorted(unknown)}")
    if selection.mode == AnalysisMode.MANUAL and not selection.styles:
        raise ValueError("manual mode requires at least one selected style")
