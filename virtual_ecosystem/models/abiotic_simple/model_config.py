"""Abiotic simple model configuration."""

from virtual_ecosystem.core.configuration import Configuration, ModelConfigurationRoot


class AbioticSharedConstants(Configuration):
    """Shared abiotic constants.

    This is a pydantic basemodel to hold constants shared between the `abiotic` and
    `abiotic_simple` models.
    """

    leaf_emissivity: float = 0.98
    """Leaf emissivity, unitless.
    
    Leaf emissivity is a measure of how efficiently a leaf emits thermal radiation
    compared to a perfect blackbody, typically ranging from 0.95 to 0.99. Value for
    tropical vegetation is taken from :cite:t:`ma_an_2019`.
    """

    soil_emissivity: float = 0.95
    """Soil emissivity, dimensionless.
    
    Soil emissivity is a measure of how efficiently the soil surface emits thermal
    radiation compared to a perfect blackbody, with values typically ranging from 0.90
    to 0.98 depending on soil texture, moisture, and surface roughness. Value taken
    from :cite:t:`molders_plant_2005`."""


class AbioticSimpleConstants(AbioticSharedConstants):
    """Dataclass to store all constants for the `abiotic_simple` model."""

    initial_net_radiation: float = 10.0
    """Initial value for net radiation per layer, W m-2.
    
    TODO This is currently set to an arbitrary value."""


class AbioticSimpleBounds(Configuration):
    """Upper and lower bounds for abiotic variables.

    When a values falls outside these bounds, it is set to the bound value.
    NOTE that this approach does not conserve energy and matter in the system.
    This will be implemented at a later stage.
    """

    air_temperature: tuple[float, float, float] = (-20.0, 80.0, -1.27)
    """Bounds and gradient for air temperature, [C].

    Gradient for linear regression to calculate air temperature as a function of
    leaf area index from :cite:t:`hardwick_relationship_2015`.
    """

    relative_humidity: tuple[float, float, float] = (0.0, 100.0, 5.4)
    """Bounds and gradient for relative humidity, dimensionless.

    Gradient for linear regression to calculate relative humidity as a function of
    leaf area index from :cite:t:`hardwick_relationship_2015`.
    """

    vapour_pressure_deficit: tuple[float, float, float] = (0.0, 10.0, -252.24)
    """Bounds and gradient for vapour pressure deficit, [kPa].
    
    Gradient for linear regression to calculate vapour pressure deficit as a function of
    leaf area index from :cite:t:`hardwick_relationship_2015`.
    """

    wind_speed: tuple[float, float, float] = (0.001, 100.0, -0.1)
    """Bounds and gradient for wind speed, [m s-1].
    
    Gradient for linear regression to calculate wind speed as a function of
    leaf area index. The value is choses arbitrarily and needs to be replaced with
    observations.
    """

    soil_temperature: tuple[float, float] = (-10.0, 50.0)
    """Bounds for soil temperature, [C]."""


class AbioticSimpleConfiguration(ModelConfigurationRoot):
    """Root configuration class for the abiotic simple model."""

    constants: AbioticSimpleConstants = AbioticSimpleConstants()
    bounds: AbioticSimpleBounds = AbioticSimpleBounds()
