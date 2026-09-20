# Engineering Changelog

## 2026-09-19 — Phase 6 AI/ML boundary closure
- TASK-115 changed the example AI configuration to explicit opt-in by setting `AI_ENABLED=false`.
- TASK-115 changed production readiness so missing AI credentials are warned about only when AI is explicitly enabled.
- TASK-116 removed the dormant AI component from `AnalysisScorer`; legacy `ai_score` no longer influences canonical production scoring.
- TASK-117 hardened AI configuration and response boundaries against non-finite values.
- TASK-118 completed the repository-wide AI/ML boundary audit.
- Existing `ai/` capability remains isolated and dormant; it was not activated.
- No Ollama, coding-agent, autonomous-agent, or model-orchestration architecture was introduced.
- Final Phase-6 code HEAD: `91a59421cbd82043cec59bc9f5fe883796a1a8da`; all seven required checks completed successfully.



## 2026-09-19 — Multi-Asset closure audit continuation
- Corrected engineering scope documentation to explicitly preserve Forex, Crypto, Stocks, Indices, and Commodities.
- TASK-119 hardened PC Worker readiness against stale/future/malformed heartbeats and reflected degraded readiness in health.
- TASK-120 hardened Telegram scanner environment overrides against unsupported symbols.
- Added focused regression coverage for both production-boundary fixes.
- Updated phase/task/test engineering state; exact-head CI verification remains required before marking the new tasks VERIFIED.


## 2026-09-19 — Phase 7 PC Worker / Heavy Processing closure
- Verified TASK-119, TASK-120, and TASK-121 on exact closure HEAD `d34a8836ff5a2e1c8820540dd1d6cc5bff473f8a`.
- TASK-122 completed the full Phase-7 cross-layer audit across WorkerRuntime, WorkerHTTPServer, PCWorkerClient, WorkerDispatcher, WorkerQueue, application readiness, recovery, shutdown, and security boundaries.
- No additional repository-backed Phase-7 correctness gap requiring code changes was identified.
- All seven required GitHub Actions workflows completed successfully on the exact closure HEAD.
- Phase 7 is now COMPLETE; Phase 8 — Trading / Decision Engine — is the next audit frontier.


## 2026-09-19 — Phase 8 Trading / Decision Engine closure
- TASK-123 hardened `MarketAwareAnalysisEngine` against mismatched candle symbols and stale/future market inputs before decision/risk evaluation.
- Preserved the existing compatibility contract for legacy candle-like inputs that do not expose market metadata.
- Added regression coverage for symbol mismatch, stale input, and future-dated input.
- TASK-124 completed the full Phase-8 cross-layer audit across DecisionEngine, ConfidenceEngine, RiskEngine, PositionSizing, CurrencyConversionService, and MarketAwareAnalysisEngine.
- No additional repository-backed Phase-8 correctness gap was identified.
- Code closure HEAD: `1edbf5126c86bcde45c32cf91e365d22e20e4037`; all seven required GitHub Actions checks completed successfully.
- Phase 8 is now COMPLETE; Phase 9 — Backtesting / Simulation — is the next audit frontier.


## Phase 9 — Backtesting / Simulation Closure
- TASK-125 completed the full Phase-9 cross-layer closure audit.
- Hardened backtest inputs against missing, non-numeric, non-finite, and non-positive close prices.
- Added validation for non-negative signal thresholds, bounded fees, simulation counts, and simulation horizons.
- Corrected walk-forward evaluation so the training history is available for the first test signal while only the test segment contributes to reported performance.
- Added deterministic seeded Monte Carlo regression coverage and fail-closed invalid-input coverage.
- Code closure HEAD: `d616df74377af7de1aaf798c7b876fe8acecee60`; all seven required GitHub Actions checks completed successfully.
- Phase 9 is COMPLETE; Phase 10 — Security / Production Hardening — is the next audit frontier.


## 2026-09-19 — Phase 10 Security / Production Hardening checkpoint
- TASK-126 hardened `WorkerHTTPServer` request validation against malformed JSON shapes, invalid timeout/priority values, oversized identifiers, and non-object payloads.
- Added regression coverage in `tests/test_pc_worker_health_security.py`.
- Hardened the production Docker image to run as a dedicated non-root user.
- Restricted production CI workflow permissions to `contents: read` where write access is unnecessary.
- Exact audit HEAD: `b92aae52828e7737402da30ec5d513df4c8b0dad`; all seven required GitHub Actions checks completed successfully.
- Phase 10 remains open for additional concrete security/production-hardening audit work.


