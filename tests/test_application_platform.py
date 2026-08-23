from application.idempotency import IdempotencyGuard
from application.rate_limit import RateLimiter
from i18n.catalog import ENGLISH, PERSIAN
from notifications.contracts import AlertSeverity, Notification, NotificationChannel
from notifications.dedup import NotificationDeduplicator
from security.auth import Authorization, Principal, Role


def test_idempotency_rejects_duplicate() -> None:
    guard = IdempotencyGuard()
    assert guard.accept("x") is True
    assert guard.accept("x") is False


def test_rate_limit_rejects_after_limit() -> None:
    limiter = RateLimiter(2, 60)
    assert limiter.allow("u") is True
    assert limiter.allow("u") is True
    assert limiter.allow("u") is False


def test_authorization() -> None:
    Authorization().require(Principal("u", Role.ADMIN), Role.ADMIN)


def test_localization() -> None:
    assert PERSIAN.get("analysis.no_trade") == "عدم معامله"
    assert ENGLISH.get("analysis.no_trade") == "NO TRADE"


def test_notification_deduplication() -> None:
    notification = Notification("n", "u", NotificationChannel.TELEGRAM, AlertSeverity.IMPORTANT, "x", "same")
    dedup = NotificationDeduplicator()
    assert dedup.should_send(notification) is True
    assert dedup.should_send(notification) is False
