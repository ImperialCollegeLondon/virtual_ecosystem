"""Configuration classes for the fertiliser addition disturbance."""

from pydantic import Field

from virtual_ecosystem.core.configuration import (
    Configuration,
    DisturbanceConfigurationRoot,
)


class AddFertiliserConstants(Configuration):
    """Dataclass to store all constants for the fertiliser addition disturbance."""

    inorganic_nitrogen_addition: float = Field(default=0.0, ge=0.0)
    """Rate of inorganic nitrogen fertiliser addition [kg{N} m^-2]
    
    Fertiliser is added to the soil model at each timestep (that the disturbance is
    configured to run for). This means that the mass added should be the total added
    mass of fertiliser per simulation timestep.
    """

    nitrate_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    """Fraction of added inorganic nitrogen that is nitrate [unitless].
    
    The remainder is added to the soil as ammonium.
    """


class AddFertiliserConfiguration(DisturbanceConfigurationRoot):
    """Configuration class for the fertiliser addition disturbance."""

    constants: AddFertiliserConstants = AddFertiliserConstants()
    """Constants values for the fertiliser addition disturbance."""
