"""Configuration classes for the testing model."""

from virtual_ecosystem.core.configuration import DisturbanceConfigurationRoot


class DisturbanceTestingConfiguration(DisturbanceConfigurationRoot):
    """Root configuration class for the testing model."""

    # In this case, a default timing information is provided.If it were not, the timing
    # information would be required to be provided in the configuration file.
    run_at: int | tuple[int, ...] = 0
