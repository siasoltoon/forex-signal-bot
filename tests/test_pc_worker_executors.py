import numpy as np

from worker.executors import backtest, feature_engineering, monte_carlo, random_forest_training, walk_forward


def candles(n=120):
    close = 100 + np.cumsum(np.sin(np.arange(n) / 7) * .3 + .05)
    return [{"close": float(v)} for v in close]


def test_backtest():
    result = backtest({"data": candles()})
    assert "final_equity" in result
    assert result["trades"] >= 0


def test_walk_forward():
    result = walk_forward({"data": candles(), "train_size": 50, "test_size": 20})
    assert result["windows"] >= 1


def test_monte_carlo():
    result = monte_carlo({"data": candles(), "simulations": 100, "horizon": 20, "seed": 1})
    assert result["simulations"] == 100
    assert result["p05"] <= result["median"] <= result["p95"]


def test_feature_engineering():
    result = feature_engineering({"data": candles()})
    assert result["rows"] > 0
    assert "sma_20" in result["columns"]


def test_random_forest_training():
    x = np.arange(1000, dtype=float).reshape(100, 10)
    y = x.sum(axis=1)
    result = random_forest_training({"X": x.tolist(), "y": y.tolist(), "n_estimators": 20})
    assert result["model"] == "random_forest"
    assert result["rmse"] >= 0
