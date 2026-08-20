class ApplicationError(Exception):
    """
    Base application exception.
    """
    pass


class ConfigurationError(ApplicationError):
    """
    Configuration related errors.
    """
    pass


class ServiceInitializationError(ApplicationError):
    """
    Service startup errors.
    """
    pass
