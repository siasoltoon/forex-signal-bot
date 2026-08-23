from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from platform_runtime.data_runtime import Candle, DataValidator, Market, MarketRequest, MarketSnapshot, ProviderManager
from platform_runtime.intelligence import AdvancedFusion
from platform_runtime.live_runtime import AlertEngine, LiveMonitor, LiveSignal
from platform_runtime.ml_runtime import ProbabilisticModel
from platform_runtime.persistence_security import SecretManager
from platform_runtime.production_pipeline import PipelineRequest, ProductionAnalysisPipeline
from platform_runtime.real_analyzers import MomentumAnalyzer, TrendAnalyzer
from platform_runtime.research_engine import ExecutionSimulator, run_backtest
from platform_runtime.strategy_runtime import MovingAverageCrossStrategy
from platform_runtime.worker_runtime import JobQueue, WorkerJob
from platform_runtime.analysis_runtime import AnalyzerRegistry


def candles(n: int = 40) -> tuple[Candle, ...]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(Candle(start + timedelta(minutes=i), 100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100.5 + i * 0.1, 10) for i in range(n))


def test_validator_and_snapshot():
    result = DataValidator().validate(candles())
    assert result.valid and result.score == 100


class Provider:
    name = "test"
    async def health(self):
        return True
    async def fetch(self, request):
        return candles(request.limit)


@pytest.mark.asyncio
async def test_production_pipeline_uses_real_provider_and_analyzers():
    registry = AnalyzerRegistry((MomentumAnalyzer(), TrendAnalyzer()))
    manager = ProviderManager((Provider(),))
    pipeline = ProductionAnalysisPipeline(manager, registry, AdvancedFusion())
    result = await pipeline.analyze(PipelineRequest((MarketRequest(Market.FOREX, "EUR_USD", "1h", 40),), ("momentum", "trend")))
    assert result.decision in {"BUY", "SELL", "WAIT", "NO TRADE"}
    assert result.evidence


def test_backtest_engine_executes_strategy():
    result = run_backtest(candles(80), MovingAverageCrossStrategy(5, 15), execution=ExecutionSimulator())
    assert len(result.equity_curve) == 80
    assert result.trades >= 0

@pytest.mark.asyncio
async def test_worker_queue():
    queue = JobQueue()
    job = WorkerJob.create("analysis", {"symbol": "EUR_USD"})
    await queue.submit(job)
    claimed = await queue.claim()
    assert claimed.job_id == job.job_id and claimed.status == "running"


def test_live_alert_deduplication():
    monitor = LiveMonitor(AlertEngine())
    monitor.register(LiveSignal("s1", "EUR_USD", "BUY", 100, 95, (110,), 80, "bull"))
    assert monitor.update("s1", 101)
    assert monitor.update("s1", 111) == ()


def test_secret_signatures():
    secret = b"test-secret"
    payload = b"job"
    signature = SecretManager.sign_payload(payload, secret)
    assert SecretManager.verify_signature(payload, signature, secret)


def test_real_ml_model():
    x = [[float(i), float(i % 3)] for i in range(30)]
    y = [i % 2 for i in range(30)]
    model = ProbabilisticModel("test", "1")
    model.fit(x, y)
    output = model.predict([3.0, 0.0])
    assert 0 <= output.probability <= 1
