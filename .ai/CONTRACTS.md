# Contract Index

This file records stable contracts that have been intentionally established during architecture hardening.

## Core

### BaseService

- `async start() -> None`
- `async stop() -> None`
- `health() -> dict[str, str]`

### ServiceManager

- Registers services by stable service name.
- Starts in registration order.
- Stops in reverse registration order.
- Continues lifecycle processing after an individual service error.
- Routes lifecycle errors through `handle_exception()`.
- Aggregates health results and reports failing services with `{"status": "error"}`.

## Data / Provider

Provider and market-data contracts are documented here as they are verified. Do not mark a contract verified solely because a workflow completed successfully; the relevant test must actually execute and pass.
