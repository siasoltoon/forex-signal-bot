from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class ModelInput:
    model_id: str
    version: str
    features: Mapping[str, Any]
    timestamp: str


@dataclass(frozen=True)
class ModelOutput:
    model_id: str
    version: str
    task: str
    value: Any
    confidence: float | None
    calibrated: bool
    metadata: Mapping[str, Any]


class ModelProvider(Protocol):
    model_id: str
    version: str
    async def predict(self, model_input: ModelInput) -> ModelOutput: ...


class ModelGateway:
    """Registry boundary for real models; never invents predictions."""
    def __init__(self, providers: Sequence[ModelProvider] = ()) -> None:
        self._providers = {p.model_id: p for p in providers}

    def register(self, provider: ModelProvider) -> None:
        self._providers[provider.model_id] = provider

    def get(self, model_id: str) -> ModelProvider | None:
        return self._providers.get(model_id)
