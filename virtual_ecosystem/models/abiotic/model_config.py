"""The ``models.abiotic.constants`` module contains a set of dataclasses which contain
parameters required by the broader
:mod:`~virtual_ecosystem.models.abiotic.abiotic_model` model.
These parameters are constants in that they should not be changed during a particular
simulation.
"""  # noqa: D205

from virtual_ecosystem.core.configuration import ModelConfigurationRoot
from virtual_ecosystem.models.abiotic_simple.model_config import (
    AbioticSharedConstants,
    AbioticSimpleBounds,
    AbioticSimpleConstants,
)


class AbioticConstants(AbioticSharedConstants):
    """Dataclass to store all constants for the `abiotic` model."""

    leaf_albedo: float = 0.15
    """Leaf albedo, unitless.
    
    Leaf albedo is the fraction of incoming solar radiation that a leaf reflects,
    typically ranging from 0.12 to 0.18 in tropical forests due to their dark, broadleaf
    surfaces. Value here is taken from :cite:t:`su_aerodynamic_2021`.
    """

    bulk_density_soil: float = 1.175 * 1000
    """Bulk density of soil, [kg m-3].
    
    Bulk density describes the mass of dry soil per unit volume, including both the
    solid soil particles and the pore spaces between them. Value for average rainforest
    soil is taken from :cite:t:`gupta_soilksatdb_2021`.
    """

    wind_reference_height: float = 10.0
    """Reference height for wind speed above the canopy, [m].

    The reference height for horizontal wind is typically 10m above ground compared to
    2m for other atmospheric variables such as temperature and relative humidity. We
    assume here that the reference height is above the canopy, please check the input
    data carefully and be aware of limitations."""

    latent_heat_vap_equ_factors: tuple[float, float] = 1.91846e6, 33.91
    """Factors in calculation of latent heat of vapourisation.

    Implementation after :cite:t:`maclean_microclimc_2021`, value is taken from
    :cite:t:`henderson-sellers_new_1984`.
    """

    zero_plane_scaling_parameter: float = 7.5
    """Control parameter for scaling zero displacement to height, dimensionless.

    Implementation after :cite:t:`maclean_microclimc_2021`, value is taken from
    :cite:t:`raupach_simplified_1994`."""

    substrate_surface_roughness_length: float = 0.003
    """Substrate-surface roughness length, m.

    The substrate-surface roughness length is the "baseline roughness" of the ground
    itself before adding vegetation on top. Implementation and value from
    :cite:t:`maclean_microclimc_2021`."""

    roughness_element_drag_coefficient: float = 0.3
    """Roughness-element drag coefficient, dimensionless.

    The roughness-element drag coefficient refers to the dimensionless coefficient
    used to quantify the drag force exerted by individual roughness elements (such as
    buildings, trees, or surface irregularities) on airflow, influencing the overall
    aerodynamic characteristics of a surface within the atmospheric boundary layer.
    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    roughness_sublayer_depth_parameter: float = 0.193
    """Parameter characterizes the roughness sublayer depth.

    The roughness sublayer depth refers to the layer near the surface where the
    effects of surface roughness significantly influence airflow, turbulence, momentum
    transfer, typically extending up to about 10% of the height of the roughness
    elements or features on the surface. This layer is characterized by intense
    turbulence and rapid velocity changes due to surface irregularities.
    Implementation and value taken from :cite:p:`maclean_microclimc_2021`."""

    max_ratio_wind_to_friction_velocity: float = 0.3
    """Maximum ratio of wind velocity to friction velocity, dimensionless.

    The maximum ratio of wind velocity to friction velocity refers to the highest
    observed or theoretical value of the ratio between the wind speed at a given height
    and the surface friction velocity (u*), indicating the efficiency of momentum
    transfer from the atmosphere to the surface. Implementation and value from
    :cite:t:`maclean_microclimc_2021`."""

    drag_coefficient: float = 0.2
    """Drag coefficient, dimensionless.

    The drag coefficient is a dimensionless quantity that characterizes the drag or
    resistance experienced by an object moving through a fluid (here the atmosphere) and
    is defined as the ratio of the drag force on the object to the dynamic pressure of
    the fluid flow and the reference area of the object.
    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    min_windspeed_below_canopy: float = 0.1
    """Minimum wind speed below the canopy or in absence of vegetation, [m s-1]."""

    min_roughness_length: float = 0.01
    """Minimum roughness length, [m].

    The minimum roughness length represents the lowest height at which the surface
    roughness significantly affects the wind flow over a particular terrain or
    surface. Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    light_extinction_coefficient: float = 0.01
    """Light extinction coefficient for canopy, unitless.
    
    The light extinction coefficient for a canopy quantifies how quickly light
    diminishes as it passes through vegetation, reflecting the canopy's ability to
    absorb or scatter incoming radiation. This value is only used in the model setup and
    later derived in the plant model."""

    soil_thermal_conductivity: float = 1.206
    """Soil thermal conductivity, [W m-1 K-1].

    Soil thermal conductivity is a measure of the soil's ability to conduct heat,
    influenced by factors such as moisture content, texture, and density. Value is
    taken from :cite:t:`rasimeng_characterization_2020`.
    """

    specific_heat_capacity_soil: float = 881
    """Specific heat capacity of soil, [J kg-1 K-1].
   
    Specific heat capacity of soil is the amount of heat required to raise the
    temperature of a unit mass of soil by one degree Celsius (or Kelvin), and depends on
    soil composition, moisture content, and organic matter. Value taken from
    :cite:t:`molders_plant_2005`.
    """

    surface_albedo: float = 0.125
    """Mean surface albedo of a tropical rainforest in South East Asia, dimensionless.

    The value is takes from a study that compares changes in surface albedo before and
    after deforestation in South East Asia :cite:p:`wilson_role_2020`."""

    saturated_pressure_slope_parameters: tuple[float, float, float, float] = (
        4098.0,
        0.6108,
        17.27,
        237.3,
    )
    """List of parameters to calculate the slope of saturated vapour pressure curve."""

    dry_air_factor: float = 0.378
    """Dry air factor, dimensionless.

    This term accounts for the proportion of dry air when computing the partitioning
    of total air pressure. It is the complement of the
    `molecular_weight_ratio_water_to_dry_air` in core.constants."""

    initial_flux_value: float = 0.001
    """Initial non-zero fill value for energy fluxes, [W m-2]."""

    aerodynamic_resistance_canopy_default: float = 12.5
    """Default aerodynamic resistance of the canopy, [s m-1]."""


class AbioticConfiguration(ModelConfigurationRoot):
    """The abiotic model configuration."""

    constants: AbioticConstants = AbioticConstants()
    """Constants for the abiotic model"""

    bounds: AbioticSimpleBounds = AbioticSimpleBounds()
    """Bounds for abiotic variables."""

    simple_constants: AbioticSimpleConstants = AbioticSimpleConstants()
    """Constants used for the simple abiotic model, used to set up initial
    conditions."""
