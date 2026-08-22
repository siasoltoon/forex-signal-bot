from core.errors import handle_exception
from core.exceptions import (
    ApplicationError,
    ConfigurationError,
    ServiceInitializationError,
)


def test_application_error_is_canonical_and_preserves_details():
    error = ApplicationError("boom", {"source": "test"})

    assert str(error) == "boom"
    assert error.message == "boom"
    assert error.details == {"source": "test"}


def test_specialized_errors_share_the_canonical_application_error():
    assert issubclass(ConfigurationError, ApplicationError)
    assert issubclass(ServiceInitializationError, ApplicationError)
    assert ConfigurationError.__mro__[1] is ApplicationError
    assert ServiceInitializationError.__mro__[1] is ApplicationError


def test_errors_module_reexports_canonical_application_error():
    from core.exceptions import ApplicationError as canonical_error
    from core.errors import ApplicationError as handled_error

    assert handled_error is canonical_error


def test_handle_exception_accepts_application_error(monkeypatch):
    captured = []

    class Logger:
        def exception(self, message, error):
            captured.append((message, error))

    monkeypatch.setattr("core.errors.logger", Logger())
    error = ConfigurationError("invalid configuration")

    handle_exception(error)

    assert captured == [("Application error: %s", error)]
