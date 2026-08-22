# Project Map

This file is the navigation index for AI-assisted maintenance of the repository.

## Rules for working with large files

1. Do not rewrite an entire large file when a targeted edit is sufficient.
2. Search for the relevant symbol, class, function, or error first.
3. Read only the smallest useful source range plus its callers/dependencies.
4. Prefer minimal patches that preserve unrelated code.
5. Never edit a file when the retrieved content is incomplete or untrusted.
6. After a change, run the narrowest relevant tests first, then the broader suite.
7. Treat GitHub Actions as verification of the committed repository state, not as a patching mechanism.

## Repository navigation

### Core

- `core/application.py` — application lifecycle/orchestration entry point.
- `core/service.py` — `ServiceManager`; service registration, async startup/shutdown, health aggregation.
- `core/container.py` — dependency/container layer.
- `core/errors.py` — error handling utilities.
- `core/exceptions.py` — exception definitions.
- `core/logger.py` — logging setup.
- `core/shutdown.py` — shutdown coordination.

### Services

- `services/base.py` — `BaseService` lifecycle contract.
- `services/` — concrete application services.

### Data / Provider layer

- `data/` — market-data domain and provider-facing data structures.
- Provider and market-data components should be traced through their contracts before modifying consumers.

### Tests

- `tests/` — unit, contract, integration, and regression tests.
- Prefer existing tests before creating a new test file.

## Current architecture contracts

### BaseService lifecycle

`BaseService.start()` and `BaseService.stop()` are asynchronous contracts. Concrete services must implement them as async methods. `health()` is synchronous unless a concrete service contract explicitly requires otherwise.

### ServiceManager lifecycle

`ServiceManager.start_all()` starts services in registration order and continues after a service failure while routing the exception through `handle_exception()`.

`ServiceManager.stop_all()` stops services in reverse registration order and continues after a service failure while routing the exception through `handle_exception()`.

`ServiceManager.health()` collects each service health result and returns `{status: error}` for a failing service after routing the exception through `handle_exception()`.

## Large-file hotspots

Keep this section updated when a file becomes difficult to safely retrieve or modify in one pass.

- Market-data and analysis engines: inspect by symbol/range rather than whole-file rewrites.
- Provider managers: inspect contract boundaries and delegation paths first.
- Signal/analysis engines: prefer targeted edits and staged refactors.

## Maintenance workflow

`Audit → Search symbol → Read focused ranges → Trace callers/dependencies → Minimal patch → Targeted tests → Full verification → Commit`
