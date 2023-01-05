"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest.
The sequence of processes is based on Maclean et al, 2021: Microclimc: A mechanistic
model of above, below and within-canopy microclimate. Ecological Modelling
Volume 451, 109567. https://doi.org/10.1016/j.ecolmodel.2021.109567.

# --- this is the sequence of processes in microclimc for one time step ---
# paraminit - DONE
# soilinit - DONE
# runonetimestep:
# Check whether any vegetation layers have zero PAI
# == Unpack climate variables == DONE
# == calculate baseline variables: == DONE
# - molar density of air DONE
# - specific heat of air DONE
# - latent heat of vaporisation DONE

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
"""

from math import exp, sqrt, log

import numpy as np
from numpy.typing import NDArray

# from core.constants import CONSTANTS as C
LEAF_TEMPERATURE_INI_FACTOR = 0.01  # factor used to initialise leaf temperature
SOIL_DIVISION_FACTOR = 2.42  # factor defines how to divide soil into layers with
# increasing thickness, alternateve value 1.2
MIN_LEAF_CONDUCTIVITY = (
    0.25  # typical for decidious forest with wind above canopy 2 m/s
)
MAX_LEAF_CONDUCTIVITY = (
    0.32  # typical for decidious forest with wind above canopy 2 m/s
)
AIR_CONDUCTIVITY = 50.0  # typical for decidious forest with wind above canopy 2 m/s
MIN_LEAF_AIR_CONDUCTIVITY = (
    0.13  # typical for decidious forest with wind above canopy 2 m/s
)
MAX_LEAF_AIR_CONDUCTIVITY = (
    0.19  # typical for decidious forest with wind above canopy 2 m/s
)
KARMANS_CONSTANT = 0.4  # constant to calculate mixing length
CELCIUS_TO_KELVIN = 273.15  # calculate absolute temperature in Kelvin
STANDARD_MOLE = 44.6  # moles of ideal gas in 1 m^3 air at standard atmosphere
VAPOR_PRESSURE_FACTOR1 = 0.6108  # constant in calculation of vapor pressure
VAPOR_PRESSURE_FACTOR2 = 17.27  # constant in calculation of vapor pressure
VAPOR_PRESSURE_FACTOR3 = 237.7  # constant in calculation of vapor pressure

# import external driving data at reference hight (2 m) for current timestep
# this will be a Data.data object
data = {
    "air_temperature_2m": 25,
    "relative_humidity_2m": 90,
    "atmospheric_pressure_2m": 101.325,
    "wind_speed_10m": 2.0,
    "soil_moisture_reference": 0.3,
}

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
        mean_annual_temperature: NDArray[np.float32], temperature of deepest soil layer
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
        soil_moisture: NDArray[np.float32]
        soil_moisture_reference: NDArray[np.float32]
        wind_profile: NDArray[np.float32]
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
        self.soil_depth = soil_depth

        self.air_temperature_2m = data["air_temperature_2m"]
        self.relative_humidity_2m = data["relative_humidity_2m"]
        self.atmospheric_pressure_2m = data["atmospheric_pressure_2m"]
        self.wind_speed_10m = data["wind_speed_10m"]
        self.mean_annual_temperature = mean_annual_temperature
        self.soil_moisture_reference = data["soil_moisture_reference"]

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
        self.canopy_temperature = (
            self.air_temperature + LEAF_TEMPERATURE_INI_FACTOR * self.absorbed_radiation
        )

        # initiate relative humidity and atmospheric pressure
        self.relative_humidity = np.repeat(
            data["relative_humidity_2m"], self.canopy_layers
        )
        self.atmospheric_pressure = data["atmospheric_pressure_2m"]

        # set initial conductivities
        self.air_conductivity = (
            np.repeat(AIR_CONDUCTIVITY, self.canopy_layers + 1)
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
            np.array(MIN_LEAF_CONDUCTIVITY),
            np.array(MAX_LEAF_CONDUCTIVITY),
            self.canopy_layers,
        )
        self.air_leaf_conductivity = np.linspace(
            np.array(MIN_LEAF_AIR_CONDUCTIVITY),
            np.array(MAX_LEAF_AIR_CONDUCTIVITY),
            self.canopy_layers,
        )

        # set initial heights
        self.canopy_node_heights = [
            (x + 0.5) / self.canopy_layers * self.canopy_height
            for x in range(0, self.canopy_layers)
        ]
        self.soil_node_depths = [
            self.soil_depth
            / (self.soil_layers**SOIL_DIVISION_FACTOR)
            * (x**SOIL_DIVISION_FACTOR)
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

    def calc_molar_density_air(
        self,
        temperature: NDArray[np.float32] = 20.0,
        atmospheric_pressure: NDArray[np.float32] = 101.3,
    ) -> NDArray[np.float32]:
        """Calculate temperature-dependent molar density of air.

        Args:
            temperature: NDArray[np.float32], temperature [C]
            atmospheric_pressure: NDArray[np.float32], atmospheric pressure [kPa]

        Returns:
            molar_density_air: NDArray[np.float32], Molar density of air [mol m-3]
        """
        temperature_kelvin = temperature + CELCIUS_TO_KELVIN
        molar_density_air = (
            STANDARD_MOLE
            * (temperature_kelvin / atmospheric_pressure)
            * (CELCIUS_TO_KELVIN / temperature_kelvin)
        )
        return molar_density_air

    def calc_specific_heat_air(
        self, temperature: NDArray[np.float32] = 20.0
    ) -> NDArray[np.float32]:
        """Calculate molar temperature-dependent specific heat of air.

        Args:
            temperature: NDArray[np.float32], temperature [C]

        Returns:
            specific_heat_air: NDArray[np.float32], specific heat of air at constant
                pressure (J mol-1 K-1)
        """
        specific_heat_air = 2e-05 * temperature**2 + 0.0002 * temperature + 29.119
        return specific_heat_air

    def calc_latent_heat_of_vaporisation(
        self, temperature: NDArray[np.float32]
    ) -> NDArray[np.float32]:
        """Calculate latent heat of vaporisation.

        Args:
            temperature: NDArray[np.float32], temperature [C]

        Returns:
            Latent heat of vaporisation [J mol-1]
        """
        latent_heat_of_vaporisation = -42.575 * temperature + 44994
        return latent_heat_of_vaporisation

    def calc_roughness_length(
        self,
        canopy_height: NDArray[np.float32],
        plant_area_index: NDArray[np.float32],
        substrate_surface_drag_coefficient: float = 0.003,
        height_scaling_parameter: float = 7.5,
        roughness_element_drag_coefficient: float = 0.3,
        roughness_sublayer_depth_coefficient: float = 0.193,
        max_velocity_ratio: float = 0.3,
    ) -> NDArray[np.float32]:
        """Calculate roughness length governing momentum transfer.

        Args:
            canopy_height: NDArray[np.float32], canopy height [m]
            plant_area_index: NDArray[np.float32], Plant area index [m m-1]
            substrate_surface_drag_coefficient:float, substrate-surface drag coefficient
            height_scaling_parameter: float, Control parameter scaling d/h (from Raupach
                1994)
            roughness_element_drag_coefficient: float,roughness-element drag coefficient
            roughness_sublayer_depth_coefficient: float, parameter characterizes the
                roughness sublayer depth
            max_velocity_ratio: float, Max ratio of wind velocity to friction velocity

        Returns:
            roughness_length: NDArray[np.float32], momentum roughness length [m]

        Reference:
            Raupach, M.R. (1994) Simplified expressions for vegetation roughness length
            and zero-plane displacement as functions of canopy height and area index.
            Boundary-Layer Meteorology 71: 211-216.
        """
        zero_plane_displacement = (
            1
            - (1 - exp(-sqrt(height_scaling_parameter * plant_area_index)))
            / sqrt(height_scaling_parameter * plant_area_index)
        ) * canopy_height

        wind_ratio = sqrt(
            substrate_surface_drag_coefficient
            + (roughness_element_drag_coefficient * plant_area_index) / 2
        )
        wind_ratio[wind_ratio > max_velocity_ratio] = max_velocity_ratio
        roughness_length = (canopy_height - zero_plane_displacement) * exp(
            -0.4 * (1 / wind_ratio) - roughness_sublayer_depth_coefficient
        )
        roughness_length = (
            substrate_surface_drag_coefficient
            if roughness_length < substrate_surface_drag_coefficient
            else roughness_length
        )
        return roughness_length

    # def calc_diabatic_correction_factor()

    def calc_wind_profile(
        self,
        canopy_height: NDArray[np.float32],
        wind_profile_heights: NDArray[np.float32],
        plant_area_index: NDArray[np.float32],
        height_scaling_parameter: float = 7.5,
        ground_vegetation_height: float = 0.05,
        diabatic_correction_factor: NDArray[np.float32] = np.array(0.0),
        wind_measurement_height: float = 10.0,
        attenuation_coefficient: NDArray[np.float32] = np.array(2.0),
        below_canopy_roughness_length: float = 0.004,
    ) -> None:
        """Calculates wind speed at any given point above or below canopy.

        Args:
            canopy_height: NDArray[np.float32], height of canopy [m]
            wind_profile_heights: NDArray[np.float32], heights for which wind is
                calculated [m]
            plant_area_index: NDArray[np.float32], plant area index [m m-1]
            height_scaling_parameter: float = 7.5,
            ground_vegetation_height: float = 0.05, height of ground vegetation layer
                below canopy [m]
            diabatic_correction_factor: NDArray[np.float32] = np.array(0.0)
            wind_measurement_height: float = 10.0,
            attenuation_coefficient: NDArray[np.float32] = np.array(2.0), wind
                attenuation coefficient
            below_canopy_roughness_length: roughness length (m) of vegetation layer
                below canopy

        Returns:
            self.wind_profile: NDArray[np.float32], wind at different heights [m s-1]
        """
        zero_plane_displacement = (
            1
            - (1 - exp(-sqrt(height_scaling_parameter * plant_area_index)))
            / sqrt(height_scaling_parameter * plant_area_index)
        ) * canopy_height
        roughness_length = self.calc_roughness_length(
            canopy_height, plant_area_index, below_canopy_roughness_length
        )

        # dg = 0.65 * ground_vegetation_height   #unused?
        ground_vegetation_roughness_length = 0.1 * ground_vegetation_height

        wind_log_profile1 = (
            log((wind_measurement_height - zero_plane_displacement) / roughness_length)
            + diabatic_correction_factor
        )
        friction_velocity = KARMANS_CONSTANT * (self.wind_speed_10m / wind_log_profile1)

        # case 1: wind_profile_heights above canopy
        wind_log_profile2 = (
            log((wind_profile_heights - zero_plane_displacement) / roughness_length)
            + diabatic_correction_factor
        )  # suppress warning in MacLean
        wind_log_profile2[wind_log_profile2 < 0.55] = 0.55
        self.wind_profile = (friction_velocity / KARMANS_CONSTANT) * wind_log_profile2

        # case 2: wind_profile_heights below canopy
        sel = np.where(wind_profile_heights < canopy_height)
        wind_log_profile2 = (
            log(
                (canopy_height[sel] - zero_plane_displacement[sel])
                / roughness_length[sel]
            )
            + diabatic_correction_factor[sel]
        )
        self.wind_profile[sel] = (
            friction_velocity[sel] / KARMANS_CONSTANT
        ) * wind_log_profile2

        # case 3: wind_profile_heights above 10% of canopy hgt, but below top of canopy
        sel = np.where(
            wind_profile_heights > (0.1 * canopy_height)
            and wind_profile_heights < canopy_height
        )
        self.wind_profile[sel] = self.wind_profile[sel] * exp(
            attenuation_coefficient[sel]
            * ((wind_profile_heights[sel] / canopy_height[sel]) - 1)
        )

        # case 4: wind_profile_heights below 10% of canopy hgt
        sel = np.where(wind_profile_heights <= (0.1 * canopy_height))
        self.wind_profile[sel] = self.wind_profile[sel] * exp(
            attenuation_coefficient[sel]
            * (((0.1 * canopy_height[sel]) / canopy_height[sel]) - 1)
        )
        wind_log_profile1 < -log(
            (0.1 * canopy_height[sel]) / ground_vegetation_roughness_length[sel]
        )
        +diabatic_correction_factor[sel]
        friction_velocity = KARMANS_CONSTANT * (
            self.wind_profile[sel] / wind_log_profile1
        )
        wind_log_profile2 < -log(
            wind_profile_heights[sel] / ground_vegetation_roughness_length[sel]
        )
        +diabatic_correction_factor[sel]
        self.wind_profile[sel] < -(
            friction_velocity / KARMANS_CONSTANT
        ) * wind_log_profile2