## 2026-09-19 — Phase 10 Security / Production Hardening closure
- TASK-127 completed the broader security/production-hardening closure audit.
- Hardened production configuration so `DEBUG=true` fails closed in production and PC Worker URLs reject malformed/credential-bearing/fragmented URLs; blank worker tokens are rejected.
- Hardened WorkerHTTPServer boolean request validation for `allow_cpu_fallback`.
- Added `.dockerignore` to prevent `.env`, logs, VCS metadata, and local development artifacts from entering Docker build context.
- Reviewed health exposure, dependency auditing, CI permissions, secret handling, and error/logging boundaries; no additional repository-backed gap requiring code changes was identified.
- Phase 10 is COMPLETE; Phase 11 — Testing — is the next audit frontier.

## 2026-09-19 — Phase 11 Testing / CI Verification closure
- TASK-128 completed the full Testing / CI Verification closure audit.
- Concrete gap found: several CI verification workflows used Python 3.11 while the production Docker runtime is Python 3.12.
- Aligned Security Audit, Production E2E Contract Gate, Production Live Smoke, Final Integration Gate, Production Activation Gate, and Production Activation Validation to Python 3.12; Test and Production Readiness were already aligned.
- Final Phase-11 HEAD: b457ea33796b5833622cda4c9e7f5ecf13eabfc3.
- All seven required workflows completed successfully on the exact final HEAD.
- No additional repository-backed Phase-11 testing gap requiring code changes was identified.
- Phase 11 is COMPLETE; Phase 13 — Final Production Audit — is the next unresolved phase frontier.


## 2026-09-19 — Current-HEAD cross-phase integrity audit opened
- Audited the recorded Phase 1–12 closure state against the current repository baseline.
- Confirmed the product scope is Multi-Asset: Forex, Crypto, Stocks, Indices, and Commodities.
- Found an engineering-state consistency problem: phase documents mixed historical closure claims with current verification claims and contained contradictory/duplicated roadmap statements.
- Found a concrete current production-verification issue: the combined status for the audited `main` baseline contained a failing Railway deployment status (`lavish-energy - forex-signal-bot`).
- No code regression is declared solely from that external deployment failure; deployment re-verification is required before Phase 13.
- Normalized engineering state so historical closure evidence is distinguished from current-HEAD verification.
- Phase 12 is the active re-verification frontier; Phase 13 remains blocked pending that verification.


## 2026-09-19 — Phase 13 Code Audit: Startup Readiness and CI Surface Hardening
- Opened Phase 13 as an active current-HEAD code audit while intentionally deferring Railway deployment verification until the code surface is synchronized.
- Fixed application startup ordering so the HTTP health endpoint is available before service initialization; dependency startup now leaves the health endpoint returning degraded/not-ready state instead of leaving the port unavailable.
- Added lifecycle regression coverage for health-first startup and rollback when either the health server or service startup fails.
- Removed obsolete PR-targeted automation/provider-contract runner workflows that wrote directly to repository branches and were no longer part of the production CI contract.
- Removed the obsolete dedicated automation branch trigger from the main test workflow.
- Explicitly restricted remaining production verification workflows to contents: read where no write access is required.
- Railway remains intentionally unverified until the resulting code HEAD is ready for the final external deployment gate.


## 2026-09-19 — Phase 13 Code Audit: Multi-Asset User-Facing Contract Cleanup
- Re-audited the Telegram user-facing surface for stale product terminology after confirming the canonical product scope is multi-asset.
- Replaced legacy Forex/AI branding in the Telegram home/start/back surfaces with the multi-asset trading-intelligence product name.
- Renamed the deterministic report-explanation feature from AI Coach to Analysis Coach in user-facing Telegram text; the underlying coach remains deterministic and report-based.
- Rechecked repository-wide markers for TODO/FIXME, unsafe dynamic execution, insecure HTTP verification bypasses, provider capability boundaries, and multi-asset risk metadata. No additional concrete defect was identified in those scanned surfaces.


## 2026-09-19 — Opportunity ranking and heatmap foundation
- Added explainable, risk-aware opportunity ranking and heatmap output.
- Integrated ranking into the multi-asset Telegram scanner.
- Added focused regression coverage.

## 2026-09-19 — Portfolio and heavy research capability expansion
- Added the multi-asset portfolio engine for exposure, concentration, risk, drawdown, correlation, and deterministic stress analysis.
- Added PC Worker workload contracts/executors for correlation matrices, portfolio stress, sensitivity scenarios, and counterfactual batches.
- Added focused regression coverage.

