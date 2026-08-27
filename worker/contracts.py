from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


HEAVY_JOB_TYPES = {
    "backtest", "walk_forward", "monte_carlo", "hyperparameter_optimization",
    "feature_engineering", "multitimeframe_analysis", "heavy_market_scan",
    "ml_training", "xgboost_training", "lightgbm_training", "random_forest_training",
    "timeseries_training", "ensemble_training", "candle_batch_analysis", "dataset_build",
    "model_evaluation", "deep_learning_training", "transformer_training", "lstm_training",
    "gru_training", "medium_model_training", "multi_agent_analysis", "coding_agent",
}


@dataclass(frozen=True)
class WorkerCapabilities:
    cpu: bool = True
    gpu: bool = True
    max_ram_gb: int = 16
    supported_jobs: frozenset[str] = frozenset(HEAVY_JOB_TYPES)
    limited_jobs: frozenset[str] = frozenset({
        "deep_learning_training", "transformer_training", "lstm_training", "gru_training",
        "medium_model_training", "multi_agent_analysis", "coding_agent",
    })


@dataclass(frozen=True)
class JobRequest:
    job_id: str
    job_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 50
    timeout_seconds: int = 3600
    allow_cpu_fallback: bool = True


@dataclass(frozen=True)
class JobResult:
    job_id: str
    status: str
    job_type: str
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    worker_id: str | None = None


__all__ = ["HEAVY_JOB_TYPES", "WorkerCapabilities", "JobRequest", "JobResult"]
