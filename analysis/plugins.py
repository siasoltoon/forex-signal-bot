from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from analysis.contracts import AnalysisContext, AnalysisOutput


class PluginStatus(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    UNAVAILABLE = "UNAVAILABLE"


class AnalysisPlugin(Protocol):
    key: str
    name: str
    status: PluginStatus

    def analyze(self, context: AnalysisContext) -> AnalysisOutput: ...


@dataclass(frozen=True, slots=True)
class PluginDescriptor:
    key: str
    name: str
    category: str
    description: str
    status: PluginStatus = PluginStatus.ENABLED
    supported_timeframes: tuple[str, ...] = ()


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, AnalysisPlugin] = {}
        self._descriptors: dict[str, PluginDescriptor] = {}

    def register(self, plugin: AnalysisPlugin, descriptor: PluginDescriptor | None = None) -> None:
        if plugin.key in self._plugins:
            raise ValueError(f"duplicate analysis plugin: {plugin.key}")
        self._plugins[plugin.key] = plugin
        self._descriptors[plugin.key] = descriptor or PluginDescriptor(
            key=plugin.key, name=plugin.name, category="analysis", description=plugin.name
        )

    def unregister(self, key: str) -> None:
        self._plugins.pop(key, None)
        self._descriptors.pop(key, None)

    def get(self, key: str) -> AnalysisPlugin:
        try:
            return self._plugins[key]
        except KeyError as exc:
            raise KeyError(f"unknown analysis plugin: {key}") from exc

    def descriptor(self, key: str) -> PluginDescriptor:
        return self._descriptors[key]

    def keys(self) -> tuple[str, ...]:
        return tuple(self._plugins)

    def list(self, *, enabled_only: bool = True) -> tuple[PluginDescriptor, ...]:
        values = tuple(self._descriptors.values())
        if not enabled_only:
            return values
        return tuple(item for item in values if item.status == PluginStatus.ENABLED)
