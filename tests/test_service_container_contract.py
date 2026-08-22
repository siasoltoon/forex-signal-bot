import pytest

from core.container import ServiceContainer


class Dependency:
    pass


def test_register_and_get_return_the_same_dependency_instance():
    container = ServiceContainer()
    dependency = Dependency()

    container.register("dependency", dependency)

    assert container.get("dependency") is dependency


def test_has_reports_registration_state():
    container = ServiceContainer()
    dependency = Dependency()

    assert container.has("dependency") is False

    container.register("dependency", dependency)

    assert container.has("dependency") is True


def test_register_replaces_existing_binding_deterministically():
    container = ServiceContainer()
    first = Dependency()
    second = Dependency()

    container.register("dependency", first)
    container.register("dependency", second)

    assert container.get("dependency") is second


def test_get_missing_dependency_raises_key_error():
    container = ServiceContainer()

    with pytest.raises(KeyError, match="Service 'missing' not found"):
        container.get("missing")
