from __future__ import annotations

import os

from worker.contracts import JobRequest, JobResult
from worker.dispatcher import WorkerDispatcher
from services.worker.gateway import WorkerGateway
from worker.queue import WorkerQueue
from worker.pull_client import WorkerPullSettings


def test_pull_gateway_claim_and_complete(tmp_path) -> None:
    queue = WorkerQueue(str(tmp_path / "queue.sqlite3"))
    dispatcher = WorkerDispatcher(queue=queue)
    dispatcher.enqueue_only(JobRequest("pull-1", "backtest", {"data": [100, 101, 102]}))

    gateway = WorkerGateway(dispatcher, "secret")
    assert gateway.authenticate("Bearer secret")
    claim = gateway.claim()

    assert claim is not None
    assert claim["job_id"] == "pull-1"
    assert claim["claim_token"]

    result = gateway.result(
        {
            "job_id": "pull-1",
            "job_type": "backtest",
            "status": "COMPLETED",
            "output": {"ok": True},
            "claim_token": claim["claim_token"],
            "worker_id": "test-worker",
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["output"] == {"ok": True}
    queue.close()


def test_pull_gateway_rejects_invalid_token() -> None:
    queue = WorkerQueue(":memory:")
    gateway = WorkerGateway(WorkerDispatcher(queue=queue), "secret")
    assert not gateway.authenticate("Bearer wrong")
    assert not gateway.authenticate(None)
    queue.close()


def test_pull_settings_are_optional(monkeypatch) -> None:
    monkeypatch.delenv("WORKER_QUEUE_API_URL", raising=False)
    monkeypatch.delenv("PC_WORKER_TOKEN", raising=False)
    assert WorkerPullSettings.from_env() is None


def test_pull_settings_require_token(monkeypatch) -> None:
    monkeypatch.setenv("WORKER_QUEUE_API_URL", "https://example.test")
    monkeypatch.delenv("PC_WORKER_TOKEN", raising=False)
    try:
        WorkerPullSettings.from_env()
    except ValueError as exc:
        assert "PC_WORKER_TOKEN" in str(exc)
    else:
        raise AssertionError("missing worker token must be rejected")
