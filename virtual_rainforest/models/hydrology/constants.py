"""The :mod:`~virtual_rainforest.models.hydrology.constants` module contains a set of
dataclasses containing and parameters required by the
:mod:`~virtual_rainforest.models.hydrology.hydrology_model`. These parameters are
constants in that they should not be changed during a particular simulation.

TODO Soil parameters vary strongly with soil type and will require literature search and
sensitivity analysis to produce meaningful results. The current default values are just
examples within reasonable bounds.
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass(frozen=True)
class HydroConsts:
    """Dataclass to store all constants for the `hydrology` model."""

    soil_moisture_capacity: float = 0.9
    """Soil moisture capacity, also known as field capacity or water holding capacity,
    refers to the maximum amount of water that a soil can retain against the force of
    gravity after it has been saturated and excess water has drained away. The value is
    soil type specific, the format here is volumentic relative water content (unitless,
    between 0 and 1).
    """

    soil_moisture_residual: float = 0.1
    """Residual soil moisture refers to the water that remains in the soil after
    prolonged drainage due to the force of gravity. It is the water that is tightly held
    by soil particles and is not easily available for plant roots to extract. The value
    is soil specific, the format here is volumentic relative water content (unitless,
    between 0 and 1).
    """

    hydraulic_conductivity: float = 0.001
    """Hydraulic conductivity (m/s) is the measure of a soil's ability to transmit water
    through its pores. More specifically, is defined as the volumetric flow rate of
    water passing through a unit cross-sectional area of soil under a unit hydraulic
    gradient (pressure difference).
    """

    hydraulic_gradient: float = 0.01
    """The hydraulic gradient (m/m) is a measure of the change in hydraulic head
    (pressure) per unit of distance in a particular direction within a fluid or porous
    medium, such as soil or an aquifer. It represents the driving force behind the
    movement of water and indicates the direction in which water will flow.
    """

    seconds_to_day: float = 86400
    """Factor to convert variable unit from seconds to day."""

    nonlinearily_parameter: float = 2.0
    """Nonlinearity parameter n (dimensionless) in Mualem-van Genuchten model for
    hydraulic conductivity :cite:p:`van_genuchten_closed-form_1980`."""

    meters_to_mm: float = 1000
    """Factor to convert variable unit from meters to millimeters."""

    celsius_to_kelvin: float = 273.15
    """Factor to convert variable unit from Celsius to Kelvin."""

    density_air: float = 1.225
    """Density of air under standard atmosphere, kg m-3"""

    latent_heat_vapourisation: float = 2.45
    """Latent heat of vapourisation under standard atmosphere, MJ kg-1"""

    gas_constant_water_vapour: float = 461.51
    """Gas constant for water vapour, J kg-1 K-1"""

    heat_transfer_coefficient: float = 12.5
    """Heat transfer coefficient, :cite:p:`van_de_griend_bare_1994` """

    stream_flow_capacity: float = 5000.0
    """Stream flow capacity, mm per timestep. This is curretly an arbitrary value, but
    could be used in the future to flag flood events."""

    intercept_param_1: float = 0.935
    """Parameter in equation that estimates maximum canopy interception capacity after
    :cite:t:`von_hoyningen-huene_interzeption_1981`."""

    intercept_param_2: float = 0.498
    """Parameter in equation that estimates maximum canopy interception capacity after
    :cite:t:`von_hoyningen-huene_interzeption_1981`."""

    intercept_param_3: float = 0.00575
    """Parameter in equation that estimates maximum canopy interception capacity after
    :cite:t:`von_hoyningen-huene_interzeption_1981`."""

    veg_density_param: float = 0.046
    """Parameter used to estimate vegetation density for maximum canopy interception
    capacity estimate after :cite:t:`von_hoyningen-huene_interzeption_1981`."""

    groundwater_capacity: float = 500
    """Ground water storage capacity in relative volumetric water content. This might be
    replaced with the implementation of below ground horizontal flow."""

    alpha: float = 0.3
    r"""Dimensionless parameter :math:`alpha` in van Genuchten model that corresponds
    approximately to the inverse of the air-entry value, [kPa-1]
    :cite:p:`van_genuchten_closed-form_1980`"""

    infiltration_shape_parameter: float = 1.0
    """Empirical shape parameter that affects how much of the water available for
    infiltration goes directly to groundwater via preferential bypass flow. A value of
    0 means all surface water goes directly to groundwater, a value of 1 gives a linear
    relation between soil moisture and bypass flow."""

    max_percolation_rate_uzlz: float = 1
    """maximum perclation rate between pper and lower groundwater zone, [mm d-1]"""

    groundwater_loss: float = 1
    """constant amount of water that never rejoins the river channel and is lost beyond
    the catchment boundaries or to deep groundwater systems, [mm]"""

    reservoir_const_upper_groundwater: float = 20
    """reservoir constant for the upper groundwater layer, [days]"""

    reservoir_const_lower_groundwater: float = 20
    """reservoir constant for the lower groundwater layer, [days]"""
