from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelState(StrEnum):
    REGISTERED = "REGISTERED"
    CANDIDATE = "CANDIDATE"
    CHAMPION = "CHAMPION"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class ModelRecord:
    model_id: str
    version: str
    state: ModelState
    metadata: tuple[tuple[str, str], ...] = ()


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelRecord] = {}

    def register(self, model: ModelRecord) -> None:
        if not model.model_id.strip() or not model.version.strip():
            raise ValueError("model_id and version are required")
        self._models[model.model_id] = model

    def get(self, model_id: str) -> ModelRecord | None:
        return self._models.get(model_id)

    def transition(self, model_id: str, state: ModelState) -> ModelRecord:
        current = self._models[model_id]
        updated = ModelRecord(current.model_id, current.version, state, current.metadata)
        self._models[model_id] = updated
        return updated

    def all(self) -> tuple[ModelRecord, ...]:
        return tuple(self._models.values())
