# PC Worker

The PC Worker is the optional heavy-computation tier for `forex-signal-bot`.

## Worker-owned workloads

- Backtesting and walk-forward testing
- Monte Carlo simulation
- Light/medium hyperparameter optimization
- Feature engineering and dataset generation
- Multi-timeframe computation
- Heavy market scanning and large candle batches
- Lightweight/medium ML: XGBoost, LightGBM, Random Forest
- Medium time-series models
- Ensemble models
- Model evaluation and comparison
- Limited deep learning, small transformers, LSTM/GRU, medium training, and multi-agent analysis

## Architecture rule

Railway remains the always-on Telegram/API/data/risk/tracking layer. Heavy jobs are submitted to the PC Worker through `WorkerDispatcher`. If the worker is offline, Railway must continue operating and return a controlled `WORKER_OFFLINE` result rather than blocking the bot.

## Hardware profile

The intended worker profile is 13th-generation Core i3 CPU, 16 GB RAM, and RX 580 6 GB GPU. GPU-heavy jobs must therefore be bounded and must support CPU fallback where practical.

Transport is intentionally not hard-coded in this package; a later worker transport can use authenticated HTTPS, WebSocket, or a queue without changing the job contracts.
