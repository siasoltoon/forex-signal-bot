from core.production_activation_report import build_activation_report


def test_activation_is_not_ready_when_integrations_are_missing():
    report = build_activation_report({"market_data": True, "telegram": True})
    assert not report.ready
    assert "database" in report.missing
    assert "worker" in report.missing
    assert "news_macro" in report.missing


def test_activation_is_ready_only_when_all_real_integrations_report_healthy():
    report = build_activation_report({
        "market_data": True,
        "telegram": True,
        "database": True,
        "worker": True,
        "news_macro": True,
    })
    assert report.ready
    assert report.missing == ()
