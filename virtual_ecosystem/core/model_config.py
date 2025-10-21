"""The `models.animal.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_ecosystem.models.animal` module

"""  # noqa: D205, D415

from datetime import date
from typing import ClassVar

import numpy as np
from pint import DimensionalityError, Quantity, UndefinedUnitError
from pydantic import (
    Field,
    NegativeFloat,
    PositiveFloat,
    PositiveInt,
    PrivateAttr,
    field_validator,
)
from scipy import constants

from virtual_ecosystem.core.configuration import Configuration


class CoreConstants(Configuration):
    """Core constants for use across the Virtual Ecosystem modules.

    An instance of the CoreConsts dataclass provides definitions of the core constants
    used across an entire simulation. The core constants can be changed, as shown below,
    although for many this would likely generate nonsensical results.

    Example:
        >>> consts = CoreConsts()
        >>> consts.max_depth_of_microbial_activity
        0.25
        >>> consts = CoreConsts(max_depth_of_microbial_activity=0.75)
        >>> consts.max_depth_of_microbial_activity
        0.75
    """

    placeholder: float = 123.4
    """A placeholder configurable constant."""

    zero_Celsius: ClassVar[float] = constants.zero_Celsius
    """Conversion constant from Kelvin to Celsius (°)."""

    standard_pressure: float = constants.atmosphere / 1000
    """Standard atmospheric pressure, [kPa]"""

    standard_mole: float = 44.642
    """Moles of ideal gas in 1 m^3 air at standard atmosphere."""

    molar_heat_capacity_air: float = 29.19
    """Molar heat capacity of air, [J mol-1 K-1]."""

    gravity: float = constants.gravitational_constant
    """Newtonian constant of gravitation, [m s-1]."""

    stefan_boltzmann_constant: float = constants.Stefan_Boltzmann
    """Stefan-Boltzmann constant, [W m-2 K-4].

    The Stefan-Boltzmann constant relates the energy radiated by a black body to its
    temperature."""

    von_karmans_constant: float = 0.4
    """Von Karman's constant, [unitless].

    The von Karman's constant describes the logarithmic velocity profile of a turbulent
    fluid near a no-slip boundary."""

    max_depth_of_microbial_activity: float = 0.25
    """Maximum depth of microbial activity in the soil layers [m].

    The soil model needs to identify which of the configured soil layers are
    sufficiently close to the surface to contain significant microbial activity that
    drives nutrient processes. The default value is taken from
    :cite:t:`fatichi_mechanistic_2019`. No empirical source is provided for this value.
    """

    meters_to_mm: float = 1000.0
    """Factor to convert variable unit from meters to millimeters."""

    molecular_weight_air: float = 28.96
    """Molecular weight of air, [g mol-1]."""

    gas_constant_water_vapour: float = 461.51
    """Gas constant for water vapour, [J kg-1 K-1]"""

    seconds_to_day: float = 86400.0
    """Factor to convert variable unit from seconds to day."""

    seconds_to_hour: float = 3600.0
    """Factor to convert variable unit from seconds to hours."""

    characteristic_dimension_leaf: float = 0.01
    """Characteristic dimension of leaf, typically around 0.7 * leaf width, [m]."""

    specific_gas_constant_dry_air: float = 287.05
    """Specific gas constant for dry air, [J kg-1 K-1]."""

    molecular_weight_ratio_water_to_dry_air: float = 0.622
    """The molecular weight ratio of water to dry air.
    
    The ratio of the molar mass of water vapour (18.015 g/mol) to the molar mass of dry
    air (28.964 g/mol), which is approximately 0.622. This ratio is used in atmospheric
    calculations, particularly in determining the mixing ratio of water vapour to dry
    air."""

    conductance_to_resistance_conversion_factor: float = 40.9
    """Conductance to resistance conversion factor.
    
    This factor is used to convert between stomatal conductance in mmol m-2 s-1 and
    stomatal resistance in s m-1."""

    density_water: float = 1000.0
    """Density of water, [kg m-3]."""

    fungal_fruiting_bodies_c_n_ratio: float = 10.0
    """Carbon to nitrogen ratio of fungal fruiting bodies, [unitless].
    
    This constant is stored in the CoreConsts as it is used by both the animal model
    (to work out consumption flows) and the soil model (to work out production rates).
    The current default value is very much a guess.
    """

    fungal_fruiting_bodies_c_p_ratio: float = 75.0
    """Carbon to phosphorus ratio of fungal fruiting bodies, [unitless].
    
    This constant is stored in the CoreConsts as it is used by both the animal model (to
    work out consumption flows) and the soil model (to work out production rates). The
    current default value is very much a guess.
    """

    fungal_fruiting_bodies_decay_rate: float = np.log(2) / 50.0
    """Rate constant for the decay of fungal fruiting bodies, [day^-1].
    
    This is calculated based on the assumption that fungal fruiting bodies decay with a
    half-life of 50 days. This estimate should be improved based on empirical data.
    """


class GridConfiguration(Configuration):
    """Grid configuration.

    This configuration model sets the size and shape of grid cells within the simulation
    and then the number of cells in the X and Y directions and their locations in space.
    """

    grid_type: str = "square"
    """The grid cell type. The value must be one of the options supported by the 
    :data:`~virtual_ecosystem.core.grid.GRID_REGISTRY`."""
    cell_area: PositiveFloat = Field(default=8100.0)
    """The area of each grid cell (m^2)"""
    cell_nx: PositiveInt = Field(default=9)
    """Number of grid cells in x direction"""
    cell_ny: PositiveInt = Field(default=9)
    """Number of grid cells in y direction"""
    xoff: float = -45.0
    """The x offset of the grid origin"""
    yoff: float = -45.0
    """The x offset of the grid origin"""


