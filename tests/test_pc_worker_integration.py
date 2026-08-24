import asyncio

from worker.client import PCWorkerClient
from worker.contracts import JobRequest
from worker.dispatcher import WorkerDispatcher
from worker.handlers import register_default_handlers
from worker.runtime import WorkerRuntime


def test_all_declared_workloads_have_runtime_handlers():
    runtime = WorkerRuntime.create()
    register_default_handlers(runtime)
    assert runtime.capabilities.supported_jobs <= runtime.handlers.keys()


def test_dispatcher_accepts_declared_heavy_job():
    async def submit(request):
        return type("Result", (), {"status": "COMPLETED", "job_id": request.job_id})()

    result = asyncio.run(WorkerDispatcher(submit).submit(JobRequest("j1", "backtest")))
    assert result.status == "COMPLETED"


def test_client_offline_is_controlled():
    result = PCWorkerClient("http://127.0.0.1:1", "test", timeout=1).submit(JobRequest("j2", "backtest"))
    assert result.status == "WORKER_OFFLINE"
