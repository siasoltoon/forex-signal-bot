import asyncio

from worker.contracts import JobRequest
from worker.runtime import WorkerRuntime


def test_runtime_executes_registered_job():
    runtime = WorkerRuntime.create()

    async def handler(payload):
        return {"ok": True, "value": payload["value"] * 2}

    runtime.register("backtest", handler)
    result = asyncio.run(runtime.execute(JobRequest("job-1", "backtest", {"value": 21})))
    assert result.status == "COMPLETED"
    assert result.output == {"ok": True, "value": 42}


def test_runtime_handles_missing_handler():
    runtime = WorkerRuntime.create()
    result = asyncio.run(runtime.execute(JobRequest("job-2", "backtest")))
    assert result.status == "UNSUPPORTED"


def test_runtime_health_reports_worker_state():
    health = WorkerRuntime.create().health()
    assert health["status"] == "READY"
    assert health["max_ram_gb"] == 16
    assert "backtest" not in health["registered_jobs"]
