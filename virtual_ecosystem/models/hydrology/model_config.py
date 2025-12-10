"""The :mod:`~virtual_ecosystem.models.hydrology.model_config` defines configuration
dataclasses containing parameters required by the
:mod:`~virtual_ecosystem.models.hydrology.hydrology_model`. These parameters are
constants in that they should not be changed during a particular simulation.

Note that soil parameters vary strongly with soil type and can change over time. The
current default values are average best estimates within reasonable bounds.
"""  # noqa: D205

from pydantic import Field

from virtual_ecosystem.core.configuration import Configuration, ModelConfigurationRoot


class HydrologyConstants(Configuration):
    """Dataclass to store all constants for the `hydrology` model."""

    soil_moisture_residual: float = 0.175
    """Residual soil moisture, unitless.

    The residual soil moisture refers to the water that remains in the soil after
    prolonged drainage due to the force of gravity. It is the water that is tightly held
    by soil particles and is not easily available for plant roots to extract. The value
    is soil specific, the format here is volumentic relative water content (unitless,
    between 0 and 1). Average value of different soil textures across tropical regions
    :cite:p:`hodnett_marked_2002`.
    """

    soil_moisture_saturation: float = 0.51
    """Soil moisture saturation, unitless.

    Maximum amount of water a soil can hold when all its pores are completely filled
    with water — that is, the soil is fully saturated and contains no air in the pore
    spaces. Average value of different soil textures across tropical regions
    :cite:p:`hodnett_marked_2002`
    .
    """

    saturated_hydraulic_conductivity: float = 3.5e-5
    """Saturated hydraulic conductivity, [m s-1].

    The saturated hydraulic conductivity is the measure of a soil's ability to transmit
    water through its pores. More specifically, is defined as the volumetric flow rate
    of water passing through a unit cross-sectional area of soil under a unit hydraulic
    gradient (pressure difference). Value for average tropical rainforest taken from
    :cite:t:`gupta_global_2022`.
    """

    hydraulic_gradient: float = 1.31
    """The hydraulic gradient, [m].

    The hydraulic gradient is a measure of the change in hydraulic head
    (pressure) per unit of distance in a particular direction within a fluid or porous
    medium, such as soil or an aquifer. It represents the driving force behind the
    movement of water and indicates the direction in which water will flow. Value for
    subtropical regions, taken from :cite:t:`reichardt_hydraulic_1993`; depends on the
    soil type, permeability, slope, and water table depth.
    """

    van_genuchten_nonlinearily_parameter: float = 1.598
    """Nonlinearity parameter n (dimensionless) in Mualem-van Genuchten model.

    This parameter is a fitting shape parameters of soil water retention curve, see
    :cite:p:`van_genuchten_closed-form_1980`. Average value of different soil textures
    across tropical regions 
    is taken from :cite:t:`hodnett_marked_2002`.
    """

    stream_flow_capacity: float = 5000.0
    """Stream flow capacity, [mm per day].

    This parameter represents the maximum capacity of an average stream in the model.
    At the moment, this is set as an arbitrary value; we are working on getting a best
    estimate."""

    intercept_parameters: tuple[float, float, float] = (0.935, 0.498, 0.00575)
    """Interception parameters, unitless.

    Parameters in equation that estimates maximum canopy interception capacity after
    :cite:t:`von_hoyningen-huene_interzeption_1981`."""

    veg_density_param: float = 0.046
    """Parameter to estimate vegetation density for maximum interception, unitless.

    This parameter is used to estimate the water holding capacity of a canopy after
    :cite:t:`von_hoyningen-huene_interzeption_1981`. The value is taken from
    :cite:t:`van_der_knijff_lisflood_2010`."""

    groundwater_capacity: float = 500
    """Ground water storage capacity, [mm].

    This parameter indicates how much water can be stored in the ground water reservoir
    which affects the vertical flow of water and the horizontal sub-surface flow. This
    parameter is currently set to an arbitrary value; we are working on getting a best
    estimate."""

    bypass_flow_coefficient: float = 1.0
    """Empirical bypass flow coefficient, unitless.

    This parameter affects how much of the water available for infiltration goes
    directly to groundwater via preferential bypass flow. A value of
    0 means all surface water goes directly to groundwater, a value of 1 gives a linear
    relation between soil moisture and bypass flow."""

    air_entry_water_potential: float = -3.648
    """Water potential at which soil pores begin to aerate, [kPa].

    The constant is used to estimate soil water potential from soil moisture. As this
    estimation is a stopgap this constant probably shouldn't become a core constant. The
    value is the average across soil types found in :cite:t:`tao_simplified_2021`.
    """

    extinction_coefficient_global_radiation: float = 0.74
    """Extinction coefficient for global radiation, [unitless].

    This constant is used to reduce potential evaporation for bare soil to maximum
    shaded evaporation.
    Typical values are 0.4 to 0.7 for monocotyledons and 0.65 to 1.1 for broad leaved
    dicotyledons :cite:t:`monteith_light_1969`. The value for tropical forest is taken
    from :cite:t:`saldarriaga_solar_1991`. The extinction coefficient can be
    estimated from measurements of PAR above and below a canopy with a known LAI.
    """

    max_percolation_rate_uzlz: float = 2.7
    """Maximum percolation rate between upper and lower groundwater zone, [mm d-1].
    
    Values for tropical rainforest are taken from :cite:t:`brink_modelling_2009`."""

    groundwater_loss: float = 1
    """Constant ground water loss, [mm].

    This parameter defines the constant amount of water that never rejoins the river
    channel and is lost beyond the catchment boundaries or to deep groundwater systems.
    """

    reservoir_const_upper_groundwater: float = 20
    """Reservoir constant for the upper groundwater layer, [days].
    
    This parameter defines the residence time (in days) of water in the upper
    groundwater zone before contributing to streamflow, with typical values for tropical
    catchments ranging from 5 to 30 days depending on soil permeability and slope.
    This parameter is currently set to an arbitrary value; we are working on getting a
    better estimate."""

    reservoir_const_lower_groundwater: float = 20
    """Reservoir constant for the lower groundwater layer, [days].
    
    This reservoir constant, measured in days, determines the residence time of water in
    the lower groundwater zone. It influences how quickly water exits the lower zone as
    baseflow. Typical values range from 10 to 5000 depending on catchment
    characteristics. This parameter is currently set to an arbitrary value; we are
    working on getting a better estimate."""

    initial_aerodynamic_resistance_surface: float = 12.5
    """Initial aerodynamic resistance at the soil surface, [s m-1].
    
    This parameter is an initial estimate of the resistance to the transfer of momentum,
    heat, and water vapour between the soil surface and the atmosphere. The value is
    based on Australian evergreen forest, taken from :cite:t:`su_aerodynamic_2021`;
    note that this assumes a dense canopy.
    """

    initial_aerodynamic_resistance_canopy: float = 12.1
    """Initial aerodynamic resistance of the canopy, [s m-1].
    
    This parameter is an initial estimate of the resistance to the transfer of momentum,
    heat, and water vapour between the leaf surface and the atmosphere. The value is
    based on Australian evergreen forest, taken from :cite:t:`su_aerodynamic_2021`;
    note that this assumes a dense canopy.
    """

    drag_coefficient_evaporation: float = 0.2
    """Drag coefficient for evaporation, dimensionless.
    
    Represents the efficiency of turbulent transport of water vapour from a surface to
    the atmosphere."""

    intercept_residence_time: float = 86400.0
    """Intecept residence time, [s].
    
    The amount of time that water sits on the leaves before it evaporates or falls to
    the ground. We currently assume that at the end of each day, all water has either
    evaporated or fallen to the ground."""

    initial_stomatal_conductance: float = 1000.0
    """Initial stomatal conductance, [mmol m-2 s-1].
    
    Initial estimate of the rate at which water vapor and carbon dioxide pass
    through the stomata of plant leaves, reflecting how open the stomata are and
    regulating both transpiration and gas exchange.
    """

    pore_connectivity_parameter: float = 0.5
    """Pore connectivity parameter, dimensionless.
    
    Dimensionless parameter used in van Genuchten-Mualem model to calculate unsaturated
    hydraulic conductivity."""

    air_entry_potential_inverse: float = 0.042
    """Inverse of air entry potential (parameter alpha in van Genuchten), [m-1].
    
    The inverse of air entry potential describes how quickly soil water retention
    decreases with increasing soil suction, with higher values indicating coarser soils
    that drain more readily. Average value of different soil textures across tropical
    regions :cite:p:`hodnett_marked_2002`."""

    m_to_kpa: float = 9.804
    """Factor to convert matric potential from m to kPa."""


class HydrologyConfiguration(ModelConfigurationRoot):
    """Root configuration clas for the hydrology model."""

    initial_soil_moisture: float = Field(ge=0, le=1, default=0.5)
    """Initial soil moisture for all layers"""
    initial_groundwater_saturation: float = Field(ge=0, le=1, default=0.9)
    """Initial ground water saturation for all layers, unitless"""
    constants: HydrologyConstants = HydrologyConstants()
    """Constants values for hydrology model."""
