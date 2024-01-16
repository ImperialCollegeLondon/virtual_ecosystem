"""The ``models.abiotic.constants`` module contains a set of dataclasses which contain
parameters required by the broader :mod:`~virtual_rainforest.models.abiotic` model.
These parameters are constants in that they should not be changed during a particular
simulation.
"""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_rainforest.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class AbioticConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `abiotic` model."""

    specific_heat_equ_factor_1: float = 2e-05
    """Factor in calculation of molar specific heat of air.

    Implementation after :cite:t:`maclean_microclimc_2021`."""

    specific_heat_equ_factor_2: float = 0.0002
    """Factor in calculation of molar specific heat of air.

    Implementation after :cite:t:`maclean_microclimc_2021`."""

    latent_heat_vap_equ_factor_1: float = 1.91846e6
    """Factor in calculation of latent heat of vaporisation.

    Implementation after :cite:t:`maclean_microclimc_2021`, value is taken from
    :cite:t:`henderson-sellers_new_1984`.
    """
    latent_heat_vap_equ_factor_2: float = 33.91
    """Factor in calculation of latent heat of vaporisation.

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
    object moving on or through a surface and varies based on the nature of the surface
    and the object's properties. Here, it affects how wind speed is altered by a surface
    . Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    roughness_element_drag_coefficient: float = 0.3
    """Roughness-element drag coefficient, dimensionless.

    The roughness-element drag coefficient refers to the dimensionless coefficient used
    to quantify the drag force exerted by individual roughness elements (such as
    buildings, trees, or surface irregularities) on airflow, influencing the overall
    aerodynamic characteristics of a surface within the atmospheric boundary layer.
    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    roughness_sublayer_depth_parameter: float = 0.193
    """Parameter characterizes the roughness sublayer depth.

    The roughness sublayer depth refers to the layer near the surface where the effects
    of surface roughness significantly influence airflow, turbulence, and momentum
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

    relative_turbulence_intensity: float = 0.5
    """Relative turbulence intensity, dimensionless.

    The relative turbulence intensity is a proportionality factor that relates the mean
    eddy velocity is assumed to the local wind speed below the canopy. Implementation
    and value from :cite:t:`maclean_microclimc_2021`."""

    diabatic_correction_factor_below: float = 1
    """Diabatic correction factor below canopy, dimensionless.

    The diabatic correction factor is a scaling adjustment used to compensate for the
    effects of vertical heat transfer or thermal non-adiabaticity on atmospheric
    variables or processes, particularly when estimating or interpreting measurements
    across different heights or conditions. This factor is used to adjust wind profiles
    below the canopy. Implementation and value from :cite:t:`maclean_microclimc_2021`.
    """

    mixing_length_factor: float = 0.32
    """Factor in calculation of mixing length, dimensionless.

    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    min_relative_turbulence_intensity: float = 0.36
    """Minimum relative turbulence intensity, dimensionless.

    See :attr:`relative_turbulence_intensity`.
    The default value is taken from Shaw et al (1974) Agricultural Meteorology, 13:
    419-425. TODO this is not representative of a rainforest environment and needs to be
    adjusted.
    """

    max_relative_turbulence_intensity: float = 0.9
    """Maximum relative turbulence intensity, dimensionless.

    See :attr:`relative_turbulence_intensity`.
    The default value from Shaw et al (1974) Agricultural Meteorology, 13: 419-425.
    TODO this is not representative of a rainforest environment and needs to be
    adjusted."""

    min_wind_speed_above_canopy: float = 0.55
    """Minimum wind speed above the canopy, [m/s].

    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    min_windspeed_below_canopy: float = 0.001
    """Minimum wind speed below the canopy or in absence of vegetation, [m/s]."""

    min_roughness_length: float = 0.05
    """Minimum roughness length, [m].

    The minimum roughness length represents the lowest height at which the surface
    roughness significantly affects the wind flow over a particular terrain or surface.
    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    yasuda_stability_parameter1: float = 6
    """Parameter to approximate diabatic correction factors for heat and momentum.

    Dimenionless parameter, implementation after :cite:t:`maclean_microclimc_2021` and
    values taken from :cite:t:`yasuda_turbulent_1988`."""

    yasuda_stability_parameter2: float = 2
    """Parameter to approximate diabatic correction factors for heat and momentum.

    Dimenionless parameter, implementation after :cite:t:`maclean_microclimc_2021` and
    values taken from :cite:t:`yasuda_turbulent_1988`."""

    yasuda_stability_parameter3: float = 16
    """Parameter to approximate diabatic correction factors for heat and momentum.

    Dimenionless parameter, implementation after :cite:t:`maclean_microclimc_2021` and
    values taken from :cite:t:`yasuda_turbulent_1988`."""

    diabatic_heat_momentum_ratio: float = 0.6
    """Factor that relates diabatic correction factors for heat and momentum.

    Dimenionless parameter, implementation after :cite:t:`maclean_microclimc_2021` and
    values taken from :cite:t:`yasuda_turbulent_1988`."""

    turbulence_sign: bool = True
    """Flag indicating if turbulence increases or decreases with height."""

    canopy_temperature_ini_factor: float = 0.01
    """Factor used to initialise canopy temperature as a function of air temperature and
    absorbed shortwave radiation."""

    light_extinction_coefficient: float = 0.01
    """Light extinction coefficient for canopy, default = 0.01."""

    latent_heat_flux_fraction: float = 0.5
    """Fraction of incoming energy that is turned into latent heat flux, default = 0.5.
    """

    ground_heat_flux_fraction: float = 0.05
    """Fraction of incoming energy that is turned into ground heat flux, default = 0.05.
    """

    gas_constant_water_vapor: float = 461.51
    """Gas constant for water vapor, [J kg -1 K-1]."""

    specific_heat_capacity_leaf: float = 2760.0
    """Specific heat capacity of leaf, [J kg-1 K-1], default = 2760
    :cite:p:`aston_heat_1985`.
    """

    leaf_heat_transfer_coefficient: float = 50.0
    """Leaf heat transfer coefficient, [s^1/2 m^-1/2],
    :cite:p:`linacre_determinations_1964`, default = 50.
    """

    stomatal_resistance: float = 200.0
    """Stomatal resistance, default = 200."""

    soil_surface_heat_transfer_coefficient: float = 12.5
    """Soil surface heat transfer coefficient, default = 12.5
    :cite:p:`van_de_griend_bare_1994`.
    """

    soil_thermal_conductivity: float = 0.7
    """Soil thermal conductivity, [W m-1 K-1], default = 0.7
    :cite:p:`monteith_principles_1990`.
    """

    specific_heat_capacity_soil: float = 2.7e6
    """Specific heat capacity of soil, [J kg-1 K-1], default = 2.7e6
    :cite:p:`monteith_principles_1990`.
    """

    initial_air_conductivity: float = 50.0
    """Initial air conductivity, (mol m-2 s-1)"""

    top_leaf_vapor_conductivity: float = 0.32
    """Initial leaf vapor conductivity at the top of the canopy, (mol m-2 s-1)"""

    bottom_leaf_vapor_conductivity: float = 0.25
    """Initial leaf vapor conductivity at the bottom of the canopy, (mol m-2 s-1)"""

    top_leaf_air_conductivity: float = 0.19
    """Initial leaf air heat conductivity at the top of the canopy, (mol m-2 s-1)"""

    bottom_leaf_air_conductivity: float = 0.13
    """Initial leaf air heat conductivity at the bottom of the canopy, (mol m-2 s-1)"""
