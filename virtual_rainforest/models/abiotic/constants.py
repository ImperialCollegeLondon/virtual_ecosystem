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

    The substrate-surface drag coefficient represents the ratio of drag force exerted on
    a surface to the dynamic pressure, crucial for modeling airflow over different
    surface types, such as vegetation or rough terrain. Implementation and value from
    :cite:t:`maclean_microclimc_2021`."""

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
    """Relative turbulence intensity.

    The relative turbulence intensity is a proportionality factor that relates the mean
    eddy velocity is assumed to the local wind speed below the canopy. Implementation
    and value from :cite:t:`maclean_microclimc_2021`."""

    diabatic_correction_factor_below: float = 1
    """Diabatic correction factor below canopy.

    The diabatic correction factor is a scaling adjustment used to compensate for the
    effects of vertical heat transfer or thermal non-adiabaticity on atmospheric
    variables or processes, particularly when estimating or interpreting measurements
    across different heights or conditions. This factor is used to adjust wind profiles
    below the canopy. Implementation and value from :cite:t:`maclean_microclimc_2021`.
    """

    mixing_length_factor: float = 0.32
    """Factor in calculation of mixing length.

    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    min_relative_turbulence_intensity: float = 0.36
    """Minimum relative turbulence intensity.

    See :attr:`relative_turbulence_intensity`.
    The default value is taken from Shaw et al (1974) Agricultural Meteorology, 13:
    419-425. TODO this is not representative of a rainforest environment and needs to be
    adjusted.
    """

    max_relative_turbulence_intensity: float = 0.9
    """Maximum relative turbulence intensity.

    See :attr:`relative_turbulence_intensity`.
    The default value from Shaw et al (1974) Agricultural Meteorology, 13: 419-425.
    TODO this is not representative of a rainforest environment and needs to be
    adjusted."""

    min_wind_speed_above_canopy: float = 0.55
    """Minimum wind speed above the canopy, [m/s].

    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    min_roughness_length: float = 0.05
    """Minimum roughness length, [m].

    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    yasuda_stability_parameter1: float = 6
    """Parameter to approximate diabatic correction factors for heat and momentum.

    after :cite:t:`yasuda_turbulent_1988`."""

    yasuda_stability_parameter2: float = 2
    """Parameter to approximate diabatic correction factors for heat and momentum.

    Value is taken from :cite:t:`yasuda_turbulent_1988`."""

    yasuda_stability_parameter3: float = 16
    """Parameter to approximate diabatic correction factors for heat and momentum.

    Value is taken :cite:t:`yasuda_turbulent_1988`."""

    diabatic_heat_momentum_ratio: float = 0.6
    """Factor that relates diabatic correction factors for heat and momentum.

    Value is taken :cite:t:`yasuda_turbulent_1988`."""
