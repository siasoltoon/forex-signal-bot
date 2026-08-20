from core.errors import ApplicationError


def test_application_error():

    error = ApplicationError(
        "test error"
    )

    assert error.message == "test error"
