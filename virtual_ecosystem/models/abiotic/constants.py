"""The ``models.abiotic.constants`` module contains a set of dataclasses which contain
parameters required by the broader
:mod:`~virtual_ecosystem.models.abiotic.abiotic_model` model.
These parameters are constants in that they should not be changed during a particular
simulation.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class AbioticConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `abiotic` model."""

    leaf_emissivity: float = 0.97
    """Leaf emissivity."""

    bulk_density_soil: float = 1.5
    """Bulk density of soil."""

    wind_reference_height: float = 10.0
    """Reference height for wind speed above the canopy.

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

    substrate_surface_drag_coefficient: float = 0.003
    """Substrate-surface drag coefficient, dimensionless.

    The substrate-surface drag coefficient represents the resistance encountered by an
    object moving on or through a surface and varies based on the nature of the
    surface and the object's properties. Here, it affects how wind speed is altered by a
    surface. Implementation and value from :cite:t:`maclean_microclimc_2021`."""

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
    Implentation and value taken from :cite:p:`maclean_microclimc_2021`."""

    max_ratio_wind_to_friction_velocity: float = 0.3
    """Maximum ratio of wind velocity to friction velocity, dimensionless.

    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

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

    canopy_temperature_ini_factor: float = 0.01
    """Factor used to initialise canopy temperature as a function of air temperature and
    absorbed shortwave radiation."""

    light_extinction_coefficient: float = 0.01
    """Light extinction coefficient for canopy."""

    soil_thermal_conductivity: float = 0.7
    """Soil thermal conductivity, [W m-1 K-1], :cite:p:`monteith_principles_1990`.
    """

    specific_heat_capacity_soil: float = 2.7e6
    """Specific heat capacity of soil, [J kg-1 K-1], :cite:p:`monteith_principles_1990`.
    """

    surface_albedo: float = 0.125
    """Mean surface albedo of a tropical rainforest in South East Asia, dimensionless.

    The value is takes from a study that compares changes in surface albedo before and
    after deforestation in South East Asia :cite:p:`wilson_role_2020`."""

    soil_emissivity: float = 0.8
    """Soil emissivity, dimensionless."""

    saturated_pressure_slope_parameters: tuple[float, float, float, float] = (
        4098.0,
        0.6108,
        17.27,
        237.3,
    )
    """List of parameters to calculate the slope of saturated vapour pressure curve."""

    water_to_air_mass_ratio: float = 0.622
    """Ratio of the molecular mass of water vapour to dry air.
    
    This ratio is crucial because it determines how much water vapour contributes to
    the total pressure in a given air parcel.

    """
    dry_air_factor: float = 0.378
    """Dry air factor, complement of water_to_air_mass_ratio.

    This term accounts for the proportion of dry air when computing the partitioning
    of total air pressure."""

    initial_flux_value: float = 0.001
    """Initial non-zero fill value for energy fluxes, [W m-2]."""
