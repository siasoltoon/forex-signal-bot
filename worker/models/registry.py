"""Model registry with explicit, serialisable model contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelSpec:
    name: str
    provider: str = "ollama"
    model: str = "qwen2.5-coder:7b"
    purpose: str = "coding_agent"
    context_window: int = 32768
    temperature: float = 0.1
    options: dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelSpec] = {}

    def register(self, spec: ModelSpec) -> None:
        if not spec.name.strip() or not spec.model.strip():
            raise ValueError("Model name and model identifier are required.")
        self._models[spec.name] = spec

    def get(self, name: str) -> ModelSpec:
        try:
            return self._models[name]
        except KeyError as exc:
            raise KeyError(f"Unknown model: {name}") from exc

    def list(self) -> tuple[ModelSpec, ...]:
        return tuple(self._models.values())

    @classmethod
    def default(cls) -> "ModelRegistry":
        registry = cls()
        registry.register(ModelSpec(name="coding", model="qwen2.5-coder:7b"))
        return registry


__all__ = ["ModelSpec", "ModelRegistry"]
