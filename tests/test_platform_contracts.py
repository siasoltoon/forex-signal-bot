from ai.contracts import ModelPrediction, ModelRelease, ModelRole
from backtesting.contracts import BacktestConfig, EvaluationMode
from config.contracts import FeatureFlags, RuntimeConfig
from events.contracts import DomainEvent, EventEnvelope
from i18n.contracts import LocalizedText, SUPPORTED_LOCALES
from journal.contracts import CoachInsight, JournalEntry
from live.contracts import LiveSignal, SignalState, SignalUpdate
from monitoring.contracts import ComponentHealth, ComponentState, Metric, SystemSnapshot
from notifications.contracts import Alert, AlertSeverity, AlertType
from portfolio.contracts import PortfolioSnapshot, Position
from risk.contracts import PositionSizingInput, RiskDecision, RiskLimits
from scanner.contracts import Opportunity, ScanRequest, ScanResult
from security.contracts import AuthContext, Permission, SecurityAuditEvent


def test_platform_contracts_are_constructible() -> None:
    assert len(SUPPORTED_LOCALES) >= 2
    assert LocalizedText("x", {"fa": "سلام", "en": "hello"}).resolve("fa") == "سلام"
    assert ModelPrediction("m", ModelRole.JUDGE, "WAIT").role is ModelRole.JUDGE
    assert ModelRelease("m", "1", True, False).champion
    assert BacktestConfig("EUR_USD", "1H", "2026-01-01", "2026-01-02").mode is EvaluationMode.BACKTEST
    assert FeatureFlags().scanner is False
    assert RuntimeConfig("test").default_language == "fa"
    assert EventEnvelope(DomainEvent("e", "x", "a", "now", {}), "c").correlation_id == "c"
    assert CoachInsight("timing", "late", 3, 0.8).evidence_count == 3
    assert JournalEntry("j", "EUR_USD", "BUY", "setup", 1.1, 0.01, "trend", "reason").symbol == "EUR_USD"
    live = LiveSignal("s", "EUR_USD", "BUY", SignalState.ACTIVE, 0.8)
    assert SignalUpdate("s", SignalState.ACTIVE, SignalState.WEAKENING, "momentum").signal_id == live.signal_id
    assert SystemSnapshot((ComponentHealth("api", ComponentState.HEALTHY),), (Metric("cpu", 1, "%"),)).health[0].state is ComponentState.HEALTHY
    assert Alert("a", "u", AlertType.RISK, AlertSeverity.IMPORTANT, "risk", "message", "risk:u", "now").severity is AlertSeverity.IMPORTANT
    assert PortfolioSnapshot(1000, (Position("EUR_USD", "BUY", 1, 1.1),)).equity == 1000
    assert RiskLimits().per_trade_percent == 1.0
    assert PositionSizingInput(1000, 1, 1.1, 1.0).account_size == 1000
    assert RiskDecision(True, 1, 100).allowed
    scan = ScanResult(1, 1, (Opportunity("EUR_USD", "1H", "BUY", 0.8, 0.7),))
    assert ScanRequest("forex", ("EUR_USD",), ("1H",)).max_results == 20
    assert scan.opportunities[0].symbol == "EUR_USD"
    auth = AuthContext("u", permissions=(Permission("analysis", "read"),))
    assert auth.can("analysis", "read")
    assert SecurityAuditEvent("e", "u", "read", "analysis", "allowed", "now").outcome == "allowed"
