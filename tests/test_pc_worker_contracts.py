from worker.contracts import HEAVY_JOB_TYPES, JobRequest, WorkerCapabilities
from worker.dispatcher import WorkerDispatcher


def test_requested_workloads_are_worker_owned():
    expected = {
        "backtest", "walk_forward", "monte_carlo", "hyperparameter_optimization",
        "feature_engineering", "multitimeframe_analysis", "heavy_market_scan",
        "ml_training", "xgboost_training", "lightgbm_training", "random_forest_training",
        "timeseries_training", "ensemble_training", "candle_batch_analysis", "dataset_build",
        "model_evaluation", "deep_learning_training", "transformer_training", "lstm_training",
        "gru_training", "medium_model_training", "multi_agent_analysis",
    }
    assert expected <= HEAVY_JOB_TYPES


def test_worker_hardware_capabilities():
    capabilities = WorkerCapabilities()
    assert capabilities.cpu is True
    assert capabilities.gpu is True
    assert capabilities.max_ram_gb == 16
    assert capabilities.limited_jobs


def test_offline_worker_does_not_block_railway():
    import asyncio
    request = JobRequest("test-1", "backtest", {"symbol": "EURUSD"})
    result = asyncio.run(WorkerDispatcher().submit(request))
    assert result.status == "WORKER_OFFLINE"
    assert result.job_id == "test-1"
