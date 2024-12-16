"""The ``models.abiotic_simple.constants`` module contains a set of dataclasses
containing parameters required by the :mod:`~virtual_ecosystem.models.abiotic_simple`
model. These parameters are constants in that they should not be changed during a
particular simulation.
"""  # noqa: D205

from dataclasses import dataclass, field

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class AbioticSimpleConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `abiotic_simple` model."""

    saturation_vapour_pressure_factors: list[float] = field(
        default_factory=lambda: [0.61078, 7.5, 237.3]
    )
    """Factors for saturation vapour pressure calculation."""

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

    min_roughness_length: float = 0.01
    """Minimum roughness length, [m].

    The minimum roughness length represents the lowest height at which the surface
    roughness significantly affects the wind flow over a particular terrain or surface.
    Implementation and value from :cite:t:`maclean_microclimc_2021`."""

    wind_reference_height: float = 10.0
    """Reference height for wind speed above the canopy.
    
    The reference height for horizontal wind is typically 10m above ground compared to
    2m for other atmospheric variables such as temperature and relative humidity. We
    assume here that the reference height is above the canopy, please check the input
    data carefully and be aware of limitations."""


@dataclass(frozen=True)
class AbioticSimpleBounds(ConstantsDataclass):
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

    soil_temperature: tuple[float, float] = (-10.0, 50.0)
    """Bounds for soil temperature, [C]."""
