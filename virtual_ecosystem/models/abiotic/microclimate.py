"""The microclimate module contains the equations to solve the radiation and energy
balance in the Virtual Ecosystem.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic import abiotic_tools
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def initialise_absorbed_radiation(
    topofcanopy_radiation: NDArray[np.float32],
    leaf_area_index: NDArray[np.float32],
    layer_heights: NDArray[np.float32],
    light_extinction_coefficient: float,
) -> NDArray[np.float32]:
    r"""Calculate initial light absorption profile.

    This function calculates the fraction of radiation absorbed by a multi-layered
    canopy based on its leaf area index (:math:`LAI`) and extinction coefficient
    (:math:`k`) at each layer, the depth of each measurement (:math:`z`), and the
    incoming light intensity at the top of the canopy (:math:`I_{0}`). The
    implementation based on Beer's law:

    .. math:: I(z) = I_{0} * e^{(-k * LAI * z)}

    Args:
        topofcanopy_radiation: Top of canopy radiation shortwave radiation, [W m-2]
        leaf_area_index: Leaf area index of each canopy layer, [m m-1]
        layer_heights: Layer heights, [m]
        light_extinction_coefficient: Light extinction coefficient, [m-1]

    Returns:
        Shortwave radiation absorbed by canopy layers, [W m-2]
    """
    # Calculate the depth of each layer, [m]
    layer_depths = np.abs(np.diff(layer_heights, axis=0, append=0))

    # Calculate the light extinction for each layer
    layer_extinction = np.exp(
        -0.01 * light_extinction_coefficient * layer_depths * leaf_area_index
    )

    # Calculate how much light penetrates through the canopy, [W m-2]
    cumulative_extinction = np.cumprod(layer_extinction, axis=0)
    penetrating_radiation = cumulative_extinction * topofcanopy_radiation

    # Calculate how much light is absorbed in each layer, [W m-2]
    absorbed_radiation = np.abs(
        np.diff(
            penetrating_radiation,
            prepend=np.expand_dims(topofcanopy_radiation, axis=0),
            axis=0,
        )
    )

    return absorbed_radiation


def initialise_canopy_temperature(
    air_temperature: NDArray[np.float32],
    absorbed_radiation: NDArray[np.float32],
    canopy_temperature_ini_factor: float,
) -> NDArray[np.float32]:
    """Initialise canopy temperature.

    Args:
        air_temperature: Air temperature, [C]
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation
        absorbed_radiation: Shortwave radiation absorbed by canopy, [W m-2]

    Returns:
        Initial canopy temperature, [C]
    """
    return air_temperature + canopy_temperature_ini_factor * absorbed_radiation


def initialise_canopy_and_soil_fluxes(
    air_temperature: DataArray,
    topofcanopy_radiation: DataArray,
    leaf_area_index: DataArray,
    layer_heights: DataArray,
    layer_structure: LayerStructure,
    light_extinction_coefficient: float,
    canopy_temperature_ini_factor: float,
) -> dict[str, DataArray]:
    """Initialise canopy temperature and energy fluxes.

    This function initializes the following variables to run the first step of the
    energy balance routine: absorbed radiation (canopy), canopy temperature, sensible
    and latent heat flux (canopy and soil), and ground heat flux.

    Args:
        air_temperature: Air temperature, [C]
        topofcanopy_radiation: Top of canopy radiation, [W m-2]
        leaf_area_index: Leaf area index, [m m-2]
        layer_heights: Layer heights, [m]
        layer_structure: Instance of LayerStructure
        light_extinction_coefficient: Light extinction coefficient for canopy
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation

    Returns:
        Dictionary with absorbed radiation (canopy), canopy temperature, sensible
            and latent heat flux (canopy and soil), and ground heat flux [W m-2].
    """

    output = {}

    # Get variables within filled canopy layers
    leaf_area_index_true = leaf_area_index[layer_structure.index_filled_canopy]
    layer_heights_canopy = layer_heights[layer_structure.index_filled_canopy]
    air_temperature_canopy = air_temperature[layer_structure.index_filled_canopy]

    # Initialize absorbed radiation DataArray
    absorbed_radiation = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="canopy_absorption",
    )

    # Calculate absorbed radiation
    initial_absorbed_radiation = initialise_absorbed_radiation(
        topofcanopy_radiation=topofcanopy_radiation.to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.to_numpy(),
        light_extinction_coefficient=light_extinction_coefficient,
    )

    # Replace np.nan with new values and write in output dict
    absorbed_radiation[layer_heights_canopy.indexes] = initial_absorbed_radiation
    output["canopy_absorption"] = absorbed_radiation

    # Initialize canopy temperature DataArray
    canopy_temperature = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="canopy_temperature",
    )

    # Calculate initial temperature and write in output dict
    initial_canopy_temperature = initialise_canopy_temperature(
        air_temperature=air_temperature_canopy.to_numpy(),
        absorbed_radiation=initial_absorbed_radiation,
        canopy_temperature_ini_factor=canopy_temperature_ini_factor,
    )
    canopy_temperature[layer_structure.index_filled_canopy] = initial_canopy_temperature
    output["canopy_temperature"] = canopy_temperature

    # Initialise sensible heat flux with zeros and write in output dict
    sensible_heat_flux = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="sensible_heat_flux",
    )
    sensible_heat_flux[layer_structure.index_filled_canopy] = 0.001
    sensible_heat_flux[layer_structure.index_topsoil] = 0.001
    output["sensible_heat_flux"] = sensible_heat_flux

    # Initialise latent heat flux with zeros and write in output dict
    output["latent_heat_flux"] = sensible_heat_flux.copy().rename("latent_heat_flux")

    # Initialise latent heat flux with zeros and write in output dict
    ground_heat_flux = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="ground_heat_flux",
    )
    ground_heat_flux[layer_structure.index_topsoil] = 0.001
    output["ground_heat_flux"] = ground_heat_flux

    return output


def calculate_slope_of_saturated_pressure_curve(
    temperature: NDArray[np.float32],
    saturated_pressure_slope_parameters: list[float],
) -> NDArray[np.float32]:
    r"""Calculate slope of the saturated pressure curve.

    Args:
        temperature: Temperature, [C]
        saturated_pressure_slope_parameters: List of parameters to calcualte
            the slope of the saturated vapour pressure curve

    Returns:
        Slope of the saturated pressure curve, :math:`\Delta_{v}`
    """

    return (
        saturated_pressure_slope_parameters[0]
        * (
            saturated_pressure_slope_parameters[1]
            * np.exp(
                saturated_pressure_slope_parameters[2]
                * temperature
                / (temperature + saturated_pressure_slope_parameters[3])
            )
        )
        / (temperature + saturated_pressure_slope_parameters[3]) ** 2
    )


def calculate_longwave_emission(
    temperature: NDArray[np.float32],
    emissivity: float | NDArray[np.float32],
    stefan_boltzmann: float,
) -> NDArray[np.float32]:
    """Calculate longwave emission using the Stefan Boltzmann law, [W m-2].

    According to the Stefan Boltzmann law, the amount of radiation emitted per unit time
    from the area of a black body at absolute temperature is directly proportional to
    the fourth power of the temperature. Emissivity (which is equal to absorptive power)
    lies between 0 to 1.

    Args:
        temperature: Temperature, [K]
        emissivity: Emissivity, dimensionless
        stefan_boltzmann: Stefan Boltzmann constant, [W m-2 K-4]

    Returns:
        Longwave emission, [W m-2]
    """
    return emissivity * stefan_boltzmann * temperature**4


def calculate_net_radiation(
    incoming_radiation: NDArray[np.float32],
    absorbed_radiation: NDArray[np.float32],
    longwave_emission: NDArray[np.float32],
    albedo: float,
) -> NDArray[np.float32]:
    """Calculate net radiation, [W m-2].

    Args:
        incoming_radiation: Incoming radiation, [W m-2]
        absorbed_radiation: Absorbed radiation, [W m-2]
        longwave_emission: Longwave emission, [W m-2]
        albedo: Albedo, [-]

    Returns:
        net radiation, [W m-2]
    """
    return incoming_radiation * (1 - albedo) - absorbed_radiation - longwave_emission


def calculate_sensible_heat_flux(
    molar_density_air: NDArray[np.float32],
    specific_heat_air: NDArray[np.float32],
    air_temperature: NDArray[np.float32],
    surface_temperature: NDArray[np.float32],
    aerodynamic_resistance: float | NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate sensible heat flux, [W m-2].

    Args:
        molar_density_air: Molar density of air, [mole m-3]
        specific_heat_air: Specific heat of air, [J kg-1 K-1]
        air_temperature: Air temperature, [C]
        surface_temperature: Surface temperature (canopy or soil), [C]
        aerodynamic_resistance: Aerodynamic resistance, [-]

    Returns:
        sensible heat flux, [W m-2]
    """
    return (
        molar_density_air * specific_heat_air / aerodynamic_resistance
    ) * surface_temperature - air_temperature


