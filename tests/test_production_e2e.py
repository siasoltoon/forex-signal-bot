from core.production_e2e import REQUIRED_STAGES, validate_real_integration


def test_all_production_stages_are_declared():
    assert {
        "market_data", "analyzer_e2e", "backtest_strategy", "live_intelligence",
        "worker_queue", "ai_ml", "news_macro", "telegram_database",
        "failure_recovery", "load_stress",
    } <= set(REQUIRED_STAGES)


def test_gate_rejects_missing_real_data():
    result = validate_real_integration("market_data", {"healthy": True})
    assert not result.passed


def test_gate_rejects_synthetic_data():
    result = validate_real_integration(
        "ai_ml", {"healthy": True, "real_data": True, "synthetic_data": True}
    )
    assert not result.passed


def test_gate_accepts_explicit_real_healthy_integration():
    result = validate_real_integration(
        "telegram_database",
        {"healthy": True, "real_data": True, "synthetic_data": False},
    )
    assert result.passed
