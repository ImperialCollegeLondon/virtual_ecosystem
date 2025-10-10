"""Configuration classes for the testing model."""

from virtual_ecosystem.core.configuration import ModelConfig


class TestingConfig(ModelConfig):
    """Root configuration class for the testing model."""

    numeric_value: float = 1.0
    """A float config option"""
    string_value: str = "test"
    """A string config option"""
