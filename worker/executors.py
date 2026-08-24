from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import ParameterGrid
from sklearn.preprocessing import StandardScaler


def _frame(payload: dict[str, Any]) -> pd.DataFrame:
    data = payload.get("data", payload.get("candles"))
    if data is None:
        raise ValueError("payload.data or payload.candles is required")
    frame = pd.DataFrame(data)
    if "close" not in frame.columns:
        raise ValueError("close column is required")
    return frame.copy()


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
    windows = []
    start = 0
    while start + train + test <= len(df):
        result = backtest({"data": df.iloc[start + train:start + train + test].to_dict("records")})
        windows.append(result)
        start += test
    return {"windows": len(windows), "results": windows}


def monte_carlo(payload: dict[str, Any]) -> dict[str, Any]:
    df = _frame(payload)
    n = int(payload.get("simulations", 1000))
    horizon = int(payload.get("horizon", 100))
    rng = np.random.default_rng(payload.get("seed"))
    returns = df["close"].pct_change().dropna().to_numpy()
    if len(returns) < 2:
        raise ValueError("at least two returns are required")
    paths = rng.choice(returns, size=(n, horizon), replace=True)
    terminal = np.prod(1 + paths, axis=1)
    return {"simulations": n, "horizon": horizon, "p05": float(np.quantile(terminal, .05)), "median": float(np.median(terminal)), "p95": float(np.quantile(terminal, .95))}


def feature_engineering(payload: dict[str, Any]) -> dict[str, Any]:
    df = _frame(payload)
    windows = payload.get("windows", [5, 10, 20])
    for w in windows:
        df[f"return_{w}"] = df["close"].pct_change(w)
        df[f"sma_{w}"] = df["close"].rolling(w).mean()
        df[f"volatility_{w}"] = df["close"].pct_change().rolling(w).std()
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    return {"rows": len(df), "columns": list(df.columns), "data": df.to_dict("records")}


def dataset_build(payload: dict[str, Any]) -> dict[str, Any]:
    result = feature_engineering(payload)
    return {"rows": result["rows"], "features": result["columns"], "data": result["data"]}


def random_forest_training(payload: dict[str, Any]) -> dict[str, Any]:
    x = np.asarray(payload["X"], dtype=float)
    y = np.asarray(payload["y"], dtype=float)
    test = int(payload.get("test_size", max(1, len(x) // 5)))
    if len(x) <= test + 1:
        raise ValueError("not enough samples")
    model = RandomForestRegressor(n_estimators=int(payload.get("n_estimators", 200)), random_state=42, n_jobs=-1)
    model.fit(x[:-test], y[:-test])
    pred = model.predict(x[-test:])
    return {"model": "random_forest", "mae": float(mean_absolute_error(y[-test:], pred)), "rmse": float(mean_squared_error(y[-test:], pred) ** .5), "feature_importance": model.feature_importances_.tolist()}


def xgboost_training(payload: dict[str, Any]) -> dict[str, Any]:
    from xgboost import XGBRegressor
    x = np.asarray(payload["X"], dtype=float); y = np.asarray(payload["y"], dtype=float)
    test = int(payload.get("test_size", max(1, len(x) // 5)))
    model = XGBRegressor(n_estimators=int(payload.get("n_estimators", 200)), max_depth=int(payload.get("max_depth", 6)), learning_rate=float(payload.get("learning_rate", .05)), objective="reg:squarederror", n_jobs=-1)
    model.fit(x[:-test], y[:-test])
    pred = model.predict(x[-test:])
    return {"model": "xgboost", "mae": float(mean_absolute_error(y[-test:], pred)), "rmse": float(mean_squared_error(y[-test:], pred) ** .5)}


def lightgbm_training(payload: dict[str, Any]) -> dict[str, Any]:
    from lightgbm import LGBMRegressor
    x = np.asarray(payload["X"], dtype=float); y = np.asarray(payload["y"], dtype=float)
    test = int(payload.get("test_size", max(1, len(x) // 5)))
    model = LGBMRegressor(n_estimators=int(payload.get("n_estimators", 200)), learning_rate=float(payload.get("learning_rate", .05)), verbosity=-1)
    model.fit(x[:-test], y[:-test])
    pred = model.predict(x[-test:])
    return {"model": "lightgbm", "mae": float(mean_absolute_error(y[-test:], pred)), "rmse": float(mean_squared_error(y[-test:], pred) ** .5)}


def model_evaluation(payload: dict[str, Any]) -> dict[str, Any]:
    y = np.asarray(payload["y"], dtype=float); pred = np.asarray(payload["pred"], dtype=float)
    return {"mae": float(mean_absolute_error(y, pred)), "rmse": float(mean_squared_error(y, pred) ** .5)}


def hyperparameter_optimization(payload: dict[str, Any]) -> dict[str, Any]:
    grid = payload.get("grid", {"n_estimators": [50, 100], "max_depth": [3, 6]})
    combos = list(ParameterGrid(grid))
    return {"candidates": len(combos), "parameters": combos[: int(payload.get("max_candidates", 100))]}


def heavy_market_scan(payload: dict[str, Any]) -> dict[str, Any]:
    markets = payload.get("markets", [])
    results = []
    for item in markets:
        frame = pd.DataFrame(item.get("data", []))
        if "close" not in frame or len(frame) < 2:
            continue
        ret = float(frame["close"].pct_change().iloc[-1])
        results.append({"symbol": item.get("symbol"), "return": ret})
    return {"count": len(results), "ranked": sorted(results, key=lambda x: abs(x["return"]), reverse=True)}


def register_real_executors(runtime) -> None:
    mapping = {
        "backtest": backtest, "walk_forward": walk_forward, "monte_carlo": monte_carlo,
        "feature_engineering": feature_engineering, "dataset_build": dataset_build,
        "random_forest_training": random_forest_training, "xgboost_training": xgboost_training,
        "lightgbm_training": lightgbm_training, "model_evaluation": model_evaluation,
        "hyperparameter_optimization": hyperparameter_optimization, "heavy_market_scan": heavy_market_scan,
    }
    for name, handler in mapping.items():
        runtime.register(name, handler)
