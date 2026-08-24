import numpy as np

from worker.executors import (
    backtest, candle_batch_analysis, deep_learning_training, ensemble_training,
    feature_engineering, gru_training, lstm_training, monte_carlo,
    multitimeframe_analysis, multi_agent_analysis, random_forest_training,
    timeseries_training, transformer_training, walk_forward,
)


def candles(n=120):
    close = 100 + np.cumsum(np.sin(np.arange(n) / 7) * .3 + .05)
    return [{"close": float(v)} for v in close]


def xy():
    x = np.arange(1200, dtype=float).reshape(120, 10)
    y = x.sum(axis=1) + np.sin(np.arange(120))
    return x.tolist(), y.tolist()


def test_core_executors():
    data = candles()
    assert backtest({"data": data})["trades"] >= 0
    assert walk_forward({"data": data, "train_size": 50, "test_size": 20})["windows"] >= 1
    mc = monte_carlo({"data": data, "simulations": 100, "horizon": 20, "seed": 1})
    assert mc["p05"] <= mc["median"] <= mc["p95"]
    assert feature_engineering({"data": data})["rows"] > 0
    assert candle_batch_analysis({"data": data})["rows"] == 120


def test_timeframe_and_ensemble():
    data = candles()
    assert multitimeframe_analysis({"timeframes": {"M5": data, "H1": data}})["timeframes"]
    x, y = xy()
    assert ensemble_training({"X": x, "y": y, "test_size": 20})["members"] == 3
    assert timeseries_training({"X": x, "y": y, "test_size": 20})["model"] == "time_series_gradient_boost"


def test_bounded_limited_models():
    x, y = xy()
    for fn, name in [(deep_learning_training, "deep_learning_bounded"), (transformer_training, "small_transformer_bounded"), (lstm_training, "lstm_bounded"), (gru_training, "gru_bounded")]:
        result = fn({"X": x, "y": y, "test_size": 20, "max_iter": 20, "hidden_layers": [16, 8]})
        assert result["model"] == name
        assert result["execution"] == "bounded_cpu_fallback"


def test_random_forest():
    x, y = xy()
    result = random_forest_training({"X": x, "y": y, "n_estimators": 20})
    assert result["model"] == "random_forest"
    assert result["rmse"] >= 0


def test_multi_agent_orchestration():
    result = multi_agent_analysis({"analyses": [{"score": 1}, {"score": -0.5}, {"score": 0.2}]})
    assert result["agents"] == 3
    assert result["decision"] in {"BUY", "SELL", "WAIT"}
