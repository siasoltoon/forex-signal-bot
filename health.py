from __future__ import annotations

from datetime import datetime, timezone


def health_check() -> dict[str, str]:
    """
    Basic application health check.

    This function does not contact external services.
    """

    return {
        "status": "ok",
        "service": "forex-signal-bot",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }
