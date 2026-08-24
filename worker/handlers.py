from __future__ import annotations

from typing import Any, Callable

from .contracts import HEAVY_JOB_TYPES


def _status_handler(job_type: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def handler(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "accepted": True,
            "job_type": job_type,
            "execution": "pc_worker",
            "payload_keys": sorted(payload),
        }
    return handler


def register_default_handlers(runtime) -> None:
    """Register safe execution adapters for every declared workload.

    Algorithm implementations remain pluggable: this registry gives each workload a
    stable execution boundary so concrete backtesting/ML libraries can be attached
    independently without coupling Railway to them.
    """
    for job_type in HEAVY_JOB_TYPES:
        runtime.register(job_type, _status_handler(job_type))
