# Project State

- Project: `siasoltoon/forex-signal-bot`
- Branch: `main`
- Current HEAD: `7e978faa986ed6088511c0aee3a1fa4510a02408`
- Product: **Multi-Asset Trading Intelligence Platform**
- Supported market families: Forex, Crypto, Stocks, Indices, Commodities
- Historical phase closures: Phases 1–11 retain their recorded closure evidence.
- Current operational state: **Phase 13 code audit VERIFIED; final Railway gate pending**.
- Current-head GitHub Actions: all seven required workflows completed successfully on the exact HEAD.
- Current external Railway status: still failing for `lavish-energy - forex-signal-bot`; this is deferred for final deployment verification and is not treated as proof of a code defect.
- Phase 12 remains `REVERIFICATION_REQUIRED` until Railway is synchronized to this HEAD and fresh health/recovery evidence exists.
- Phase 13 code/test/CI/cross-phase audit is verified at this exact HEAD; final production closure requires the external Railway gate.

## Current Audit Contract
A phase is current-HEAD verified only when implementation, focused regression tests, required CI checks, deployment evidence where applicable, and synchronized engineering documentation agree.

The audit:
- inspected the full relevant phase surface rather than only the original checklist;
- fixed concrete lifecycle, CI/security, and terminology issues together;
- added/updated focused regression coverage for corrected startup behavior;
- verified the resulting exact HEAD with the complete seven-workflow CI set;
- re-audited dependent boundaries;
- avoided speculative rewrites and unsupported features.

## Multi-Asset Contract
The repository is not Forex-only. Centralized symbol/asset metadata and market-specific semantics must remain intact. Unsupported provider/market combinations, unavailable conversion data, stale/future market data, and invalid risk inputs must fail closed.

## Architecture Constraints
The PC Worker is for heavy application processing. The dormant `ai/` package is not part of canonical production scoring. No local coding-agent/Ollama/model-orchestration architecture is part of the active worker path.

## New-chat continuation
Before repository changes, read:
1. `docs/engineering/PROJECT_STATE.md`
2. `docs/engineering/PHASE_STATE.md`
3. `docs/engineering/TASK_STATE.md`
4. `docs/engineering/TEST_STATE.md`
5. `docs/engineering/ARCHITECTURE_MAP.md`
6. `docs/engineering/DECISIONS.md`
7. `docs/engineering/CHANGELOG_ENGINEERING.md`

Then inspect the exact current `main` HEAD and current CI/deployment status.

## New Master Prompt Development Frontier — 2026-09-19
The historical Phase-13 code audit is not the end of feature development. The new Master Engineering Prompt expands the product contract and requires implementation of missing capabilities.
- Current development phase: Phase 14 — Advanced Intelligence Foundation.
- Current task: TASK-129.
- Capability Matrix: docs/engineering/CAPABILITY_MATRIX.md.
- New capabilities already added in TASK-129: statistical context, explicit scenarios, counterfactuals, signal decay, crisis mode, conflict gates.
- Railway is intentionally deferred until the expanded capability roadmap is implemented and verified.
- New-chat continuation: read CAPABILITY_MATRIX and RECOVERY_STATE in addition to the existing state files; continue from CURRENT_TASK and inspect only relevant code.


## Current Development Closure — 2026-09-19
- Current HEAD: `151ea57b8e050ebc638074f46e31d5c01a5e9430`.
- TASK-147 exact-head repair was completed: an invalid literal escape in `tests/test_tracker_contract.py` caused compile failure and was removed without weakening production behavior.
- All seven required GitHub Actions workflows are green on this exact HEAD: Test, Production Readiness, Production Activation Validation, Production Activation Gate, Production E2E Contract Gate, Security Audit, and Final Integration Gate.
- The expanded roadmap capabilities through TASK-147 are code/test verified at this frontier.
- Remaining production closure is external: synchronize Railway to this HEAD and obtain fresh live `/health` smoke plus controlled restart/recovery evidence. Do not treat older Railway evidence for commit `8bf2a77840b72add70b98cbf1a3b2187f85763f2` as verification of this HEAD.


## Current Exact-Head Verification — 2026-09-20
- Current main HEAD: `7ee70ad23a7b5c0008298e37f3286d1be4869853`.
- Current GitHub Actions verification: all eight production/code workflows are green on this exact HEAD.
- Full test suite: 951 passed.
- Profile execution work through TASK-149 is verified at current HEAD.
- Railway remains a separate external deployment gate; this code verification does not claim a fresh Railway deployment result.\n\n## Current Engineering Handoff — 2026-09-21 — PC Worker Pull Transport\n- Current main HEAD: `a988e293ec93fc267373d3303ed2832cc56542e1`.\n- PR #49 (Add outbound PC Worker pull transport) is merged into `main`.\n- The PR head `d5a9a0a88594019f838148621648b8e6ffa0f698` passed all seven required CI workflows before merge.\n- New canonical transport: Railway owns the durable queue; the Windows PC Worker pulls jobs over outbound HTTPS, renews fenced claim leases, and posts terminal results. No public PC endpoint/tunnel is required.\n- The existing localhost Worker HTTP server remains available for local diagnostics.\n- Current merged HEAD has no post-merge workflow run/status reported by the GitHub connector; therefore this handoff does not claim exact-merge-head CI verification.\n- Next action: verify CI on the resulting state-sync head, then perform controlled PC Worker pull integration validation against the deployed Railway service.\n