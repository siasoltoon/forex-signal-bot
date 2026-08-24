from services.telegram.i18n import t
from services.telegram.scanner import ScanResult, format_scan


def test_language_translation_changes_main_text():
    assert "Settings" in t("en", "settings")
    assert "تنظیمات" in t("fa", "settings")


def test_scanner_hides_internal_exception_name():
    result = ScanResult("EURUSD", "NO_TRADE", 0.0, 0.0, None, "UNKNOWN", "unknown", None, "ValueError")
    text = format_scan([result], "M15", "en")
    assert "ValueError" not in text
    assert "Valid data or analysis is unavailable" in text


def test_scanner_localizes_success_output():
    result = ScanResult("EURUSD", "BUY", .82, 1.2, 80, "A", "bullish", 2.1)
    fa = format_scan([result], "M15", "fa")
    en = format_scan([result], "M15", "en")
    assert "اطمینان" in fa and "confidence" in en
