"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest. The basic
assumption of this approach is that below-canopy heat and vapor exchange attain steady
state, and the temperatures and soil moisture are determined using energy balance
equations that sum to zero. The approach is based on Maclean et al, 2021: Microclimc: A
mechanistic model of above, below and within-canopy microclimate. Ecological Modelling
Volume 451, 109567. https://doi.org/10.1016/j.ecolmodel.2021.109567.

Above-canopy temperature, humidity and wind profiles (see wind.py) are calculated using
K-theory with estimates of bulk aerodynamic resistance derived from canopy properties.
Within the canopy, radiation transmission (see radiation.py) and wind profiles are used
to estimate turbulent transfer within the canopy and boundary layer.
Heat balance equations for each canopy layer are then linearized, enabling simultaneous
calculation of leaf and air temperatures. Time-dependant differential equations for each
canopy and soil node are then specified and storage and simultaneous exchanges of heat
and vapor between each layer then computed. The model returns a time-series of
temperature and humidity at user-specified heights or depths.
"""


import dummy_constants as C
import dummy_data as data  # external driving data at reference height/depth
import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.core.logger import log_and_raise
from virtual_rainforest.core.model import InitialisationError

# this will link to other modules, structure to be decided, could be in `data` object
# at the moment 1 cell_id, 3 canopy layers, 2 soil layers
# from plants import leaf_area_index, canopy_height, absorbed_radiation
leaf_area_index = np.ones(3, dtype=np.float32)
canopy_height = np.array(20.0, dtype=np.float32)
absorbed_radiation = np.array(100.0, dtype=np.float32)  # NOT for initialisation

# from radiation import topofcanopy_radiation
topofcanopy_radiation = np.array(350.0, dtype=np.float32)

# from wind import wind_above_canopy, wind_below_canopy
wind_above_canopy = np.array(2.0, dtype=np.float32)
wind_below_canopy = np.ones(3, dtype=np.float32)


class EnergyBalance:
    """EnergyBalance method."""

    def __init__(
        self,
        soil_type: NDArray[np.string_],
        soil_layers: int = 2,  # from config?
        canopy_layers: int = 3,  # from config?
        initial_canopy_height: NDArray[np.float32] = np.array(20.0, dtype=np.float32),
    ) -> None:
        """Initializes point-based energy_balance method.

        This function sets the boundary conditions for the vertical profile and loads
        the soil parameters.
        """

        # set boundary conditions for vertical profile
        self.soil_type = soil_type
        """Soil type"""
        self.soil_parameters = data.soil_parameters[soil_type]
        """Dict of soil type specific soil parameters."""
        self.soil_depth = data.data["soil_depth"]
        """Soil depth [m]"""
        self.soil_layers = soil_layers
        """Number of soil layers. Currently static."""
        self.canopy_layers = canopy_layers
        """Number of canopy layers."""
        self.canopy_height = initial_canopy_height
        """Canopy height [m]"""

        # populated later:
        self.soil_temperature: NDArray[np.float32]
        """Vertical profile of soil temperatures [C]."""
        self.absorbed_radiation: NDArray[np.float32]
        """Radiation absorbed by canopy [W m-2]"""
        self.air_temperature: NDArray[np.float32]
        """Vertical profile of atmospheric temperatures [C]."""
        self.canopy_temperature: NDArray[np.float32]
        """Vertical profile of canopy temperatures [C]."""
        self.relative_humidity: NDArray[np.float32]
        """Vertical profile of atmospheric relative humidity [%]."""
        self.atmospheric_pressure: NDArray[np.float32]
        """Atmospheric pressure [kPa]"""
        self.air_conductivity: NDArray[np.float32]
        """Vertical profile of air conductivities [mol m-2 s-1]"""
        self.leaf_conductivity: NDArray[np.float32]
        """Vertical profile of leaf conductivities [mol m-2 s-1]"""
        self.air_leaf_conductivity: NDArray[np.float32]
        """Vertical profile of air-leaf conductivities [mol m-2 s-1]"""
        self.canopy_node_heights: NDArray[np.float32]
        """Canopy node heights [m]"""
        self.soil_node_depths: NDArray[np.float32]
        """Soil node depths [m]"""
        self.height_of_above_canopy: NDArray[np.float32]
        """Height defined as 'height above canopy' [m]"""
        self.canopy_wind_speed: NDArray[np.float32]
        """Vertical profile of canopy wind speed [m s-1]"""
        self.sensible_heat_flux: NDArray[np.float32]
        """Sensible Heat flux [J m-2]"""
        self.latent_heat_flux: NDArray[np.float32]
        """Latent Heat flux [J m-2]"""
        self.ground_heat_flux: NDArray[np.float32]
        """Ground Heat flux [J m-2]"""
        self.diabatic_correction_factor: NDArray[np.float32]
        """Diabatic correction factor [-]"""

    def initialise_vertical_profile(  # this could later move to AbioticModel ini step
        self,
        leaf_area_index: NDArray[np.float32],
        topofcanopy_radiation: NDArray[np.float32],
        interpolation_method: str = "linear",
    ) -> None:
        """Generates a set of initial climate, conductivity, and soil parameters.

        This function populates the following attributes for running the first time step
        of the energy balance:
        * data_t (climate input data at current time step),
        * absorbed_radiation (after the first time step, this is an input from the plant
            module), [J m-2]
        * air_temperature, soil_temperature, canopy_temperature, [C]
        * relative_humidity, [%]; atmospheric_pressure, [kPa],
        * air_conductivity, leaf_conductivity, air_leaf_conductivity,
        * canopy_node_heights, soil_node_depths, height_of_above_canopy, [m]
        * canopy_wind_speed, [m s-1]
        * sensible/latent/ground heat flux, [J m-2]
        * adiabatic correction factor, [-]

        Args:
            leaf_area_index: Leaf area index [m m-1]
            topofcanopy_radiation: top of canopy shortwave downward radiation [J m-2]
            interpolation_method: method to interpolate air and soil temperature profile
                default = 'linear'
        """

        # select first timestep in data set
        self.data_t = data.data["time_1"]

        # check that leaf area index has correct number of layers
        if len(leaf_area_index) != self.canopy_layers:
            log_and_raise(
                "Dimension mismatch for initial leaf area index and canopy layers!",
                InitialisationError,
            )

        # set initial absorbed radiation
        self.absorbed_radiation = self.calc_initial_absorbed_radiation(
            leaf_area_index, topofcanopy_radiation
        )

        # interpolate initial temperature profile
        self.air_temperature = self.temperature_interpolation(
            data=self.data_t, option=interpolation_method
        )[(int(self.soil_layers)) : int((self.canopy_layers + self.soil_layers))]

        self.soil_temperature = self.temperature_interpolation(
            data=self.data_t, option=interpolation_method
        )[0 : int(self.soil_layers)][::-1]

        self.canopy_temperature = (
            self.air_temperature
            + C.LEAF_TEMPERATURE_INI_FACTOR * self.absorbed_radiation
        )

        # initiate relative humidity and atmospheric pressure
        self.relative_humidity = np.repeat(
            self.data_t["relative_humidity_2m"], self.canopy_layers
        )
        self.atmospheric_pressure = self.data_t["atmospheric_pressure_2m"]

        # set initial conductivities
        self.air_conductivity = (
            np.repeat(C.AIR_CONDUCTIVITY, self.canopy_layers + 1)
            * (self.canopy_layers / self.canopy_height)
            * (2 / self.canopy_layers)
        )

        self.air_conductivity[0] = 2 * self.air_conductivity[0]
        self.air_conductivity[self.canopy_layers] = (
            self.air_conductivity[self.canopy_layers]
            * (self.canopy_height / self.canopy_layers)
            * 0.5
        )

        self.leaf_conductivity = self.temp_conductivity_interpolation(
            C.MIN_LEAF_CONDUCTIVITY,
            C.MAX_LEAF_CONDUCTIVITY,
            option=interpolation_method,
        )

        self.air_leaf_conductivity = self.temp_conductivity_interpolation(
            C.MIN_LEAF_AIR_CONDUCTIVITY,
            C.MAX_LEAF_AIR_CONDUCTIVITY,
            option=interpolation_method,
        )

        # set initial heights
        self.canopy_node_heights = np.array(
            (x + 0.5) / self.canopy_layers * self.canopy_height
            for x in range(0, self.canopy_layers)
        )

        self.soil_node_depths = np.array(
            self.soil_depth
            / (float(self.soil_layers) ** C.SOIL_DIVISION_FACTOR)
            * (x**C.SOIL_DIVISION_FACTOR)
            for x in range(1, self.soil_layers + 1)
        )

        self.height_of_above_canopy = self.canopy_height

        self.canopy_wind_speed = np.array(
            (x / self.canopy_layers) * self.data_t["wind_speed_10m"]
            for x in range(1, self.canopy_layers + 1)
        )

        # set initial fluxes
        self.sensible_heat_flux = np.array(0.0, dtype=np.float32)
        self.latent_heat_flux = np.zeros(self.canopy_layers, dtype=np.float32)
        self.ground_heat_flux = np.array(0.0, dtype=np.float32)
        self.diabatic_correction_factor = np.array(0.0, dtype=np.float32)

    def calc_energy_balance(self) -> None:
        """Calculate full energy balance for one time step."""
        raise NotImplementedError

    def update_canopy(
        self,
        canopy_height: NDArray[np.float32],
        leaf_area_index: NDArray[np.float32],
        absorbed_radiation: NDArray[np.float32],
    ) -> None:
        """Update canopy height, leaf area index and absorption at each time step."""
        self.canopy_height = canopy_height
        self.latent_heat_flux = leaf_area_index
        self.absorbed_radiation = absorbed_radiation

    def calc_temperature_above_canopy(args) -> None:
        """Calculates temperature above canopy based on logarithmic height profile."""
        raise NotImplementedError

    def calc_humidity_above_canopy(args) -> None:
        """Calculates humidity above canopy based on logarithmic height profile."""
        raise NotImplementedError

    def calc_diabatic_correction(args) -> None:
        """Calculates diabatic correction factor."""
        raise NotImplementedError

    def calc_topofcanopy_conductivity(args) -> None:
        """Calculate conductivity to top of canopy and merge."""
        raise NotImplementedError

    def calc_vapor_conductivity(args) -> None:
        """Calculate vapor conductivity."""
        raise NotImplementedError

    def calc_leaf_conductivity(args) -> None:
        """Calculate leaf conductivity."""
        raise NotImplementedError

    def calc_soil_conductivity(args) -> None:
        """Calculate soil conductivity."""
        raise NotImplementedError

    def calc_soil_specific_heat(args) -> None:
        """Calculate soil specific_heat."""
        raise NotImplementedError

    def calc_soil_heat_flux(args) -> None:
        """Calculate soil heat flux."""
        raise NotImplementedError

    def calc_soil_temperature(args) -> None:
        """Calculate soil temperature."""
        raise NotImplementedError

    def calc_sensible_heat_flux(args) -> None:
        """Calculate sensible heat flux."""
        raise NotImplementedError

    def calc_latent_heat_flux(args) -> None:
        """Calculate latent heat flux."""
        raise NotImplementedError

    def calc_canopy_temperature(args) -> None:
        """Calculates canopy temperature from rad. fluxes and reference temperatures."""
        raise NotImplementedError

    def calc_temperature_mixing(args) -> None:
        """Solves simultanious heat fluxes between soil and air layers."""
        raise NotImplementedError

    def calc_vapor_mixing(args) -> None:
        """Solves simultanious vapor fluxes between air layers."""
        raise NotImplementedError

    # small functions
    def temperature_interpolation(
        self, data: dict, option: str = "linear"
    ) -> NDArray[np.float32]:
        """Interpolation of initial temperature profile.

        Options:
            linear (default)
        """
        if option == "linear":
            temperature_interpolation = np.linspace(
                data["mean_annual_temperature"],
                data["air_temperature_2m"],
                self.canopy_layers + self.soil_layers,
            )
        else:
            NotImplementedError("This interpolation method is not available.")

        return temperature_interpolation

    def temp_conductivity_interpolation(
        self, min_conductivity: float, max_conductivity: float, option: str = "linear"
    ) -> NDArray[np.float32]:
        """Interpolation of initial temperature conductivity profile.

        Options:
            linear (default)
        """
        if option == "linear":
            temp_conductivity_interpolation = np.linspace(
                np.array(min_conductivity),
                np.array(max_conductivity),
                self.canopy_layers,
            )
        else:
            NotImplementedError("This interpolation method is not available.")

        return temp_conductivity_interpolation

    def calc_initial_absorbed_radiation(
        self,
        topofcanopy_radiation: NDArray[np.float32],
        leaf_area_index: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """Calculate initial light absorption profile."""

        initial_absorbed_radiation = np.zeros(self.canopy_layers, dtype=np.float32)
        initial_absorbed_radiation[0] = topofcanopy_radiation * (
            1 - np.exp(-C.LIGHT_EXCTINCTION_COEFFICIENT * leaf_area_index[0])
        )
        topofcanopy_radiation = topofcanopy_radiation - initial_absorbed_radiation[0]

        for i in range(1, self.canopy_layers - 1):
            initial_absorbed_radiation[i] = topofcanopy_radiation * (
                1 - np.exp(-C.LIGHT_EXCTINCTION_COEFFICIENT * leaf_area_index[i])
            )
            topofcanopy_radiation = (
                topofcanopy_radiation - initial_absorbed_radiation[i]
            )
        return initial_absorbed_radiation

    def calc_molar_density_air(
        self,
        temperature: NDArray[np.float32] = np.array(20.0, dtype=np.float32),
        atmospheric_pressure: NDArray[np.float32] = np.array(101.3, dtype=np.float32),
    ) -> NDArray[np.float32]:
        """Calculate temperature-dependent molar density of air.

        Args:
            temperature
            atmospheric_pressure

        Returns:
            molar_density_air
        """
        temperature_kelvin = temperature + C.CELSIUS_TO_KELVIN
        molar_density_air = (
            C.STANDARD_MOLE
            * (temperature_kelvin / atmospheric_pressure)
            * (C.CELSIUS_TO_KELVIN / temperature_kelvin)
        )
        return molar_density_air

    def calc_specific_heat_air(
        self, temperature: NDArray[np.float32] = np.array(20.0, dtype=float)
    ) -> NDArray[np.float32]:
        """Calculate molar temperature-dependent specific heat of air.

        Args:
            temperature

        Returns:
            specific_heat_air, specific heat of air at constant pressure (J mol-1 K-1)

        Reference:
            Maclean et al, 2021: Microclimc: A mechanistic model of above, below and
            within-canopy microclimate. Ecological Modelling Volume 451, 109567.
            https://doi.org/10.1016/j.ecolmodel.2021.109567.

        TODO identify remaining constants
        """
        return (
            2e-05 * temperature**2 + 0.0002 * temperature + C.MOLAR_HEAT_CAPACITY_AIR
        )

    def calc_latent_heat_of_vaporisation(
        self, temperature: NDArray[np.float32] = np.array(20.0, dtype=float)
    ) -> NDArray[np.float32]:
        """Calculate latent heat of vaporisation.

        Args:
            temperature

        Returns:
            Latent heat of vaporisation [J mol-1]

        Reference:
            Maclean et al, 2021: Microclimc: A mechanistic model of above, below and
            within-canopy microclimate. Ecological Modelling Volume 451, 109567.
            https://doi.org/10.1016/j.ecolmodel.2021.109567.

        TODO identify remaining constants
        """
        return -42.575 * temperature + 44994
