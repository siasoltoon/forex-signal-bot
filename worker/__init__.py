"""PC Worker package for heavy, optional computations."""

from .contracts import JobRequest, JobResult, WorkerCapabilities
from .dispatcher import WorkerDispatcher

__all__ = ["JobRequest", "JobResult", "WorkerCapabilities", "WorkerDispatcher"]
