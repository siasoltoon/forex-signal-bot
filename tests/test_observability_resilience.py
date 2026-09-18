from observability.contracts import LogLevel
from observability.health import HealthRegistry, HealthResult, HealthState
from observability.logging import StructuredLogger
from observability.metrics import MetricsRegistry
from observability.decision_trace import DecisionTrace
from resilience.policy import CircuitBreaker, CircuitState, RetryPolicy


def test_structured_logger_emits_event() -> None:
    lines: list[str] = []
    event = StructuredLogger(lines.append).log(LogLevel.INFO, "test", "ok", job_id="j1")
    assert event.job_id == "j1"
    assert '"level": "INFO"' in lines[0]


def test_metrics_increment_and_snapshot() -> None:
    registry = MetricsRegistry()
    registry.increment("jobs", labels={"state": "success"})
    registry.increment("jobs", labels={"state": "success"})
    assert registry.snapshot()[0].value == 2


def test_health_check_failure_is_isolated() -> None:
    registry = HealthRegistry()
    registry.register("ok", lambda: HealthResult("ok", HealthState.HEALTHY))
    registry.register("bad", lambda: (_ for _ in ()).throw(RuntimeError("down")))
    results = registry.run()
    assert [r.state for r in results] == [HealthState.HEALTHY, HealthState.UNHEALTHY]


def test_circuit_breaker_opens() -> None:
    breaker = CircuitBreaker(failure_threshold=2)
    breaker.failure()
    assert breaker.allow()
    breaker.failure()
    assert breaker.state is CircuitState.OPEN
    assert not breaker.allow()


def test_retry_policy_is_bounded() -> None:
    policy = RetryPolicy(base_delay_seconds=1, max_delay_seconds=3)
    assert policy.delay(0) == 1
    assert policy.delay(5) == 3


def test_decision_trace_preserves_order() -> None:
    trace = DecisionTrace("t1")
    trace.add("data", "ok", quality=1)
    trace.add("decision", "wait")
    assert [s.name for s in trace.steps()] == ["data", "decision"]
