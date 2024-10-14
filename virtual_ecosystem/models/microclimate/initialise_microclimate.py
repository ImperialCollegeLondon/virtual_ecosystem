r"""The ``models.abiotic.initialise_microclimate`` module contains a set of functions
to initialise the required variables for the microclimate update.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure


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
    sensible_heat_flux[layer_structure.index_filled_canopy] = 0
    sensible_heat_flux[layer_structure.index_topsoil] = 0
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
    ground_heat_flux[layer_structure.index_topsoil] = 0
    output["ground_heat_flux"] = ground_heat_flux

    return output
