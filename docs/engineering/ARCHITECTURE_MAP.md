# Architecture Map — Multi-Asset Trading Intelligence Platform

## System Overview
Python multi-asset trading-intelligence application with Telegram interface, market-data/provider layer, modular analysis, decision/risk components, dormant/unwired AI/ML capability, PC Worker for heavy application processing, durable processing queue, and deployment/CI infrastructure.

## Canonical Boundaries
- Telegram: `services/telegram/`
- Market-data facade: `services/market_data/service.py`
- Market-data engine: `data/market_data.py`
- Provider routing/fallback: `ProviderManager`
- Analysis: `analysis/full_engine.py`
- Decision: `analysis/decision_engine.py`
- Risk: `analysis/risk_engine.py`
- Portfolio: `analysis/portfolio_engine.py`
- Position sizing: `analysis/position_sizing.py`
- Currency conversion: `services/market_data/currency_conversion.py`
- Heavy processing: `worker/`

## Multi-Asset Contract
The platform supports Forex, Crypto, Stocks, Indices, and Commodities through centralized symbol/asset metadata. Market-specific quote currency, contract size, session, provider capability, and conversion requirements must be explicit. Unsupported or unavailable conditions fail closed.

## Market Data
Canonical flow:
`Multi-Asset caller → MarketDataService → MarketDataEngine → ProviderManager → provider(s)`.
MarketDataEngine owns candle quality/freshness gates. ProviderManager owns provider routing/fallback/retry/cooldown. Provider capability mismatches fail closed instead of being treated as transient outages.

## Analysis / Decision / Risk
`analysis/full_engine.py` is the production analysis orchestrator.
Analysis produces analytical inputs → DecisionEngine produces the decision → RiskEngine applies risk policy → PositionSizing/CurrencyConversion provide sizing where required.
The dormant `ai/` package is not in canonical production scoring.

## Portfolio / Heavy Research
`analysis/portfolio_engine.py` owns multi-asset exposure, concentration, correlation, drawdown, and deterministic stress calculations. Large correlation, stress, sensitivity, and counterfactual batches are routed through `worker/` and never require Railway to become a compute server.

## Worker / Queue
`worker/` provides the PC Worker runtime, authenticated HTTP boundary, dispatcher, durable queue, and heavy executors. The worker is an application-processing component, not a local coding/model orchestration layer.

## Market Status
Canonical states are `OPEN`, `CLOSED`, `STALE`, and `NO_DATA`. Future/invalid timestamps and stale data fail closed; weekend closure is asset-aware and does not incorrectly treat Crypto as a non-24/7 market.

## Persistence
Worker queue and Telegram persistence boundaries are durable and fail closed on corruption/invalid state according to their established contracts.

## Security / Deployment
Production configuration, worker authentication/input validation, Docker non-root execution, secret/build-context exclusion, CI permissions, and dependency auditing were covered by the historical Phase-10 closure. Railway is an infrastructure target, not a core architecture dependency.

## Testing / CI
Current verification must always use the exact current `main` HEAD. Historical closure SHAs are evidence of prior states, not proof of current state.

## Current Integrity Status
- Historical Phases 1–11: closure evidence preserved.
- Phase 12: **reverification required** because the current HEAD has a failing Railway deployment status.
- Phase 13: blocked until Phase 12 and cross-phase integrity are resolved.

## Audit Rule
When concrete evidence reopens a phase, audit the full phase surface and dependent boundaries, not only the old task list. Fix related concrete defects together, add regression coverage, run the required verification set, and only then restore the phase to current-HEAD verified status.

## Paper / Replay Boundaries
`services/paper_trading.py` is an isolated paper ledger and shadow comparison boundary; it does not authorize live orders. Historical market replay is a PC Worker workload and returns traceable decision observations. Time Machine orchestration remains separate until replay, counterfactuals, and persistent scenario selection are connected end-to-end.

## Analysis Profiles / Shared Execution Contract
User configuration is represented as AnalysisProfile objects containing versioned style selections, symbols, timeframes, risk level, and schedule. Presets are convenience configurations; Customize exposes the canonical Style Registry and permits multiple styles per profile.

Canonical flow:
Telegram User → AnalysisProfile → selected styles → FullAnalysisEngine → DecisionEngine → RiskEngine

The same FullAnalysisEngine style-weighting path is used by live analysis and the PC Worker profile_backtest executor. Backtest payloads carry profile_id, profile_version, and style_ids so historical results remain tied to the exact profile configuration used. Live scanning groups recipients by active profile and never sends a decision generated for a different profile.


### Profile Execution Context
profiles/execution.py is the canonical boundary between user configuration and execution. It freezes profile identity/version, enabled styles, symbols, timeframes, risk, schedule, and a configuration snapshot for LIVE/BACKTEST/REPLAY/RESEARCH contexts.

Live scanning and Worker historical evaluation both consume this contract. Scanner state and notification deduplication are profile-scoped; a profile's historical result retains its profile version and snapshot so later profile edits do not rewrite historical meaning.


### Profile Style Decomposition
For a profile with multiple selected styles, the shared analysis snapshot is evaluated once and then each selected style receives its own deterministic DecisionEngine result before the combined profile decision. This keeps style conflicts observable without creating separate market-data or indicator pipelines.

Historical Worker jobs may carry user scope, profile ID/version, exact profile snapshot, experiment ID, and requested capabilities through the canonical `ProfileExecutionContext`/payload contract. Snapshot identity and version mismatches fail closed.\n\n## PC Worker Pull Transport — 2026-09-21\nCanonical remote-worker flow:\n`Application → WorkerProcessingService → durable SQLite queue → authenticated Railway worker gateway → outbound HTTPS PC Worker pull client → local WorkerRuntime`.\n\n- Railway remains the queue/control plane and deployment target, not the heavy compute host.\n- The Windows PC Worker initiates outbound HTTPS requests; no public PC endpoint or tunnel is required.\n- Claim tokens fence stale workers; leases can be renewed during long-running jobs.\n- Terminal worker results are applied only through the durable queue boundary.\n- Local Worker HTTP remains bound to the local diagnostic interface and is not the remote transport.\n- Pull transport is optional and must fail closed when its token/configuration is incomplete.\n