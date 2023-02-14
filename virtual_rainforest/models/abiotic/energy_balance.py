"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest. The basic
assumption of this approach is that below-canopy heat and vapor exchange attain steady
state, and that temperatures and soil moisture are determined using energy balance
equations that sum to zero. The approach is based on :cite:t:`MACLEAN2021`; the details
are described here [link to general documentation here].

The module contains the :class:`~virtual_rainforest.models.abiotic.Energy_Balance` class
and associated functions to calculate above and below canopy atmospheric temperature and
humidity profiles, soil temperatures, and radiative fluxes.
"""
# TODO include time dimension, i.e. initialise vertical profile and update other
# variables for each time step with inputs from other modules via the data object (for
# example leaf area index from `plants`)

from dataclasses import dataclass

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.base_model import InitialisationError
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER


# In the future, we want to import the EnergyBalanceConstants dataclass here
@dataclass
class EnergyBalanceConstants:
    """Energy balance constants class."""

    leaf_temperature_ini_factor = 0.01
    """Factor used to initialise leaf temperature."""
    soil_division_factor = 2.42
    """Factor defines how to divide soil into layers with increasing thickness,
    alternative value 1.2."""
    min_leaf_conductivity = 0.25
    """Minimum leaf conductivity, typical value for decidious forest with wind above
    canopy 2 m/s."""
    max_leaf_conductivity = 0.32
    """Maximum leaf conductivity, typical value for decidious forest with wind above
    canopy 2 m/s :cite:p:`MACLEAN2021`."""
    air_conductivity = 50.0
    """Initial air conductivity, typical value for decidious forest with wind above
    canopy 2 m/s :cite:p:`MACLEAN2021`."""
    min_leaf_air_conductivity = 0.13
    """Minimum conductivity between leaf and air, typical value for decidious forest
    with wind above canopy 2 m/s :cite:p:`MACLEAN2021`."""
    max_leaf_air_conductivity = 0.19
    """Maximum conductivity between leaf and air, typical value for decidious forest
    with wind above canopy 2 m/s :cite:p:`MACLEAN2021`."""
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
    """EnergyBalance class.

    **General description of what happens in the class...**

    This class generates a set of initial microclimate and conductivities using a given
    interpolation method (default 'linear') and populates the following attributes of a
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
    * leaf_area_index: leaf area index, [m m-1]
    * canopy_height: canopy height, [m]
    * absorbed_radiation: shortwave radiation absorbed by each canopy layer, [J m-2]

    2. from radiation:
    * topofcanopy_radiation: top of canopy radiation shortwave radiation, [J m-2]

    3. from wind:
    * wind_above_canopy: wind profile above canopy, [m s-1]
    * wind_below_canopy: wind profile below canopy, [m s-1]

    4. from soil:
    * soil_type: soil type (proportion of sand, clay)
    * soil_parameters: dictionnary of soil parameters (list and link to more info)
    * soil_depth: depth of deepest soil layer, [m]

    The ``const`` argument takes an instance of class
    :class:`~virtual_rainforest.models.abiotic.energy_balance.EnergyBalanceConstants`,
    which provides a user modifiable set of required constants.

    `run_energy_balance()` funds the full energy balance per grid cell which updates
    attributes of :class:`~virtual_rainforest.models.abiotic.Energy_Balance` class which
    will be used to update the :class:`~virtual_rainforest.core.data.Data` object.

    Args:
        data: A Virtual Rainforest Data object.
        const: A EnergieBalanceConstants instance.
        soil_layers: number of soil layers, currently constant
        canopy_layers: number of canopy layers, currently constant
        interpolation_method: method to interpolate air and soil temperature profile
            default = 'linear'
    """

    def __init__(
        self,
        data: Data,
        const: EnergyBalanceConstants = EnergyBalanceConstants(),
        soil_layers: int = 2,  # will come from config
        canopy_layers: int = 3,  # will come from config
        interpolation_method: str = "linear",
    ) -> None:
        """Initializes point-based energy balance method."""

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
        self.absorbed_radiation = calculate_initial_absorbed_radiation(
            topofcanopy_radiation=data["topofcanopy_radiation"],
            leaf_area_index=data["leaf_area_index"],
        )

        # interpolate initial temperature profile
        self.air_temperature = temperature_interpolation(
            temperature_top=data["air_temperature_2m"],
            temperature_bottom=data["mean_annual_temperature"],
            canopy_layers=canopy_layers,
            soil_layers=soil_layers,
            option=interpolation_method,
        )[int(soil_layers) :]

        self.soil_temperature = temperature_interpolation(
            temperature_top=data["air_temperature_2m"],
            temperature_bottom=data["mean_annual_temperature"],
            canopy_layers=canopy_layers,
            soil_layers=soil_layers,
            option=interpolation_method,
        )[soil_layers - 1 :: -1]

        self.canopy_temperature = calc_initial_canopy_temperature(
            air_temperature=data["air_temperature_2m"],
            leaf_temperature_ini_factor=const.leaf_temperature_ini_factor,
            absorbed_radiation=data["absorbed_radiation"],
        )

        # initiate relative humidity and atmospheric pressure
        self.relative_humidity = np.repeat(data["relative_humidity_2m"], canopy_layers)
        self.atmospheric_pressure = data["atmospheric_pressure_2m"]

        # set initial conductivities
        self.air_conductivity = (
            np.repeat(const.air_conductivity, canopy_layers + 1)
            * (canopy_layers / data["canopy_height"])
            * (2 / canopy_layers)
        )

        self.air_conductivity[0] = 2 * self.air_conductivity[0]
        self.air_conductivity[canopy_layers] = (
            self.air_conductivity[canopy_layers]
            * (data["canopy_height"] / canopy_layers)
            * 0.5
        )

        self.leaf_conductivity = temp_conductivity_interpolation(
            const.min_leaf_conductivity,
            const.max_leaf_conductivity,
            option=interpolation_method,
        )

        self.air_leaf_conductivity = temp_conductivity_interpolation(
            const.min_leaf_air_conductivity,
            const.max_leaf_air_conductivity,
            option=interpolation_method,
        )

        # set initial heights
        self.canopy_node_heights = (
            (np.arange(canopy_layers) + 0.5) / canopy_layers * data["canopy_height"]
        )

        self.soil_node_depths = np.array(
            soil_depth
            / (float(soil_layers) ** const.soil_division_factor)
            * (x**const.soil_division_factor)
            for x in range(1, soil_layers + 1)
        )

        self.height_of_above_canopy = data["canopy_height"]

        self.canopy_wind_speed = np.array(
            (np.arange(canopy_layers) + 1) / canopy_layers * data["wind_speed_10m"]
        )

        # set initial fluxes TODO set correct dimensions
        self.sensible_heat_flux = DataArray(
            [np.zeros()], dims=["canopy_layers", "cell_id"]
        )
        self.latent_heat_flux = DataArray(
            [np.zeros()], dims=["canopy_layers", "cell_id"]
        )
        self.ground_heat_flux = DataArray([np.zeros()], dims=["cell_id"])
        self.diabatic_correction_factor = DataArray([np.zeros()], dims=["cell_id"])

    def run_energy_balance(self) -> None:
        """Calculate full energy balance for one time step."""
        raise NotImplementedError


# pure functions
def calculate_initial_absorbed_radiation(
    topofcanopy_radiation: DataArray,
    leaf_area_index: DataArray,
    canopy_layers: int = 3,
    light_extinction_coefficient: float = (
        EnergyBalanceConstants.light_extinction_coefficient
    ),
) -> DataArray:
    """Calculate initial light absorption profile.

    This function calculates the initial absorbed shortwave radiation for each canopy
    layer. The calculation is based on Beer's law: ...

    Args:
        topofcanopy_radiation: topofcanopy_radiation: top of canopy radiation shortwave
            radiation, [J m-2]
        leaf_area_index: leaf area index of each canopy layer, [m m-1]
        canopy_layers: number of canopy layers
        light_extinction_coefficient: light extinction coefficient, [m-1]

    Returns:
        shortwave radiation absorbed by canopy layers, [J m-2]
    """

    initial_absorbed_radiation = DataArray(
        np.zeros([3, 2]), dims=["canopy_layers", "cell_id"]  # generalise dimensions
    )

    for i in range(0, canopy_layers):
        initial_absorbed_radiation[i,] = topofcanopy_radiation * (
            1 - np.exp(-light_extinction_coefficient * leaf_area_index[i,])
        )
        topofcanopy_radiation = topofcanopy_radiation - initial_absorbed_radiation[i,]

    return initial_absorbed_radiation


def temperature_interpolation(
    temperature_top: DataArray,
    temperature_bottom: DataArray,
    canopy_layers: int = 3,
    soil_layers: int = 2,
    option: str = "linear",
) -> DataArray:
    """Interpolation of initial temperature profile.

    This function creates a vertical temperature profile by interpolating between a
    reference air temperature and the temperature of the lowest soil layer, which is
    typically the mean annual temperature. ideally, this would use cubic spline
    interpolation, at the moment only linear interpolation is implemented.

    Args:
        temperature_top: reference air temperature, [K]
        temperature_bottom: temperature of the lowest layer, [K]
        option: interpolation method

    Returns:
        vertical temperature profile of length canopy_layers+1

    Options:
        linear (default)
    """

    if option == "linear":
        temperature_profile: DataArray = np.linspace(
            temperature_bottom, temperature_top, canopy_layers + soil_layers
        )

    else:
        NotImplementedError("This interpolation method is not available.")

    return temperature_profile


def temp_conductivity_interpolation(
    min_conductivity: float,
    max_conductivity: float,
    canopy_layers: float = 3,
    option: str = "linear",
) -> DataArray:
    """Interpolation of initial temperature conductivity profile.

    Args:
        min_conductivity
        max_conductivity
        canopy_layers: number of canopy layers
        option: interpolation mothod, default = 'linear

    Returns:
        vertical profile of conductivities

    Options:
        linear (default)
    """
    if option == "linear":
        temp_conductivity_profile = np.linspace(
            min_conductivity,  # need to be an array
            max_conductivity,
            canopy_layers,
        )
    else:
        NotImplementedError("This interpolation method is not available.")

    return temp_conductivity_profile


def calc_initial_canopy_temperature(
    air_temperature: DataArray,
    absorbed_radiation: DataArray,
    leaf_temperature_ini_factor=EnergyBalanceConstants.leaf_temperature_ini_factor,
) -> DataArray:
    """Calculate initial canopy temperature.

    Args:
        air_temperature: reference air temperature?
        absorbed_radiation:
        leaf_temperature_ini_factor

    Returns:
        initial vertical canopy temperature profile
    """

    return air_temperature + leaf_temperature_ini_factor * absorbed_radiation

    # def update_canopy(
    #    self,
    #    canopy_height: NDArray[np.float32],
    #    leaf_area_index: NDArray[np.float32],
    #    absorbed_radiation: NDArray[np.float32],
    # ) -> None:
    #    """Update canopy height, leaf area index and absorption at each time step."""
    #    self.latent_heat_flux = leaf_area_index
    #    self.canopy_height = canopy_height
    #    self.absorbed_radiation = absorbed_radiation

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


# not used small functions
def calc_molar_density_air(
    temperature: DataArray,
    atmospheric_pressure: DataArray,
    celsius_to_kelvin: float = EnergyBalanceConstants.celsius_to_kelvin,
    standard_mole: float = EnergyBalanceConstants.standard_mole,
) -> DataArray:
    """Calculate temperature-dependent molar density of air.

    Args:
        temperature
        atmospheric_pressure

    Returns:
        molar_density_air
    """
    temperature_kelvin = temperature + celsius_to_kelvin
    molar_density_air = (
        standard_mole
        * (temperature_kelvin / atmospheric_pressure)
        * (celsius_to_kelvin / temperature_kelvin)
    )
    return molar_density_air


def calc_specific_heat_air(
    temperature: DataArray,
    molar_heat_capacity_air: float = EnergyBalanceConstants.molar_heat_capacity_air,
) -> DataArray:
    """Calculate molar temperature-dependent specific heat of air.

    Args:
        temperature

    Returns:
        specific heat of air at constant pressure (J mol-1 K-1)

    Reference:
            Maclean et al, 2021: Microclimc: A mechanistic model of above, below and
            within-canopy microclimate. Ecological Modelling Volume 451, 109567.
            https://doi.org/10.1016/j.ecolmodel.2021.109567.

    TODO identify remaining constants
    """
    return 2e-05 * temperature**2 + 0.0002 * temperature + molar_heat_capacity_air


def calc_latent_heat_of_vaporisation(
    temperature: DataArray,
) -> DataArray:
    """Calculate latent heat of vaporisation.

    Args:
        temperature, [K]

    Returns:
        Latent heat of vaporisation [J mol-1]

    Reference:
        Maclean et al, 2021: Microclimc: A mechanistic model of above, below and
        within-canopy microclimate. Ecological Modelling Volume 451, 109567.
        https://doi.org/10.1016/j.ecolmodel.2021.109567.

    TODO identify remaining constants
    """
    return -42.575 * temperature + 44994
