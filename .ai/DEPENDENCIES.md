# Dependency Map

Keep this map focused on architectural boundaries rather than listing every import.

## Core lifecycle

```text
Application
  → ServiceManager
  → BaseService
  → Concrete Services
```

## Market data

```text
MarketDataEngine
  → ProviderManager
  → Provider implementations
  → Data models / validation
  → Quality / freshness metadata
```

## Change impact rule

Before modifying a boundary, search for its callers and implementations. For large modules, trace only the relevant symbols and call paths needed for the change.
