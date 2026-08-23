from application.session import AnalysisSession
from telegram_app.commands import AnalysisHandler, HelpHandler, StartHandler
from telegram_app.contracts import CommandRequest, UserContext
from telegram_app.keyboards import analysis_menu, main_menu
from telegram_app.report import render_analysis_report
from telegram_app.router import TelegramRouter


def test_router_dispatches_commands() -> None:
    router = TelegramRouter()
    router.register_command("start", StartHandler())
    response = router.dispatch_command(CommandRequest("start"), UserContext("u1"))
    assert "تحلیل" in response.text


def test_analysis_handler_creates_user_session() -> None:
    sessions: dict[str, AnalysisSession] = {}
    handler = AnalysisHandler(sessions)
    response = handler.handle(CommandRequest("analysis"), UserContext("u1"))
    assert "تنظیم تحلیل" in response.text
    assert "u1" in sessions


def test_localized_menus_and_report() -> None:
    assert "Analysis" in main_menu("en").text
    assert "Analysis setup" in analysis_menu("en").text
    report = render_analysis_report({"decision": "WAIT", "confidence": 70}, "fa")
    assert "تصمیم" in report


def test_help_command() -> None:
    response = HelpHandler().handle(CommandRequest("help"), UserContext("u1", language="en"))
    assert "/analysis" in response.text
