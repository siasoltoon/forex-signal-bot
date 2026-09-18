from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AnalysisMode(str, Enum):
    SMART = "smart"
    MANUAL = "manual"
    HYBRID = "hybrid"


@dataclass(frozen=True, slots=True)
class AnalysisStyle:
    name: str
    description: str = ""
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class StyleSelection:
    mode: AnalysisMode
    styles: tuple[str, ...] = ()
    suggested_styles: tuple[str, ...] = ()

    def allows(self, style: str) -> bool:
        if self.mode is AnalysisMode.SMART:
            return True
        return style in self.styles

    def effective_styles(self) -> tuple[str, ...]:
        if self.mode is AnalysisMode.HYBRID:
            return tuple(dict.fromkeys((*self.styles, *self.suggested_styles)))
        return self.styles


class StyleCatalog:
    def __init__(self, styles: tuple[AnalysisStyle, ...] = ()) -> None:
        self._styles = {style.name: style for style in styles if style.enabled}

    def names(self) -> tuple[str, ...]:
        return tuple(self._styles)

    def get(self, name: str) -> AnalysisStyle:
        try:
            return self._styles[name]
        except KeyError as exc:
            raise KeyError(f"unknown analysis style: {name}") from exc