class TimingConfiguration(Configuration):
    """Configuration of the model timing.

    This configuration section sets the model start data, update length and run time.
    The update length and run time are provided as a text string that will be
    automatically parsed to give a total time in seconds.
    """

    start_date: date = date(2013, 1, 1)
    """The simulation start date."""
    update_interval: str = "1 month"
    """The interval at which all models are updated."""
    run_length: str = "2 years"
    """The total run length of the simulation."""

    _update_interval_seconds: int = PrivateAttr()
    """Interval update length in seconds"""
    _run_length_seconds: int = PrivateAttr()
    """Total run length in seconds"""

    @field_validator("update_interval", "run_length")
    def validate_pint_time_quantities(cls, value):
        """Validates time strings can be parsed as quantities."""
        try:
            _ = Quantity(value).to("seconds")
        except (DimensionalityError, UndefinedUnitError):
            raise ValueError(f"Cannot parse value as time quantity: {value}")

    def __post_init__(self):
        """Post init to set values in seconds and check enough time for one update."""
        self._update_interval_seconds = Quantity(self.update_interval).to("seconds")
        self._run_length_seconds = Quantity(self._run_length_seconds).to("seconds")

        if self.run_length < self._update_interval_seconds:
            raise ValueError(
                f"Model run length ({self.run_length}) expires before "
                f"first update ({self.update_interval})"
            )


class DataOutputConfiguration(Configuration):
    """Output settings for the Virtual Ecosystem model state."""

    save_initial_state: bool = False
    "Whether the initial state should be saved"
    save_continuous_data: bool = True
    "Whether continuous data should be saved"
    save_final_state: bool = True
    "Whether the final state should be saved"
    save_merged_config: bool = True
    "Whether to save a merged TOML file containing all config options"
    out_path: str = "."
    "File path for output files"
    out_initial_file_name: str = "initial_state.nc"
    """File name for initial state output file"""
    out_folder_continuous: str = "."
    "Folder to save states of simulation with time to"
    out_continuous_file_name: str = "all_continuous_data.nc"
    """Name of file to save combined continuous data to"""
    out_final_file_name: str = "final_state.nc"
    """File name for final state output file"""
    out_merge_file_name: str = "ve_full_model_configuration.toml"
    """Name for TOML file containing merged configs"""


class LayersConfiguration(Configuration):
    """Settings for the simulation vertical structure."""

    soil_layers: list[NegativeFloat] = Field(min_length=1, default=[-0.25, -1.0])
    """A list of negative float values that provides the depth in metres of the soil
    horizons to be used in the simulation, hence also setting the number of soil layers
    and the horizon depth for each layer relative to the surface. The values must be
    unique and strictly decreasing.
    """
    canopy_layers: int = Field(gt=0, default=10)
    """The maximum number of canopy layers to simulate. This is used to control the 
    number of layers with the ``canopy`` role. Not all of these layers necessarily
    contain canopy during a simulation as the canopy structure within these layers is
    dynamic."""
    ""
    above_canopy_height_offset: PositiveFloat = Field(default=2.0)
    """A height offset relative to the canopy top that is used as the measurement height
    of reference climate data. It sets the the height above the canopy top of the first
    layer role ``above`` (metres)."""

    subcanopy_layer_height: PositiveFloat = Field(default=1.5)
    """The height above ground level of the ground surface atmospheric layer, used to
    calculate subcanopy microclimate conditions (metres)."""

    surface_layer_height: PositiveFloat = Field(default=0.1)
    """The height above ground level of the ground surface atmospheric layer
    (metres)."""

    @field_validator("soil_layers")
    def soil_depths_unique_decreasing(cls, values):
        """Check the soil depths are unique and decreasing.

        This runs post validation, so the inputs are a list of negative floats.
        """

        if len(values) != len(set(values)):
            raise ValueError("Repeated values in soil layer depths.")

        strictly_decreasing = [-m for m in sorted([abs(n) for n in values])]
        if not values == strictly_decreasing:
            raise ValueError("Soil layer depths must be strictly decreasing")

    @field_validator("soil_layers")
    def finite_heights(cls, value):
        """Prevent infinite heights.

        This seems paranoid, but was in the older validation.
        """
        if value == np.inf:
            raise ValueError("Height must be finite.")


class DataSource(Configuration):
    """Data source configuration."""

    file_path: str = "placeholder"
    var_name: str = "placeholder"


class Variables(Configuration):
    """Variables configuration."""

    variable: tuple[DataSource, ...] = (DataSource(), DataSource())


class CoreConfiguration(Configuration):
    """The core model configuration."""

    constants: CoreConstants = CoreConstants()
    """Constants for the core module"""
    grid: GridConfiguration = GridConfiguration()
    """Configuration of the spatial grid"""
    data_output_options: DataOutputConfiguration = DataOutputConfiguration()
    """Configuration of the output of the Virtual Ecosystem model state"""
    layers: LayersConfiguration = LayersConfiguration()
    """Configuration of the layers in the vertical structure"""
    timing: TimingConfiguration = TimingConfiguration()
    """Configuration of the model run and step lengths"""
    data: Variables = Variables()
    """Configuration of the input variables and data sources."""
