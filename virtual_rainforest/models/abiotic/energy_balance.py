"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest. The basic
assumption of this approach is that below-canopy heat and vapor exchange attain steady
state, and that temperatures and soil moisture are determined using energy balance
equations that sum to zero. The approach is based on :cite:t:`MACLEAN2021`; the details
are described here [link to general documentation will follow here].

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

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.model import InitialisationError  # change to base_model


# In the future, we want to import the EnergyBalanceConstants dataclass here
@dataclass
class EnergyBalanceConstants:
    """Energy balance constants class."""

    leaf_temperature_ini_factor = 0.01
    """Factor used to initialise leaf temperature."""
    soil_division_factor = 2.42
    """Factor defines how to divide soil into layers with increasing thickness,
    alternative value 1.2 :cite:p:`MACLEAN2021`."""
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

    * leaf_area_index: leaf area index, [m m-1]
    * canopy_height: canopy height, [m]
    * absorbed_radiation: shortwave radiation absorbed by each canopy layer, [J m-2]
    * topofcanopy_radiation: top of canopy radiation shortwave radiation, [J m-2]
    * wind_above_canopy: wind profile above canopy, [m s-1]
    * wind_below_canopy: wind profile below canopy, [m s-1]
    * soil_type: soil type (proportion of sand, clay)
    * soil_parameters: dictionnary of soil parameters (list and link to more info)
    * soil_depth: depth of deepest soil layer, [m]

    The ``const`` argument takes an instance of class
    :class:`~virtual_rainforest.models.abiotic.energy_balance.EnergyBalanceConstants`,
    which provides a user modifiable set of required constants.

    `run_energy_balance()` runs the full energy balance per grid cell which updates
    attributes of :class:`~virtual_rainforest.models.abiotic.Energy_Balance` class. This
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
        self.absorbed_radiation = initialise_absorbed_radiation(
            topofcanopy_radiation=data["topofcanopy_radiation"],
            leaf_area_index=data["leaf_area_index"],
        )

        # interpolate initial temperature profile
        temperature_profile = temperature_interpolation(
            temperature_top=data["air_temperature_2m"],
            temperature_bottom=data["mean_annual_temperature"],
            canopy_layers=canopy_layers,
            soil_layers=soil_layers,
            option=interpolation_method,
        )
        self.air_temperature = temperature_profile[int(soil_layers) :]  # test

        self.soil_temperature = temperature_profile[soil_layers - 1 :: -1]

        self.canopy_temperature = initialise_canopy_temperature(
            air_temperature=data["air_temperature_2m"],
            leaf_temperature_ini_factor=const.leaf_temperature_ini_factor,
            absorbed_radiation=data["absorbed_radiation"],
        )

        # initiate relative humidity and atmospheric pressure
        self.relative_humidity = DataArray(
            [np.repeat(data["relative_humidity_2m"], canopy_layers)]
        )
        self.atmospheric_pressure = data["atmospheric_pressure_2m"]

        # set initial conductivities
        self.air_conductivity = initialise_air_temperature_conductivity(
            canopy_height=data["canopy_height"],
            canopy_layers=canopy_layers,
            air_conductivity=const.air_conductivity,
        )

        self.leaf_conductivity = temperature_conductivity_interpolation(
            const.min_leaf_conductivity,
            const.max_leaf_conductivity,
            option=interpolation_method,
        )

        self.air_leaf_conductivity = temperature_conductivity_interpolation(
            const.min_leaf_air_conductivity,
            const.max_leaf_air_conductivity,
            option=interpolation_method,
        )

        # set initial heights
        self.canopy_node_heights = set_canopy_node_heights(
            canopy_height=data["canopy_height"],
            canopy_layers=canopy_layers,
        )

        self.soil_node_depths = set_soil_node_depths(
            soil_depth=data["soil_depth"],
            soil_layers=soil_layers,
            soil_division_factor=const.soil_division_factor,
        )

        self.height_of_above_canopy = data["canopy_height"]

        # the wind component will likely move to a separate submodule
        self.canopy_wind_speed = set_initial_canopy_windspeed(
            wind_speed_10m=data["wind_speed_10m"],
            canopy_layers=canopy_layers,
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
def initialise_absorbed_radiation(
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
            1
            - np.exp(
                -light_extinction_coefficient
                * leaf_area_index[
                    i,
                ]
            )
        )
        topofcanopy_radiation = (
            topofcanopy_radiation
            - initial_absorbed_radiation[
                i,
            ]
        )

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
        vertical temperature profile of length canopy_layers+soil layers

    Options:
        linear (default)
    """

    if option == "linear":
        temperature_profile: DataArray = DataArray(
            [
                np.linspace(
                    temperature_bottom, temperature_top, canopy_layers + soil_layers
                )
            ]
        )

    else:
        NotImplementedError("This interpolation method is not available.")

    return temperature_profile


def initialise_canopy_temperature(
    air_temperature: DataArray,
    absorbed_radiation: DataArray,
    leaf_temperature_ini_factor: float = (
        EnergyBalanceConstants.leaf_temperature_ini_factor
    ),
) -> DataArray:
    """Calculate initial canopy temperature.

    Args:
        air_temperature: reference air temperature?
        absorbed_radiation: shortwave radiation absorbed by each canopy layer, [J m-2]
        leaf_temperature_ini_factor: factor used to initialise leaf temperature

    Returns:
        initial vertical canopy temperature profile
    """

    return (
        air_temperature + leaf_temperature_ini_factor * absorbed_radiation
    ).transpose()


def initialise_air_temperature_conductivity(
    canopy_height: DataArray,
    canopy_layers: int = 3,
    air_conductivity: float = EnergyBalanceConstants.air_conductivity,
) -> DataArray:
    """Calculate initial air conductivity profile.

    Args:
        canopy_height: canopy height, [m]
        canopy_layers: number of canopy layers
        air_conductivity: Initial air conductivity, default = 50.0; typical value for
            decidious forest with wind above canopy 2 m/s :cite:p:`MACLEAN2021`.

    Returns:
        initial air conductivity profile
    """

    air_conductivity_ini = (
        air_conductivity * (canopy_layers / canopy_height) * (2 / canopy_layers)
    )
    air_conductivity_profile = DataArray(
        np.full((canopy_layers + 1, int(canopy_height.size)), air_conductivity_ini),
        dims=["canopy_layers", "cell_id"],
    )
    air_conductivity_profile[0,] = (
        air_conductivity_ini * 2
    )
    air_conductivity_profile[-1,] = (
        air_conductivity_ini * (canopy_height / canopy_layers) * 0.5
    )

    return air_conductivity_profile


def temperature_conductivity_interpolation(
    min_conductivity: float,
    max_conductivity: float,
    canopy_layers: float = 3,
    option: str = "linear",
) -> DataArray:
    """Interpolation of initial temperature conductivity profile.

    Args:
        min_conductivity: minimum conductivity for specific medium
        max_conductivity: maximum conductivity for specific medium
        canopy_layers: number of canopy layers
        option: interpolation method, default = 'linear

    Returns:
        vertical profile of conductivities

    Options:
        linear (default)
    """
    if option == "linear":
        temp_conductivity_profile = DataArray(
            np.linspace(
                min_conductivity,
                max_conductivity,
                canopy_layers,
            ),
            dims="canopy_layers",
        )
    else:
        NotImplementedError("This interpolation method is not available.")

    return temp_conductivity_profile


def set_canopy_node_heights(
    canopy_height: DataArray,
    canopy_layers: int = 3,
) -> DataArray:
    """Set initial canopy node heights.

    *Describe how this will be used in the following*

    Args:
        canopy_height: canopy height, [m]
        canopy_layers: number of canopy layers
    Returns:
        array of initial canopy node heights
    """
    # TODO variable dimensions
    canopy_node_heights = DataArray(np.zeros([3, 2]), dims=["canopy_layers", "cell_id"])

    for i in range(0, canopy_height.size):
        canopy_node_heights[:, i] = (np.arange(canopy_layers) + 0.5) / (
            canopy_layers
            * canopy_height.values[
                i,
            ]
        )

    return canopy_node_heights


def set_soil_node_depths(
    soil_depth: DataArray,
    soil_layers: int = 2,
    soil_division_factor: float = EnergyBalanceConstants.soil_division_factor,
) -> DataArray:
    """Set initial soil node depths.

    *Describe how this will be used in the following*

    Args:
        soil_depth: soil depth, [m]
        soil_layers: number of soil layers
        soil_division_factor: Factor defines how to divide soil into layers with
        increasing thickness, alternative value 1.2 :cite:p:`MACLEAN2021`.

    Returns:
        array of initial soil node depths
    """

    return DataArray(
        [
            np.array(
                soil_depth
                / (float(soil_layers) ** soil_division_factor)
                * (x**soil_division_factor)
                for x in range(1, soil_layers + 1)
            )
        ]
    )


def set_initial_canopy_windspeed(
    wind_speed_10m: DataArray,
    canopy_layers: int = 3,
) -> DataArray:
    """Initialise canopy wind profile."""

    return DataArray(
        [np.array((np.arange(canopy_layers) + 1) / canopy_layers * wind_speed_10m)]
    )