## 2026-09-19 — New Master Prompt capability roadmap begins
Historical Phases 1–13 are not treated as the end of product development.
Added CAPABILITY_MATRIX.md to distinguish historical verified capabilities from capabilities required by the new Master Engineering Prompt.
Added TASK-129: statistical analysis, scenario classification, counterfactual analysis, signal decay, crisis-mode state, and decision gating.
Railway remains deferred until required capabilities and final regression/security verification are complete.

## 2026-09-19 — Paper, shadow and replay foundation
- Added isolated paper trading and PnL ledger.
- Added shadow decision comparison without coupling to live execution.
- Added worker-owned market replay producing traceable historical decision output.
- Added focused regression coverage.


## 2026-09-19 — Time Machine foundation
- Added deterministic historical Time Machine orchestration over candle prefixes.
- Added traceable counterfactual evaluation per replay step.
- Registered `time_machine` as a PC Worker-owned heavy workload.
- Added focused deterministic and counterfactual regression coverage.
- Exact-head CI verification remains pending; no production verification is claimed.


## 2026-09-19 — Strategy Intelligence foundation
- Added canonical strategy lifecycle registry with strategy DNA, lineage, observations, versioning, pause/retirement, and audit-friendly snapshots.
- Added sample-aware champion/challenger comparison and promotion contract.
- Added PC Worker-owned strategy evaluation workload for heavier batches.
- Added focused lifecycle and worker regression tests.
- Exact-head CI verification remains pending; no production verification is claimed.


## 2026-09-19 — Strategy / Research Expansion
- TASK-135 extended strategy intelligence with weakness detection, explicit DNA adaptation, continuous evaluation, rollback, and audit events.
- TASK-136 added deterministic robustness matrix analysis and temporal leakage detection, routed as a PC Worker workload.
- Current exact-head CI verification remains pending; Railway remains a later external gate.


## 2026-09-19 — TASK-137 Macro / News Risk Expansion
- Added real NewsAPI and FRED adapters with explicit external-dependency diagnostics.
- Added macro event proximity assessment and integrated NORMAL/ELEVATED/CRISIS risk into the full analysis and decision boundary.
- Added regression tests for providers, macro assessment, and full-pipeline gating.
- Exact-head CI verification remains pending; no production verification is claimed for the new commits.


## 2026-09-19 — TASK-138 Advanced Research Validation
- Added deterministic out-of-sample and rolling walk-forward research validation.
- Added train/test divergence and OOS stability diagnostics to expose overfitting risk without claiming statistical certainty.
- Added temporal leakage checks and routed the heavy research workload to PC Worker.
- Added focused regression and worker contract coverage.
- Exact-head CI and production verification remain pending.


## 2026-09-19 — TASK-139 Research-Gated Strategy Lifecycle
- Connected OOS/walk-forward research evidence to strategy lifecycle decisions.
- Added admissible validation evidence with OOS stability, robustness, leakage and overfitting gates.
- Champion/challenger promotion now requires research validation evidence for both sides.
- Updated Worker strategy evaluation and regression tests.


## 2026-09-19 — TASK-140
### Research-Gated Strategy Adaptation
- Added proposal-first strategy DNA adaptation.
- Added validation-gated application with OOS/stability/robustness requirements.
- Added stale-proposal protection and validation metadata in audit events.
- Preserved rollback and lifecycle auditability.
- Added regression coverage.
- CI verification pending at exact head.


## 2026-09-19 — TASK-141 Strategy Validation Identity + Research Integration
- Bound strategy validation evidence to the exact strategy version and canonical DNA fingerprint.
- Added fail-closed rejection for stale validation evidence during attachment and champion/challenger comparison.
- Adaptation validation now targets the proposal's base version/DNA and invalidates prior evidence after a DNA change.
- PC Worker strategy evaluation can derive validation evidence directly from OOS/walk-forward research input, including overfitting and optional temporal-leakage diagnostics.
- Added focused regression coverage for research-backed validation and stale identity rejection.
- Exact-head CI verification remains pending.


## 2026-09-19 — TASK-142 Continuous Evaluation History
- Added immutable strategy evaluation snapshots with version and validation-readiness state.
- Continuous evaluation can ingest current validation evidence and records an auditable history per strategy.
- Stale version/DNA evidence is excluded from current validation state.
- Added focused regression coverage.

## 2026-09-19 — TASK-142 CI Repair
- Fixed StrategyRecord construction so validation-aware evaluation history is always initialized.
- The previous HEAD failed 8 tests with AttributeError; this was a direct regression from TASK-142 and is now corrected.