def run_microclimate(
    data: Data,
    time_index: int,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConsts,
    core_constants: CoreConsts,
) -> dict[str, DataArray]:
    """Run microclimate model.

    Args:
        data: Data object
        time_index: Time index
        layer_structure: layer structure object
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models

    Returns:
        dictionary with updated microclimate variables
    """

    output = {}

    # Mean atmospheric pressure profile, [kPa]
    # TODO: this should only be filled for filled/true above ground layers
    output["atmospheric_pressure"] = layer_structure.from_template()
    output["atmospheric_pressure"][layer_structure.index_atmosphere] = data[
        "atmospheric_pressure_ref"
    ].isel(time_index=time_index)

    # Mean atmospheric C02 profile, [ppm]
    # TODO: this should only be filled for filled/true above ground layers
    output["atmospheric_co2"] = layer_structure.from_template()
    output["atmospheric_co2"][layer_structure.index_atmosphere] = data[
        "atmospheric_co2_ref"
    ].isel(time_index=time_index)

    #  Calculate atmospheric background variables
    molar_density_air = abiotic_tools.calculate_molar_density_air(
        temperature=data["air_temperature"].mean(dim="layers").to_numpy(),
        atmospheric_pressure=(
            data["atmospheric_pressure_ref"].isel(time_index=time_index).to_numpy()
        ),
        standard_mole=core_constants.standard_mole,
        standard_pressure=core_constants.standard_pressure,
        celsius_to_kelvin=core_constants.zero_Celsius,
    )
    specific_heat_air = abiotic_tools.calculate_specific_heat_air(
        temperature=data["air_temperature"].mean(dim="layers").to_numpy(),
        molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
        specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
    )

    # Calculate longwave emission from canopy
    longwave_emission_canopy = calculate_longwave_emission(
        temperature=data["canopy_temperature"].to_numpy() + core_constants.zero_Celsius,
        emissivity=abiotic_constants.leaf_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    # Calculate longwave emission from soil
    longwave_emission_soil = calculate_longwave_emission(
        temperature=data["soil_temperature"].to_numpy() + core_constants.zero_Celsius,
        emissivity=abiotic_constants.leaf_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    # Combine longwave emission in one variable
    longwave_emission = layer_structure.from_template()
    longwave_emission[layer_structure.index_filled_canopy] = longwave_emission_canopy[
        layer_structure.index_filled_canopy
    ]
    longwave_emission[layer_structure.index_topsoil_scalar] = longwave_emission_soil[
        layer_structure.index_topsoil_scalar
    ]
    output["longwave_emission"] = longwave_emission

    # Net radiation canopy
    net_radiation_canopy = calculate_net_radiation(
        incoming_radiation=data["topofcanopy_radiation"]
        .isel(time_index=time_index)
        .to_numpy(),
        absorbed_radiation=data["absorbed_radiation"].to_numpy(),
        longwave_emission=longwave_emission_canopy,
        albedo=abiotic_constants.leaf_albedo,
    )
    # net radiation soil
    net_radiation_soil = calculate_net_radiation(
        incoming_radiation=data["topofcanopy_radiation"]
        .isel(time_index=time_index)
        .to_numpy(),
        absorbed_radiation=data["absorbed_radiation"].sum(dim="layers").to_numpy(),
        longwave_emission=longwave_emission_soil[layer_structure.index_topsoil_scalar],
        albedo=abiotic_constants.surface_albedo,
    )
    # Combine net radiation in one variable
    net_radiation = layer_structure.from_template()
    net_radiation[layer_structure.index_filled_canopy] = net_radiation_canopy[
        layer_structure.index_filled_canopy
    ]
    net_radiation[layer_structure.index_topsoil_scalar] = net_radiation_soil

    #  TODO ra=ln((z-d)/z0)/karman *u(z)
    aerodynamic_resistance_canopy = 100.0
    aerodynamic_resistance_soil = 100.0

    sensible_heat_flux_canopy = calculate_sensible_heat_flux(
        molar_density_air=molar_density_air,
        specific_heat_air=specific_heat_air,
        air_temperature=data["air_temperature"].to_numpy(),
        surface_temperature=data["canopy_temperature"].to_numpy(),
        aerodynamic_resistance=aerodynamic_resistance_canopy,
    )

    sensible_heat_flux_soil = calculate_sensible_heat_flux(
        molar_density_air=molar_density_air,
        specific_heat_air=specific_heat_air,
        air_temperature=data["air_temperature"][
            layer_structure.index_topsoil_scalar - 1
        ].to_numpy(),
        surface_temperature=data["soil_temperature"][
            layer_structure.index_topsoil_scalar
        ].to_numpy(),
        aerodynamic_resistance=aerodynamic_resistance_soil,
    )

    # Combine sensible heat flux in one variable
    sensible_heat_flux = layer_structure.from_template()
    sensible_heat_flux[layer_structure.index_filled_canopy] = sensible_heat_flux_canopy[
        layer_structure.index_filled_canopy
    ]
    sensible_heat_flux[layer_structure.index_topsoil_scalar] = sensible_heat_flux_soil
    output["sensible_heat_flux"] = sensible_heat_flux

    #  TODO
    # wind speed
    # aerodynamic_resistance
    # latent heat flux
    #   latent heat vapourisation
    #   specific humidity
    #  Ground heat flux
    #  Update air/canopy/soil temperatures
    #  Update humidity/VPD

    return output
