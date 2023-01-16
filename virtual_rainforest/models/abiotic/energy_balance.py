"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest.
The sequence of processes is based on Maclean et al, 2021: Microclimc: A mechanistic
model of above, below and within-canopy microclimate. Ecological Modelling
Volume 451, 109567. https://doi.org/10.1016/j.ecolmodel.2021.109567.
"""

import numpy as np
from numpy.typing import NDArray

# from core.constants import CONSTANTS as C
LEAF_TEMPERATURE_INI_FACTOR = 0.01
"""factor used to initialise leaf temperature"""
SOIL_DIVISION_FACTOR = 2.42
"""factor defines how to divide soil into layers with increasing thickness, alternative
value 1.2"""
MIN_LEAF_CONDUCTIVITY = 0.25
"""min leaf conductivity, typical for decidious forest with wind above canopy 2 m/s"""
MAX_LEAF_CONDUCTIVITY = 0.32
"""max leaf conductivity, typical for decidious forest with wind above canopy 2 m/s"""
AIR_CONDUCTIVITY = 50.0
"""air conductivity, typical for decidious forest with wind above canopy 2 m/s"""
MIN_LEAF_AIR_CONDUCTIVITY = 0.13
"""min conductivity between leaf and air, typical for decidious forest with wind above
canopy 2 m/s"""
MAX_LEAF_AIR_CONDUCTIVITY = 0.19
"""max conductivity between leaf and air, typical for decidious forest with wind above
canopy 2 m/s"""
KARMANS_CONSTANT = 0.4
"""constant to calculate mixing length"""
CELSIUS_TO_KELVIN = 273.15
"""factor to convert temperature in Celsius to absolute temperature in Kelvin"""
STANDARD_MOLE = 44.6
"""moles of ideal gas in 1 m^3 air at standard atmosphere"""
MOLAR_HEAT_CAPACITY_AIR = 29.19
"""molar heat capacity of air [J mol-1 C-1]"""
VAPOR_PRESSURE_FACTOR1 = 0.6108
"""constant in calculation of vapor pressure"""
VAPOR_PRESSURE_FACTOR2 = 17.27
"""constant in calculation of vapor pressure"""
VAPOR_PRESSURE_FACTOR3 = 237.7
"""constant in calculation of vapor pressure"""

# import external driving data at reference hight (2 m) TODO for current timestep
# this will be a Data.data object
data = {
    "time": [1, 2, 3],
    "air_temperature_2m": 25,  # Celsius
    "relative_humidity_2m": 90,  # percent
    "atmospheric_pressure_2m": 101.325,  # kPa
    "wind_speed_10m": 2.0,  # m s-1
    "soil_moisture_reference": 0.3,  # fraction
    "mean_annual_temperture": 20.0,  # Celsius
    "soil_depth": 2.0,  # meter
}

# soil parameter for different soil types, no real values, will be external data base
soil_parameters = {  # these are not real values
    "Sand": {
        "Smax": 1,  # Volumetric water content at saturation (m^3 / m^3)
        "Smin": 1,  # Residual water content (m^3 / m^3)
        "alpha": 1,  # Shape parameter of the van Genuchten model (cm^-1)
        "n": 1,  # Pore_size_distribution_parameter (dimensionless, > 1)
        "Ksat": 1,  # Saturated hydraulic conductivity (cm / day)
        "Vq": 1,  # Volumetric quartz content of soil
        "Vm": 1,  # Volumetric mineral content of soil
        "Vo": 1,  # Volumetric organic content of soil
        "Mc": 1,  # Mass fraction of clay
        "rho": 1,  # Soil bulk density (Mg / m^3)
        "b": 1,  # Shape parameter for Campbell model (dimensionless, > 1)
        "psi_e": 1,  # Matric potential (J / m^3)
    },
    "Clay": {
        "Smax": 0.1,  # Volumetric water content at saturation (m^3 / m^3)
        "Smin": 0.1,  # Residual water content (m^3 / m^3)
        "alpha": 0.1,  # Shape parameter of the van Genuchten model (cm^-1)
        "n": 0.1,  # Pore_size_distribution_parameter (dimensionless, > 1)
        "Ksat": 0.1,  # Saturated hydraulic conductivity (cm / day)
        "Vq": 0.1,  # Volumetric quartz content of soil
        "Vm": 0.1,  # Volumetric mineral content of soil
        "Vo": 0.1,  # Volumetric organic content of soil
        "Mc": 0.1,  # Mass fraction of clay
        "rho": 0.1,  # Soil bulk density (Mg / m^3)
        "b": 0.1,  # Shape parameter for Campbell model (dimensionless, > 1)
        "psi_e": 0.1,  # Matric potential (J / m^3)
    },
}


class EnergyBalance:
    """EnergyBalance method."""

    def __init__(
        self,
        soil_type: NDArray[np.string_],
        soil_layers: NDArray[np.int32] = np.array(
            2, dtype=np.int32
        ),  # opt. from config
        canopy_layers: NDArray[np.int32] = np.array(
            3, dtype=np.int32
        ),  # opt. from config
    ) -> None:
        """Initializes point-based energy_balance method."""

        # set boundary conditions
        self.soil_type = soil_type
        """Soil type"""
        self.soil_depth = data["soil_depth"]
        """Soil depth [m]"""
        self.soil_layers = soil_layers
        """Number of soil layers. Currently static."""
        self.canopy_layers = canopy_layers
        """Number of canopy layers."""

    def initialise_vertical_profile(  # this could later move to AbioticModel
        self,
        initial_canopy_height: NDArray[np.float32] = np.array(20.0, dtype=np.float32),
        initial_absorbed_radiation: NDArray[np.float32] = np.array(
            100.0, dtype=np.float32
        ),
        interpolation_method: str = "linear",
    ) -> None:
        """Generates a set of initial climate, conductivity, and soil parameters.

        Generates a set of climate, conductivity, and soil parameters for running the
        first time step of the model.
        """

        # select first timestep in data
        self.data = data[0]  # how can I select first timestep?

        # set initial canopy height
        self.canopy_height = initial_canopy_height
        """Canopy height [m]"""

        # set initial absorbed radiation
        self.absorbed_radiation = initial_absorbed_radiation
        """Radiation absorbed by canopy [W m-2]"""

        # interpolate initial temperature profile, linear, could be more realistic
        self.air_temperature = self.temperature_interpolation(
            option=interpolation_method
        )[(int(self.soil_layers)) : int((self.canopy_layers + self.soil_layers))]
        """Vertical profile of atmospheric temperatures [C]."""

        self.soil_temperature = self.temperature_interpolation(
            option=interpolation_method
        )[0 : int(self.soil_layers)][::-1]
        """Vertical profile of soil temperatures [C]."""

        self.canopy_temperature = (
            self.air_temperature
            + LEAF_TEMPERATURE_INI_FACTOR
            * self.absorbed_radiation  # this needs vertical levels
        )
        """Vertical profile of canopy temperatures [C]."""

        # initiate relative humidity and atmospheric pressure
        self.relative_humidity = np.repeat(
            data["relative_humidity_2m"], self.canopy_layers
        )
        """Vertical profile of atmospheric relative humidity [%]."""

        self.atmospheric_pressure = data["atmospheric_pressure_2m"]
        """Atmospheric pressure [kPa]"""

        # set initial conductivities
        self.air_conductivity = (
            np.repeat(AIR_CONDUCTIVITY, self.canopy_layers + 1)
            * (self.canopy_layers / self.canopy_height)
            * (2 / self.canopy_layers)
        )
        """Vertical profile of air conductivities []"""

        self.air_conductivity[0] = 2 * self.air_conductivity[0]
        self.air_conductivity[self.canopy_layers] = (
            self.air_conductivity[self.canopy_layers]
            * (self.canopy_height / self.canopy_layers)
            * 0.5
        )

        self.leaf_conductivity = self.temp_conductivity_interpolation(
            MIN_LEAF_CONDUCTIVITY, MAX_LEAF_CONDUCTIVITY, option=interpolation_method
        )
        """Vertical profile of leaf conductivities []"""

        self.air_leaf_conductivity = self.temp_conductivity_interpolation(
            MIN_LEAF_AIR_CONDUCTIVITY,
            MAX_LEAF_AIR_CONDUCTIVITY,
            option=interpolation_method,
        )
        """Vertical profile of air-leaf conductivities []"""

        # set initial heights
        self.canopy_node_heights = [
            (x + 0.5) / self.canopy_layers * self.canopy_height
            for x in range(0, self.canopy_layers)
        ]
        """Canopy node heights [m]"""

        self.soil_node_depths = [
            self.soil_depth
            / (self.soil_layers**SOIL_DIVISION_FACTOR)
            * (x**SOIL_DIVISION_FACTOR)
            for x in range(1, self.soil_layers + 1)
        ]
        """Soil node depths [m]"""

        self.height_of_above_canopy = self.canopy_height
        """Height defined as 'height above canopy' [m]"""

        self.canopy_wind_speed = [
            (x / self.canopy_layers) * data["wind_speed_10m"]
            for x in range(1, self.canopy_layers + 1)
        ]
        """Vertical profile of canopy wind speed [m s-1]"""

        # set initial fluxes
        self.sensible_heat_flux = np.array(0.0)
        """Sensible Heat flux [W m-2]"""
        self.latent_heat_flux = np.repeat(0.0, self.canopy_layers)
        """Latent Heat flux [W m-2]"""
        self.ground_heat_flux = np.array(0.0)
        """Ground Heat flux [W m-2]"""
        self.diabatic_correction_factor = np.array(0.0)
        """Diabatic correction factor []"""

        # get soil parameters
        self.soil_parameters = soil_parameters[str(self.soil_type)]
        """Dictionary of soil parameters for each grid cell."""

    def update_canopy(
        self,
        canopy_height: NDArray[np.float32] = np.array(30.0, dtype=np.float32),
        absorbed_radiation: NDArray[np.float32] = np.array(100.0, dtype=np.float32),
    ) -> None:
        """Update canopy each time step."""
        self.canopy_height = canopy_height  # input from plant module
        self.absorbed_radiation = absorbed_radiation  # input from plant module

    # small functions
    def temperature_interpolation(self, option: str = "linear") -> NDArray[np.float32]:
        """Interpolation of initial temperature profile.

        Options:
            linear
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
            linear
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
        temperature_kelvin = temperature + CELSIUS_TO_KELVIN
        molar_density_air = (
            STANDARD_MOLE
            * (temperature_kelvin / atmospheric_pressure)
            * (CELSIUS_TO_KELVIN / temperature_kelvin)
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
        return 2e-05 * temperature**2 + 0.0002 * temperature + MOLAR_HEAT_CAPACITY_AIR

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
