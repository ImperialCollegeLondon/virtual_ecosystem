"""The `models.animal.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_ecosystem.models.animal` module

"""  # noqa: D205, D415

from datetime import date
from typing import ClassVar

import numpy as np
from pydantic import Field
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


class GridConfig(Configuration):
    """Grid configuration."""

    grid_type: str = "square"
    ("The grid cell type",)
    cell_area: float = Field(gt=0, default=8100.0)
    ("The area of each grid cell (m^2)",)
    cell_nx: int = Field(gt=0, default=9)
    "Number of grid cells in x direction"
    cell_ny: int = Field(gt=0, default=9)
    "Number of grid cells in y direction"
    xoff: float = -45.0
    "The x offset of the grid origin"
    yoff: float = -45.0
    "The x offset of the grid origin"


class TimingConfig(Configuration):
    """Timing configuration."""

    start_date: date = date(2013, 1, 1)
    "Simulation start date"
    update_interval: str = "1 month"
    "Interval at which all models are updated"
    run_length: str = "2 years"
    "How long the simulation should be run for"


class DataOutput(Configuration):
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


class Layers(Configuration):
    """Settings for the simulation vertical structure."""

    soil_layers: list[float] = Field(min_length=1, default=[-0.25, -1.0])
    """Depth and number of soil layers to simulate
    TODO: unique items only
    """
    canopy_layers: int = Field(gt=0, default=10)
    "Maximum number of canopy layers to simulate"
    above_canopy_height_offset: float = Field(gt=0, default=2.0)
    "The height offset relative to the canopy top for climatic reference variables."
    surface_layer_height: float = Field(gt=0, default=0.1)
    ("The height used to calculate ground surface microclimate conditions.",)
    subcanopy_layer_height: float = Field(gt=0, default=1.5)
    "The height used to calculate subcanopy microclimate conditions."


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
    "Constants for the core module"
    grid: GridConfig = GridConfig()
    "Details of the grid to configure"
    data_output_options: DataOutput = DataOutput()
    "Options for output the Virtual Ecosystem model state"
    layers: Layers = Layers()
    "Layers to create vertical structure"
    data: Variables = Variables()
