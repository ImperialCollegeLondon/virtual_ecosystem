"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest. The basic
assumption of this approach is that below-canopy heat and vapor exchange attain steady
state, and that temperatures and soil moisture are determined using energy balance
equations that sum to zero. The approach is based on :cite:t:`MACLEAN2021`; the details
are described here [link to general documentation here].

In summary, the submodule contains the
:class:`~virtual_rainforest.models.abiotic.Energy_Balance` class and associated
functions to calculate above and below canopy atmospheric temperature and humidity
profiles, soil temperatures, and radiative fluxes.
"""

from dataclasses import dataclass

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.base_model import InitialisationError


@dataclass
class EnergyBalanceConstants:
    """Energy balance constants class."""

    leaf_temperature_ini_factor = 0.01
    """Factor used to initialise leaf temperature."""
    soil_division_factor = 2.42
    """Factor defines how to divide soil into layers with increasing thickness,
    alternative value 1.2."""
    min_leaf_conductivuty = 0.25
    """Minimum leaf conductivity, typical value for decidious forest with wind above
    canopy 2 m/s."""
    max_leaf_conductivity = 0.32
    """Maximum leaf conductivity, typical value for decidious forest with wind above
    canopy 2 m/s."""  # add reference
    ait_conductivity = 50.0
    """Initial air conductivity, typical value for decidious forest with wind above
    canopy 2 m/s."""  # add reference
    min_leaf_air_conductivity = 0.13
    """Minimum conductivity between leaf and air, typical value for decidious forest
    with wind above canopy 2 m/s."""  # add reference
    max_leaf_air_conductivity = 0.19
    """Maximum conductivity between leaf and air, typical value for decidious forest
    with wind above canopy 2 m/s."""  # add reference
    karmans_constant = 0.4
    """Constant to calculate mixing length."""
    celsius_to_kelvin = 273.15
    """Factor to convert temperature in Celsius to absolute temperature in Kelvin."""
    standard_mole = 44.6
    """Moles of ideal gas in 1 m3 air at standard atmosphere."""
    molar_heat_capacity_air = 29.19
    """Molar heat capacity of air [J mol-1 C-1]."""
    vapor_pressure_factor1 = 0.6108
    """Constant in calculation of vapor pressure."""
    vapor_pressure_factor2 = 17.27
    """Constant in calculation of vapor pressure."""
    vapor_pressure_factor3 = 237.7
    """Constant in calculation of vapor pressure."""
    light_extinction_coefficient = 0.01
    """Default light extinction coefficient for canopy."""


class EnergyBalance:
    """EnergyBalance method."""

    def __init__(
        self,
        data: Data,
        const: EnergyBalanceConstants = EnergyBalanceConstants(),
        soil_layers: int = 2,  # will come from config
        canopy_layers: int = 3,  # will come from config
        interpolation_method: str = 'linear',
    ) -> None:
        """Initializes point-based energy balance method.

        This function generates a set of initial climate, conductivities, and soil
        parameters and populates the following attributes of a
        :class:`~virtual_rainforest.models.abiotic.Energy_Balance` instance for running
        the first time step of the energy balance:

        * air_temperature, soil_temperature, canopy_temperature, [C]
        * relative_humidity, [%]; atmospheric_pressure, [kPa],
        * air_conductivity, leaf_conductivity, air_leaf_conductivity,
        * canopy_node_heights, soil_node_depths, height_of_above_canopy, [m]
        * canopy_wind_speed, [m s-1]
        * sensible/latent/ground heat flux, [J m-2]
        * adiabatic correction factor, [-]

       Creating an instance of this class expects a
        :class:`~virtual_rainforest.core.data.Data` object that contains the following
        variables:

        1. from plants:
        * leaf_area_index: DataArray(dims=['cell_id'])
        * canopy_height: DataArray(dims=['cell_id'])
        * absorbed_radiation: DataArray(dims=['canopy_layers', 'cell_id'])

        2. from radiation:
        * topofcanopy_radiation: DataArray(dims=['cell_id'])

        3. from wind:
        * wind_above_canopy: DataArray(dims=['cell_id'])
        * wind_below_canopy: DataArray(dims=['canopy_layers', 'cell_id'])

        4. from soil:
        * soil_type: DataArray(dims=['cell_id'])
        * soil_parameters: DataArray(dims=['cell_id'])
        * soil_depth: DataArray(dims=['cell_id'])

        Args:
            data: A Virtual Rainforest Data object.
            const: A EnergieBalanceConstants instance.
            soil_layers: number of soil layers, currently constant
            canopy_layers: number of canopy layers, currently constant
            interpolation_method: method to interpolate air and soil temperature profile
                default = 'linear'
    
        """

        # Initialise attributes
        self.soil_temperature: DataArray
        """Vertical profile of soil temperatures [C]."""
        self.air_temperature: DataArray
        """Vertical profile of atmospheric temperatures [C]."""
        self.canopy_temperature: DataArray
        """Vertical profile of canopy temperatures [C]."""
        self.relative_humidity: DataArray
        """Vertical profile of atmospheric relative humidity [%]."""
        self.atmospheric_pressure: DataArray
        """Atmospheric pressure [kPa]"""
        self.air_conductivity: DataArray
        """Vertical profile of air conductivities [mol m-2 s-1]"""
        self.leaf_conductivity: DataArray
        """Vertical profile of leaf conductivities [mol m-2 s-1]"""
        self.air_leaf_conductivity: DataArray
        """Vertical profile of air-leaf conductivities [mol m-2 s-1]"""
        self.canopy_node_heights: DataArray
        """Canopy node heights [m]"""
        self.soil_node_depths: DataArray
        """Soil node depths [m]"""
        self.height_of_above_canopy: DataArray
        """Height defined as 'height above canopy' [m]"""
        self.canopy_wind_speed: DataArray
        """Vertical profile of canopy wind speed [m s-1]"""
        self.sensible_heat_flux: DataArray
        """Sensible Heat flux [J m-2]"""
        self.latent_heat_flux: DataArray
        """Latent Heat flux [J m-2]"""
        self.ground_heat_flux: DataArray
        """Ground Heat flux [J m-2]"""
        self.diabatic_correction_factor: DataArray
        """Diabatic correction factor [-]"""

    # The following could later move to AbioticModel ini step
    # check that leaf area index has correct number of layers
        if len(data["leaf_area_index"]) != canopy_layers:
            to_raise = InitialisationError(
                "Dimension mismatch for initial leaf area index and canopy layers!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # set initial absorbed radiation
        self.absorbed_radiation = calc_initial_absorbed_radiation(
            topofcanopy_radiation=data["topofcanopy_radiation"],
            leaf_area_index=data["leaf_area_index"],
        )

        # interpolate initial temperature profile
        self.air_temperature = temperature_interpolation(
            temperature_top = data["air_temperature_2m"],
            temperature_bottom= data["mean_annual_temperature"],
            canopy_layers = canopy_layers,
            soil_layers = soil_layers,
            option = interpolation_method,
        )[int(soil_layers) :]

        self.soil_temperature = temperature_interpolation(
            temperature_top = data["air_temperature_2m"],
            temperature_bottom= data["mean_annual_temperature"],
            canopy_layers = canopy_layers,
            soil_layers = soil_layers,
            option = interpolation_method,
        )[int(self.soil_layers) - 1 :: -1]

        self.canopy_temperature = calc_initial_canopy_temperature(
            air_temperature = data["air_temperature_2m"],
            leaf_temperature_ini_factor = const.leaf_temperature_ini_factor,
            absorbed_radiation = data["absorbed_radiation"]
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
        self.canopy_node_heights = (
            (np.arange(self.canopy_layers) + 0.5)
            / self.canopy_layers
            * self.canopy_height
        )

        self.soil_node_depths = np.array(
            self.soil_depth
            / (float(self.soil_layers) ** C.SOIL_DIVISION_FACTOR)
            * (x**C.SOIL_DIVISION_FACTOR)
            for x in range(1, self.soil_layers + 1)
        )

        self.height_of_above_canopy = self.canopy_height

        self.canopy_wind_speed = np.array(
            (np.arange(self.canopy_layers) + 1)
            / self.canopy_layers
            * self.data_t["wind_speed_10m"]
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
    temperature_top: Data,
    temperature_bottom: DataArray,
    canopy_layers: int = 3,
    soil_layers: int = 2,
    interpolation_option: str = "linear",
) -> DataArray:
    """Interpolation of initial temperature profile.

    Args:
        temperature_top: temperature of the highest layer, [K]
        temperature_bottom: temperature of the lowest layer, [K]
        interpolation_method:

    Returns:
        vertical temperature profile of length canopy_layers+1

    Options:
        linear (default)
    """

    if interpolation_option != "linear":
        NotImplementedError("This interpolation method is not available.")

    else:
        return np.linspace(
            temperature_bottom,
            temperature_top,
            canopy_layers + soil_layers,
        )

def temp_conductivity_interpolation(
    self, min_conductivity: float, max_conductivity: float, option: str = "linear"
) -> DataArray:
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
    topofcanopy_radiation: DataArray,
    leaf_area_index: DataArray,
    canopy_layers: int = 3,
    light_extinction_coefficient: float = EnergyBalanceConstants.light_extinction_coefficient
) -> DataArray:
    """Calculate initial light absorption profile."""

    initial_absorbed_radiation = np.zeros(canopy_layers, dtype=np.float32)

    for i in range(0, canopy_layers - 1):
        initial_absorbed_radiation[i] = topofcanopy_radiation * (
            1 - np.exp(-light_extinction_coefficient * leaf_area_index[i])
        )
        topofcanopy_radiation = (
            topofcanopy_radiation - initial_absorbed_radiation[i]
        )
    return initial_absorbed_radiation

def calc_initial_canopy_temperature(
    air_temperature: DataArray,
    absorbed_radiation: DataArray,
    leaf_temperature_ini_factor = EnergyBalanceConstants.leaf_temperature_ini_factor,
    )-> DataArray:
    """Calculate initial canopy temperature.
    
    Args:
        air_temperature
        absorbed_radiation
        leaf_temperature_ini_factor
        
    Returns:
        initial vertical canopy temperature profile"""
    
    return air_temperature + leaf_temperature_ini_factor * absorbed_radiation







def calc_molar_density_air(
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
    temperature: NDArray[np.float32] = np.array(20.0, dtype=float)
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
