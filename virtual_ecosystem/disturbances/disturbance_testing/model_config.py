"""Configuration classes for the testing model."""

from virtual_ecosystem.core.configuration import DisturbanceConfigurationRoot


class DisturbanceTestingConfiguration(DisturbanceConfigurationRoot):
    """Root configuration class for the testing model."""

    run_at: int | tuple[int, ...] = 0
