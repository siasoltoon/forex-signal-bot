from app import create_app as root_create_app
from core.application import create_app as core_create_app


def test_root_factory_is_the_canonical_core_factory():
    assert root_create_app is core_create_app


def test_root_factory_registers_the_same_application_services():
    root_app = root_create_app()
    core_app = core_create_app()

    assert root_app.services.services.keys() == core_app.services.services.keys()
