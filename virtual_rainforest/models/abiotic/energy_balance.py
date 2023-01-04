"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest.
The sequence of processes is based on Maclean et al, 2021: Microclimc: A mechanistic
model of above, below and within-canopy microclimate. Ecological Modelling
Volume 451, 109567. https://doi.org/10.1016/j.ecolmodel.2021.109567.
"""

# from math import exp as exp

import numpy as np
from numpy.typing import NDArray

# from core.constants import CONSTANTS as C
CELCIUS_TO_KELVIN = 273.15  # calculate absolute temperature in Kelvin
VAPOR_PRESSURE_FACTOR1 = 0.6108  # constant in calculation of vapor pressure
VAPOR_PRESSURE_FACTOR2 = 17.27  # constant in calculation of vapor pressure
VAPOR_PRESSURE_FACTOR3 = 237.7  # constant in calculation of vapor pressure

# import external driving data at reference hight (2 m) for current timestep
# this will be a Data.data object
data = {
    "air_temperature_2m": 25,
    "relative_humidity_2m": 90,
    "atmospheric_pressure_2m": 101.325,
    "wind_speed_2m": 10.0,
}

soil_parameters = {
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
    """EnergyBalance method.

    Attributes:
        air_temperature: NDArray[np.float32],
        soil_temperature: NDArray[np.float32],
        canopy_temperature: NDArray[np.float32],
        temperature_above_canopy: NDArray[np.float32],
        canopy_wind_speed: NDArray[np.float32],
        canopy_node_heights: NDArray[np.float32],
        soil_node_depths: NDArray[np.float32],
        height_of_above_canopy: NDArray[np.float32],
        relative_humidity_2m: NDArray[np.float32],
        air_temperature_2m: NDArray[np.float32],
        mean_annual_temperature: NDArray[np.float32],
        atmospheric_pressure_2m: NDArray[np.float32],
        absorbed_radiation: : NDArray[np.float32],
        air_conductivity: NDArray[np.float32],
        leaf_conductivity: NDArray[np.float32],
        air_leaf_conductivity: NDArray[np.float32],
        sensible_heat_flux: NDArray[np.float32],
        latent_heat_flux: NDArray[np.float32],
        ground_heat_flux: NDArray[np.float32],
        diabatic_correction_factor: NDArray[np.float32]
        soil_type: NDArray[np.string_]
        soil_depth: NDArray[np.float32]
    """

    def __init__(
        self,
        data: dict[str, float],
        soil_type: NDArray[np.string_],
        soil_depth: NDArray[np.float32] = np.array(2.0, dtype=float),
        mean_annual_temperature: NDArray[np.float32] = np.array(20, dtype=float),
        canopy_layers: NDArray[np.int32] = np.array(3, dtype=int),
        soil_layers: NDArray[np.int32] = np.array(2, dtype=int),
        canopy_height: NDArray[np.float32] = np.array(30.0, dtype=float),
        absorbed_radiation: NDArray[np.float32] = np.array(100.0, dtype=float),
    ) -> None:
        """Initializes point-based energy_balance method.

        Generates a set of climate, conductivity, and soil parameters for running the
        first time step of the model. This might go in the json file.
        """

        # set boundary conditions
        self.canopy_layers = canopy_layers
        self.soil_layers = soil_layers
        self.canopy_height = canopy_height

        self.air_temperature_2m = data["air_temperature_2m"]
        self.relative_humidity_2m = data["relative_humidity_2m"]
        self.atmospheric_pressure_2m = data["atmospheric_pressure_2m"]
        self.wind_speed_2m = data["wind_speed_2m"]
        self.mean_annual_temperature = mean_annual_temperature

        # interpolate initial temperature profile, could be more realistic
        self.temperature_above_canopy = self.air_temperature_2m
        temperature_interpolation = np.linspace(
            self.mean_annual_temperature,
            self.temperature_above_canopy,
            self.canopy_layers + self.soil_layers,
        )

        self.air_temperature = temperature_interpolation[
            (int(self.soil_layers)) : int((self.canopy_layers + self.soil_layers))
        ]
        self.soil_temperature = temperature_interpolation[0 : int(self.soil_layers)][
            ::-1
        ]
        self.absorbed_radiation = absorbed_radiation
        self.canopy_temperature = self.air_temperature + 0.01 * self.absorbed_radiation

        # initiate relative humidity and atmospheric pressure
        self.relative_humidity = np.repeat(
            data["relative_humidity_2m"], self.canopy_layers
        )
        self.atmospheric_pressure = data["atmospheric_pressure_2m"]

        # set initial conductivities
        self.air_conductivity = (
            np.repeat(50, self.canopy_layers + 1)
            * (self.canopy_layers / self.canopy_height)
            * (2 / self.canopy_layers)
        )
        self.air_conductivity[0] = 2 * self.air_conductivity[0]
        self.air_conductivity[self.canopy_layers] = (
            self.air_conductivity[self.canopy_layers]
            * (self.canopy_height / self.canopy_layers)
            * 0.5
        )

        self.leaf_conductivity = np.linspace(
            np.array(0.35), np.array(0.32), self.canopy_layers
        )
        self.air_leaf_conductivity = np.linspace(
            np.array(0.13), np.array(0.19), self.canopy_layers
        )

        # set initial heights
        self.canopy_node_heights = [
            (x + 0.5) / self.canopy_layers * self.canopy_height
            for x in range(0, self.canopy_layers)
        ]
        self.soil_node_depths = [
            2 / (self.soil_layers**2.42) * (x**2.42)
            for x in range(1, self.soil_layers + 1)
        ]
        self.height_of_above_canopy = self.canopy_height
        self.canopy_wind_speed = [
            (x / self.canopy_layers) * self.wind_speed_2m
            for x in range(1, self.canopy_layers + 1)
        ]

        # set initial fluxes
        self.sensible_heat_flux = np.array(0.0)
        self.latent_heat_flux = np.repeat(0.0, self.canopy_layers)
        self.ground_heat_flux = np.array(0.0)
        self.diabatic_correction_factor = np.array(0.0)

        # get soil parameters
        self.soil_parameters = soil_parameters[str(soil_type)]
        # there is another soil node depth in Maclean, not sure what the difference is
        # self.soil_node_depth = [soil_depth/self.soil_layers**1.2 * (x**1.2)
        # for x in range(1, self.soil_layers)]


# --- this is the sequence of processes in microclimc for one time step ---
# paraminit - DONE
# soilinit
# runonetimestep:
# Check whether any vegetation layers have zero PAI
# == Unpack climate variables ==
# == calculate baseline variables: ==
# - molar density of air
# - specific heat of air
# - latent heat of vaporisation
# Adjust wind to 2 m above canopy
# Generate heights of nodes
# Set z above
# == Calculate diabatic correction factors ==
# Calculate temperatures and relative humidities for top of canopy
# Set limits to temp can
# Adjust relative humidity
# == Calculate wind speed and turbulent conductances ==
# == Calculate canopy turbulences ==
# == Calculate conductivity to top of canopy and merge ==
# Turbulent air conductivity and layer merge
# == Calculate absorbed radiation
# == Conductivities ==
# Vapour conductivity
# Leaf conductivity
# == Soil conductivity ==
# conductivity and specific heat
# soil heat
# Canopy air layer not in equilibrium with above canopy:
# Heat to add / loose
# vapour exchange
# Interpolate
# Canopy air layer in equilibrium with above canopy
# Set limits to soil temperatures
# Calculate Heat flux
# Latent heat
# dewpoints
# Incoming radiation
# internal function to sort out vegetation parameters
