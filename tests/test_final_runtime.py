from core.final_runtime import DependencyCheck, FinalRuntimeGate, RuntimeStatus
from core.production_policy import DecisionMode, ProductionPolicy


def test_runtime_gate_is_ready_when_required_dependencies_are_healthy():
    gate = FinalRuntimeGate()
    gate.register("market", lambda: DependencyCheck("market", True))
    gate.register("risk", lambda: DependencyCheck("risk", True))
    readiness = gate.evaluate()
    assert readiness.status is RuntimeStatus.READY
    assert readiness.ready


def test_runtime_gate_blocks_on_required_dependency_failure():
    gate = FinalRuntimeGate()
    gate.register("market", lambda: DependencyCheck("market", False, True, "stale"))
    readiness = gate.evaluate()
    assert readiness.status is RuntimeStatus.BLOCKED
    assert not readiness.ready
    assert "market: stale" in readiness.reasons


def test_optional_dependency_failure_is_degraded():
    gate = FinalRuntimeGate()
    gate.register("market", lambda: DependencyCheck("market", True))
    gate.register("news", lambda: DependencyCheck("news", False, False, "provider unavailable"))
    readiness = gate.evaluate()
    assert readiness.status is RuntimeStatus.DEGRADED


def test_live_submission_is_fail_closed_by_default():
    policy = ProductionPolicy()
    assert policy.mode is DecisionMode.PAPER
    assert not policy.can_submit(
        runtime_ready=True,
        market_fresh=True,
        risk_valid=True,
        scenario_valid=True,
        stop_loss_valid=True,
        signal_age_seconds=1,
    )


def test_live_submission_requires_all_guards():
    policy = ProductionPolicy(mode=DecisionMode.LIVE, allow_order_submission=True)
    assert policy.can_submit(True, True, True, True, True, 1)
    assert not policy.can_submit(True, False, True, True, True, 1)
    assert not policy.can_submit(True, True, False, True, True, 1)
    assert not policy.can_submit(True, True, True, False, True, 1)
    assert not policy.can_submit(True, True, True, True, False, 1)
    assert not policy.can_submit(True, True, True, True, True, 61)
