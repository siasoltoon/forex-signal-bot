# Architecture Notes

## Current verified core boundary

```text
Application
  ↓
ServiceManager
  ↓
BaseService contract
  ↓
Concrete services
```

## Data boundary

```text
Provider
  ↓
ProviderManager
  ↓
Market Data
  ↓
Quality / Freshness / Staleness
  ↓
MarketDataEngine
```

## Editing principle

Changes should be made at the narrowest architectural boundary that owns the behavior. Large modules should be split by responsibility when a targeted edit is no longer safe or maintainable, not merely to reduce line count.