## 2026-09-19 — TASK-143 Robustness-Gated Research Validation
- Research-backed strategy validation now derives `robust` from the existing RobustnessEngine rather than trusting caller-provided state.
- Added regression coverage for automatic robustness gating.


## 2026-09-19 — TASK-144
- Fixed CI research fixtures by using a stable geometric-return price series; production overfitting gates remain fail-closed.
- Added validation-gated CHALLENGER lifecycle transition.
- Added automatic retirement for persistent negative expectancy with elevated drawdown after sufficient sample.
- Persisted OOS, overfitting, and robustness diagnostics in strategy validation evidence.
- Added focused regression coverage.


## 2026-09-19 — TASK-146 Portfolio Risk / Shadow Integration
- Added equity-aware gross-exposure enforcement to PortfolioRiskGuard.
- Integrated optional portfolio candidate checks into the analysis/decision boundary with explicit NO_TRADE fail-closed behavior.
- Extended AnalysisResult and AnalysisReport with portfolio risk status/flags.
- Added ShadowComparisonLedger for deterministic paper/reference comparison history and agreement-rate reporting.
- Added focused regression coverage.
- Exact-head CI verification remains pending; no Railway or production verification is claimed.


## 2026-09-19 — TASK-147 Alert / Tracker Hardening
- Made report alert eligibility aware of portfolio risk blocks.
- Suppressed AlertEngine emissions for portfolio-blocked candidates.
- Added Telegram display of portfolio risk block/flags.
- Added tracker lifecycle event history with backward-compatible persistence.
- Added regression coverage.
- Exact-head CI verification pending; no Railway or production verification claimed.


## 2026-09-19 — TASK-147 CI repair and closure checkpoint
- The exact-head CI run for `5dcddbc448842b78ff9482baf12b7cd0753a27e4` exposed a real syntax error in `tests/test_tracker_contract.py`: a literal escaped newline was inserted as source text.
- Corrected only the malformed test source in `151ea57b8e050ebc638074f46e31d5c01a5e9430`; no production gate was weakened.
- Re-ran the full seven-workflow required set on the corrected HEAD; all seven completed successfully.
- The expanded roadmap is now at an exact-head CI-verified frontier. Railway remains an external verification dependency.


## 2026-09-19 — Telegram market availability and signal failure messaging
- Added explicit weekend market-closure classification before candle availability checks.
- Replaced the generic `/signal` failure response with user-facing explanations for closed markets, stale market data, provider unavailability, unsupported symbols, and timeouts.
- Preserved fail-closed behavior: stale or unavailable data never produces a synthetic signal.
- Added regression coverage for weekend closure when no candles are available.
- Exact-head CI verification remains pending.


## 2026-09-20 — Profile execution completion
- Added independent per-style decision/risk summaries to profile-aware analysis reports before the combined decision.
- Extended immutable profile execution context with optional user scope, experiment ID, requested capabilities, and snapshot identity/version validation.
- Added canonical Worker payload construction and propagated profile context through backtest, replay, Time Machine, and research workloads.
- Added regression coverage for style decomposition and historical execution metadata.

## 2026-09-21 — TASK-151 Outbound PC Worker Pull Transport
- PR #49 was merged to `main` as `a988e293ec93fc267373d3303ed2832cc56542e1`.
- Railway now owns the durable worker queue and exposes authenticated claim/renew/result/health operations on the existing HTTPS service.
- Windows PC Worker pull mode executes heavy jobs locally and keeps claim leases alive during execution.
- No public PC endpoint, router exposure, Tailscale Funnel, or Cloudflare Tunnel is required for the canonical home-PC transport.
- All seven required workflows were green on the PR head before merge.
- Post-merge exact-head CI and live pull/recovery verification remain pending.

## 2026-09-21 — Phase 14–20 Exact-Head Closure
- Synchronized engineering state after the full Phase 14–20 capability audit.
- Confirmed all eight required GitHub Actions workflows succeeded on exact HEAD `803f9e13a38e8bb424e957d07f91e9682c7629f6`.
- Marked the implemented Phase 14–20 capability groups current-head verified: advanced intelligence, signal state/decision gates, portfolio intelligence, research/robustness, strategy lifecycle, opportunity/heatmap, paper/shadow/replay/Time Machine, plus associated macro/news and alert/tracker boundaries.
- Preserved the explicit economic-calendar provider limitation and the separate Railway production gate.
