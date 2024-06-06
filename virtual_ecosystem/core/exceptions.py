"""The ``core.exceptions`` module stores custom exceptions that are used within the core
module or used across multiple modules.
"""  # noqa: D205


class ConfigurationError(Exception):
    """Custom exception class for configuration failures."""


class InitialisationError(Exception):
    """Custom exception class for model initialisation failures."""
