"""The :mod:`~virtual_ecosystem.models.hydrology.constants` module contains a set of
dataclasses containing parameters required by the
:mod:`~virtual_ecosystem.models.hydrology.hydrology_model`. These parameters are
constants in that they should not be changed during a particular simulation.

TODO Soil parameters vary strongly with soil type and will require literature search and
sensitivity analysis to produce meaningful results. The current default values are just
examples within reasonable bounds.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class HydroConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `hydrology` model."""

    soil_moisture_capacity: float = 0.9
    """Soil moisture capacity, unitless.

    The soil moisture capacity, also known as field capacity or water holding capacity,
    refers to the maximum amount of water that a soil can retain against the force of
    gravity after it has been saturated and excess water has drained away. The value is
    soil type specific, the format here is volumentic relative water content (unitless,
    between 0 and 1).
    """

    soil_moisture_residual: float = 0.1
    """Residual soil moisture, unitless.

    The residual soil moisture refers to the water that remains in the soil after
    prolonged drainage due to the force of gravity. It is the water that is tightly held
    by soil particles and is not easily available for plant roots to extract. The value
    is soil specific, the format here is volumentic relative water content (unitless,
    between 0 and 1).
    """

    hydraulic_conductivity: float = 0.001
    """Hydraulic conductivity, [m s-1].

    The hydraulic conductivity is the measure of a soil's ability to transmit water
    through its pores. More specifically, is defined as the volumetric flow rate of
    water passing through a unit cross-sectional area of soil under a unit hydraulic
    gradient (pressure difference).
    """

    hydraulic_gradient: float = 0.01
    """The hydraulic gradient, [m m-1].

    The hydraulic gradient is a measure of the change in hydraulic head
    (pressure) per unit of distance in a particular direction within a fluid or porous
    medium, such as soil or an aquifer. It represents the driving force behind the
    movement of water and indicates the direction in which water will flow.
    """

    nonlinearily_parameter: float = 2.0
    """Nonlinearity parameter n (dimensionless) in Mualem-van Genuchten model.

    This parameter is a fitting shape parameters of soil water retention curve, see
    :cite:p:`van_genuchten_closed-form_1980`."""

    soil_surface_heat_transfer_coefficient: float = 12.5
    """Heat transfer coefficient from soil to atmosphere above, [W m-2 K-1].

    :cite:p:`van_de_griend_bare_1994`.
    """

    stream_flow_capacity: float = 5000.0
    """Stream flow capacity, [mm per timestep].

    This parameter represents the maximum capacity of an average stream in the model.
    At the moment, this is set as an arbitrary value, but could be used in the future to
    flag flood events."""

    intercept_parameters: tuple[float, float, float] = (0.935, 0.498, 0.00575)
    """Interception parameters.

    Parameters in equation that estimates maximum canopy interception capacity after
    :cite:t:`von_hoyningen-huene_interzeption_1981`."""

    veg_density_param: float = 0.046
    """Parameter to estimate vegetation density for maximum canopy interception.

    This parameter is used to estimate the water holding capacity of a canopy after
    :cite:t:`von_hoyningen-huene_interzeption_1981`."""

    groundwater_capacity: float = 500
    """Ground water storage capacity, [mm].

    This parameter indicates how much water can be stored in the ground water reservoir
    which affects the vertical flow of water and the horizontal sub-surface flow. This
    parameter is currently set to an arbitrary value and might."""

    infiltration_shape_parameter: float = 1.0
    """Empirical infiltration shape parameter, unitless.

    This parameter affects how much of the water available for infiltration goes
    directly to groundwater via preferential bypass flow. A value of
    0 means all surface water goes directly to groundwater, a value of 1 gives a linear
    relation between soil moisture and bypass flow."""

    air_entry_water_potential: float = -3.815
    """Water potential at which soil pores begin to aerate, [kPa].

    The constant is used to estimate soil water potential from soil moisture. As this
    estimation is a stopgap this constant probably shouldn't become a core constant. The
    value is the average across all soil types found in
    :cite:t:`cosby_statistical_1984`. In future, this could be calculated based on soil
    texture.
    """

    water_retention_curvature: float = -7.22
    """Curvature of the water retention curve.

    The value is the average across all soil types found in
    :cite:t:`cosby_statistical_1984`; see documentation for
    :attr:`air_entry_water_potential` for further details.
    """

    extinction_coefficient_global_radiation: float = 0.7
    """Extinction coefficient for global radiation, [unitless].

    This constant is used to reduce potential evaporation for bare soil to maximum
    shaded evaporation in
    :func:~virtual_ecosystem.models.hydrology.above_ground.calculate_soil_evaporation`.
    Typical values are 0.4 to 0.7 for monocotyledons and 0.65 to 1.1 for broad leaved
    dicotyledons :cite:t:`monteith_light_1969`. The extinction coefficient can be
    estimated from measurements of PAR above and below a canopy with a known LAI.
    """

    max_percolation_rate_uzlz: float = 1
    """Maximum percolation rate between upper and lower groundwater zone, [mm d-1]"""

    groundwater_loss: float = 1
    """Constant ground water loss, [mm].

    This parameter defines the constant amount of water that never rejoins the river
    channel and is lost beyond the catchment boundaries or to deep groundwater systems.
    """

    reservoir_const_upper_groundwater: float = 20
    """Reservoir constant for the upper groundwater layer, [days]"""

    reservoir_const_lower_groundwater: float = 20
    """Reservoir constant for the lower groundwater layer, [days]"""
