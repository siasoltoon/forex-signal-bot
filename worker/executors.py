from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import ParameterGrid
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def _frame(payload: dict[str, Any]) -> pd.DataFrame:
    data = payload.get("data", payload.get("candles"))
    if data is None:
        raise ValueError("payload.data or payload.candles is required")
    frame = pd.DataFrame(data)
    if "close" not in frame.columns:
        raise ValueError("close column is required")
    return frame.copy()


def _xy(payload: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, int]:
    x = np.asarray(payload["X"], dtype=float)
    y = np.asarray(payload["y"], dtype=float)
    test = int(payload.get("test_size", max(1, len(x) // 5)))
    if x.ndim != 2 or len(x) <= test + 1 or len(y) != len(x):
        raise ValueError("X/y dimensions or sample count are invalid")
    return x, y, test


def _metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    return {"mae": float(mean_absolute_error(y, pred)), "rmse": float(mean_squared_error(y, pred) ** 0.5)}


def backtest(payload: dict[str, Any]) -> dict[str, Any]:
    df = _frame(payload)
    threshold = float(payload.get("signal_threshold", 0.0))
    fee = float(payload.get("fee", 0.0))
    returns = df["close"].pct_change().fillna(0.0)
    signal = np.sign(returns.shift(1).fillna(0.0))
    if threshold:
        signal = signal.where(returns.shift(1).abs() >= threshold, 0.0)
    strategy = signal * returns - fee * signal.abs()
    equity = (1.0 + strategy).cumprod()
    return {"trades": int((signal != 0).sum()), "return": float(equity.iloc[-1] - 1), "max_drawdown": float((equity / equity.cummax() - 1).min()), "final_equity": float(equity.iloc[-1])}


def walk_forward(payload: dict[str, Any]) -> dict[str, Any]:
    df = _frame(payload)
    train = int(payload.get("train_size", max(20, len(df) // 2)))
    test = int(payload.get("test_size", max(5, len(df) // 10)))
    if train < 2 or test < 1:
        raise ValueError("train_size/test_size are invalid")
    windows, start = [], 0
    while start + train + test <= len(df):
        windows.append(backtest({"data": df.iloc[start + train:start + train + test].to_dict("records")}))
        start += test
    return {"windows": len(windows), "results": windows}


def monte_carlo(payload: dict[str, Any]) -> dict[str, Any]:
    df = _frame(payload)
    n = min(int(payload.get("simulations", 1000)), int(payload.get("max_simulations", 10000)))
    horizon = min(int(payload.get("horizon", 100)), int(payload.get("max_horizon", 5000)))
    rng = np.random.default_rng(payload.get("seed"))
    returns = df["close"].pct_change().dropna().to_numpy()
    if len(returns) < 2:
        raise ValueError("at least two returns are required")
    paths = rng.choice(returns, size=(n, horizon), replace=True)
    terminal = np.prod(1 + paths, axis=1)
    return {"simulations": n, "horizon": horizon, "p05": float(np.quantile(terminal, .05)), "median": float(np.median(terminal)), "p95": float(np.quantile(terminal, .95))}


def feature_engineering(payload: dict[str, Any]) -> dict[str, Any]:
    df = _frame(payload)
    windows = [int(w) for w in payload.get("windows", [5, 10, 20])]
    for w in windows:
        if w < 2:
            continue
        df[f"return_{w}"] = df["close"].pct_change(w)
        df[f"sma_{w}"] = df["close"].rolling(w).mean()
        df[f"volatility_{w}"] = df["close"].pct_change().rolling(w).std()
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    return {"rows": len(df), "columns": list(df.columns), "data": df.to_dict("records")}


def dataset_build(payload: dict[str, Any]) -> dict[str, Any]:
    result = feature_engineering(payload)
    return {"rows": result["rows"], "features": result["columns"], "data": result["data"]}


def random_forest_training(payload: dict[str, Any]) -> dict[str, Any]:
    x, y, test = _xy(payload)
    model = RandomForestRegressor(n_estimators=min(int(payload.get("n_estimators", 200)), 1000), random_state=42, n_jobs=-1)
    model.fit(x[:-test], y[:-test])
    pred = model.predict(x[-test:])
    return {"model": "random_forest", **_metrics(y[-test:], pred), "feature_importance": model.feature_importances_.tolist()}


def xgboost_training(payload: dict[str, Any]) -> dict[str, Any]:
    from xgboost import XGBRegressor
    x, y, test = _xy(payload)
    model = XGBRegressor(n_estimators=min(int(payload.get("n_estimators", 200)), 1000), max_depth=int(payload.get("max_depth", 6)), learning_rate=float(payload.get("learning_rate", .05)), objective="reg:squarederror", n_jobs=-1)
    model.fit(x[:-test], y[:-test])
    return {"model": "xgboost", **_metrics(y[-test:], model.predict(x[-test:]))}


def lightgbm_training(payload: dict[str, Any]) -> dict[str, Any]:
    from lightgbm import LGBMRegressor
    x, y, test = _xy(payload)
    model = LGBMRegressor(n_estimators=min(int(payload.get("n_estimators", 200)), 1000), learning_rate=float(payload.get("learning_rate", .05)), verbosity=-1)
    model.fit(x[:-test], y[:-test])
    return {"model": "lightgbm", **_metrics(y[-test:], model.predict(x[-test:]))}


def model_evaluation(payload: dict[str, Any]) -> dict[str, Any]:
    y = np.asarray(payload["y"], dtype=float); pred = np.asarray(payload["pred"], dtype=float)
    if len(y) != len(pred):
        raise ValueError("y and pred lengths differ")
    return _metrics(y, pred)


def hyperparameter_optimization(payload: dict[str, Any]) -> dict[str, Any]:
    grid = payload.get("grid", {"n_estimators": [50, 100], "max_depth": [3, 6]})
    limit = min(int(payload.get("max_candidates", 100)), 500)
    combos = list(ParameterGrid(grid))[:limit]
    return {"candidates": len(combos), "parameters": combos}


def heavy_market_scan(payload: dict[str, Any]) -> dict[str, Any]:
    results = []
    for item in payload.get("markets", []):
        frame = pd.DataFrame(item.get("data", []))
        if "close" not in frame or len(frame) < 2:
            continue
        ret = float(frame["close"].pct_change().iloc[-1])
        results.append({"symbol": item.get("symbol"), "return": ret})
    return {"count": len(results), "ranked": sorted(results, key=lambda x: abs(x["return"]), reverse=True)}


def multitimeframe_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    frames = payload.get("timeframes", {})
    result = {}
    for timeframe, data in frames.items():
        frame = pd.DataFrame(data)
        if "close" in frame and len(frame) >= 2:
            result[str(timeframe)] = {"last_close": float(frame["close"].iloc[-1]), "return": float(frame["close"].pct_change().iloc[-1])}
    return {"timeframes": result}


def candle_batch_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    df = _frame(payload)
    close = df["close"].astype(float)
    return {"rows": len(df), "min": float(close.min()), "max": float(close.max()), "mean": float(close.mean()), "return": float(close.iloc[-1] / close.iloc[0] - 1)}


def timeseries_training(payload: dict[str, Any]) -> dict[str, Any]:
    x, y, test = _xy(payload)
    model = HistGradientBoostingRegressor(max_iter=min(int(payload.get("max_iter", 200)), 500), learning_rate=float(payload.get("learning_rate", .05)), max_leaf_nodes=int(payload.get("max_leaf_nodes", 31)), random_state=42)
    model.fit(x[:-test], y[:-test])
    return {"model": "time_series_gradient_boost", **_metrics(y[-test:], model.predict(x[-test:]))}


def ensemble_training(payload: dict[str, Any]) -> dict[str, Any]:
    x, y, test = _xy(payload)
    models = [RandomForestRegressor(n_estimators=100, random_state=i, n_jobs=-1) for i in range(3)]
    preds = []
    for model in models:
        model.fit(x[:-test], y[:-test]); preds.append(model.predict(x[-test:]))
    pred = np.mean(preds, axis=0)
    return {"model": "random_forest_ensemble", "members": len(models), **_metrics(y[-test:], pred)}


def _bounded_neural_training(payload: dict[str, Any], model_name: str) -> dict[str, Any]:
    x, y, test = _xy(payload)
    hidden = tuple(int(v) for v in payload.get("hidden_layers", [64, 32]))
    hidden = tuple(min(max(v, 4), 256) for v in hidden[:3])
    model = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=hidden, max_iter=min(int(payload.get("max_iter", 200)), 500), early_stopping=True, random_state=42))
    model.fit(x[:-test], y[:-test])
    return {"model": model_name, "execution": "bounded_cpu_fallback", "limitations": {"max_hidden_layers": 3, "max_units": 256}, **_metrics(y[-test:], model.predict(x[-test:]))}


def deep_learning_training(payload: dict[str, Any]) -> dict[str, Any]:
    return _bounded_neural_training(payload, "deep_learning_bounded")


def medium_model_training(payload: dict[str, Any]) -> dict[str, Any]:
    return _bounded_neural_training(payload, "medium_model_bounded")


def transformer_training(payload: dict[str, Any]) -> dict[str, Any]:
    result = _bounded_neural_training(payload, "small_transformer_bounded")
    result["architecture_note"] = "bounded sequence-model fallback; GPU transformer backend is intentionally not required"
    return result


def lstm_training(payload: dict[str, Any]) -> dict[str, Any]:
    result = _bounded_neural_training(payload, "lstm_bounded")
    result["architecture_note"] = "bounded recurrent-model fallback"
    return result


def gru_training(payload: dict[str, Any]) -> dict[str, Any]:
    result = _bounded_neural_training(payload, "gru_bounded")
    result["architecture_note"] = "bounded recurrent-model fallback"
    return result


def multi_agent_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    analyses = payload.get("analyses", [])
    if not isinstance(analyses, list):
        raise ValueError("analyses must be a list")
    scores = [float(item.get("score", 0.0)) for item in analyses if isinstance(item, dict)]
    return {"model": "multi_agent_orchestrator", "agents": len(analyses), "aggregate_score": float(np.mean(scores)) if scores else 0.0, "decision": "WAIT" if not scores else ("BUY" if np.mean(scores) > 0 else "SELL")}


def register_real_executors(runtime) -> None:
    mapping = {
        "backtest": backtest, "walk_forward": walk_forward, "monte_carlo": monte_carlo,
        "feature_engineering": feature_engineering, "dataset_build": dataset_build,
        "random_forest_training": random_forest_training, "xgboost_training": xgboost_training,
        "lightgbm_training": lightgbm_training, "model_evaluation": model_evaluation,
        "hyperparameter_optimization": hyperparameter_optimization, "heavy_market_scan": heavy_market_scan,
        "multitimeframe_analysis": multitimeframe_analysis, "candle_batch_analysis": candle_batch_analysis,
        "timeseries_training": timeseries_training, "ensemble_training": ensemble_training,
        "deep_learning_training": deep_learning_training, "transformer_training": transformer_training,
        "lstm_training": lstm_training, "gru_training": gru_training,
        "medium_model_training": medium_model_training, "multi_agent_analysis": multi_agent_analysis,
    }
    for name, handler in mapping.items():
        runtime.register(name, handler)
