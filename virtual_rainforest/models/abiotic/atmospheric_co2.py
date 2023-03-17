r"""The ``models.abiotic.atmospheric_co2`` module calculates the within- and below-
canopy CO\ :sub:`2`\ profile for the Virtual Rainforest.

Based on external inputs, the module interpolates an initial vertical
CO\ :sub:`2`\ profile which
is then modified by plant net carbon assimilation and soil and animal respiration and
vertically mixed based on the wind profiles above, within, and below the canopy (the
mixing is currently not implemented).

TODO cross-check input variable names with other modules
TODO update indexing vertical dimension
"""  # noqa: D205, D415

from dataclasses import dataclass

import numpy as np
import xarray as xr
from xarray import DataArray

from virtual_rainforest.core.data import Data


@dataclass
class CO2Constants:
    r"""CO\ :sub:`2`\ constants class."""

    ambient_co2_default: float = 400
    r"""Default ambient CO\ :sub:`2`\ concentration, [ppm]"""


def calculate_co2_profile(
    data: Data,
    atmosphere_layers: int,  # from config?
    initialisation_method: str = "homogenous",
    mixing: bool = False,
    co2_const: CO2Constants = CO2Constants(),
) -> DataArray:
    r"""Calculate CO\ :sub:`2`\ profile.

    This function takes a :class:`~virtual_rainforest.core.data.Data` object as ``data``
    argument that contains the following variables:

    * atmospheric CO\ :sub:`2`\
    * plant net CO\ :sub:`2`\ assimilation
    * soil respiration
    * animal respiration

    Args:
        data: A Virtual Rainforest Data object.
        atmosphere_layers: number of atmosphere layers for which CO\ :sub:`2`\
            concentration is calculated
        initialisation_method: interpolation method, default copies ambient
            CO\ :sub:`2`\ to all vertical levels
        mixing: flag if mixing is true or false

    Returns:
        vertical profile of CO\ :sub:`2`\ concentrations, [ppm]
    """

    # check if atmospheric CO2 concentration in data
    if "atmospheric_co2" not in data:
        ambient_atmospheric_co2 = DataArray(
            np.repeat(
                co2_const.ambient_co2_default,
                len(data.grid.cell_id),
            ),
            dims="cell_id",
        )
    else:
        ambient_atmospheric_co2 = data["atmsopheric_co2"]

    # check if plant_net_co2_assimilation in data
    if "plant_net_co2_assimilation" not in data:
        plant_net_co2_assimilation = DataArray(
            np.zeros((atmosphere_layers - 2, len(data.grid.cell_id))),
            dims=["atmosphere_layers", "cell_id"],
        )

    else:
        plant_net_co2_assimilation1 = data["plant_net_co2_assimilation"]
        plant_net_co2_assimilation = plant_net_co2_assimilation1.rename(
            {"canopy_layers": "atmosphere_layers"}
        )

    # check if soil_respiration in data
    if "soil_respiration" not in data:
        soil_respiration = DataArray(
            np.zeros((len(data.grid.cell_id))),
            dims=["cell_id"],
        )
    else:
        soil_respiration = data["soil_respiration"]

    # check if animal_respiration in data
    if "animal_respiration" not in data:
        animal_respiration = DataArray(
            np.zeros((len(data.grid.cell_id))),
            dims=["cell_id"],
        )
    else:
        animal_respiration = data["animal_respiration"]

    # initialise CO2 profile
    initial_co2_profile = initialise_co2_profile(
        ambient_atmospheric_co2=ambient_atmospheric_co2,
        atmosphere_layers=atmosphere_layers,
        initialisation_method=initialisation_method,
    )

    # Calculate CO2 within canopy
    co2_within_canopy = calculate_co2_within_canopy(
        initial_co2_profile=initial_co2_profile.isel(
            atmosphere_layers=slice(1, atmosphere_layers - 1)
        ),
        plant_net_co2_assimilation=plant_net_co2_assimilation,
    )
    # Calculate CO2 below canopy
    co2_below_canopy = calculate_co2_below_canopy(
        initial_co2_profile=initial_co2_profile.isel(atmosphere_layers=-1),
        soil_respiration=soil_respiration,
        animal_respiration=animal_respiration,
    )
    # Mix CO2
    co2_profile_mixed = vertical_mixing_co2(
        co2_above_canopy=initial_co2_profile.isel(atmosphere_layers=0),
        co2_within_canopy=co2_within_canopy,
        co2_below_canopy=co2_below_canopy,
        mixing=False,
    )

    return co2_profile_mixed


# helper functions
def initialise_co2_profile(
    ambient_atmospheric_co2: DataArray,
    atmosphere_layers: int,
    initialisation_method: str = "homogenous",
) -> DataArray:
    r"""Initialise CO\ :sub:`2`\ profile.

    Args:
        ambient_atmospheric_co2: ambient CO\ :sub:`2`\ concentraion, [ppm],
        atmosphere_layers: number of atmosphere layers for which CO\ :sub:`2`\
             concentration is calculated
        initialisation_method: interpolation method for initial CO\ :sub:`2`\ profile,
            default copies ambient CO\ :sub:`2`\ to all vertical levels

    Returns:
        initial vertical CO\ :sub:`2`\ profile, [ppm]
    """

    if initialisation_method != "homogenous":
        raise (NotImplementedError("This method is not implemented"))

    else:
        initial_co2_profile = DataArray(
            ambient_atmospheric_co2.expand_dims(
                dim={"atmosphere_layers": atmosphere_layers}
            )
        )
    return initial_co2_profile


def calculate_co2_within_canopy(
    initial_co2_profile: DataArray,
    plant_net_co2_assimilation: DataArray,
) -> DataArray:
    r"""Calculate CO\ :sub:`2`\ concentration within canopy.

    This function subtracts the net CO\ :sub:`2`\ assimilation of plants from the
    ambient CO\ :sub:`2`\ level. Make sure that the initial_co2_profile has the same
    dimensions as the canopy.

    Args:
        initial_co2_profile: initial CO\ :sub:`2`\ profile, [ppm]
        plant_net_co2_assimilation: plant net canron assimilation, [ppm]

    Returns:
        CO\ :sub:`2`\ concentration within canopy, [ppm]
    """

    return initial_co2_profile - plant_net_co2_assimilation


def calculate_co2_below_canopy(
    initial_co2_profile: DataArray,
    soil_respiration: DataArray,
    animal_respiration: DataArray,
) -> DataArray:
    r"""Calculate CO\ :sub:`2`\ concentration below canopy.

    This function adds the net respiration of soil organisms and animals to the ambient
    CO\ :sub:`2`\ level. Make sure that the initial_co2_profile has the same dimensions
    as layers below canopy.

    Args:
        initial_co2_profile: initial CO\ :sub:`2`\ profile, [ppm]
        soil_respiration: soil respiration, [ppm]
        animal_respiration: animal respiration, [ppm]

    Returns:
        CO\ :sub:`2`\ concentration below canopy, [ppm]
    """
    return initial_co2_profile + soil_respiration + animal_respiration


def vertical_mixing_co2(
    co2_above_canopy: DataArray,
    co2_within_canopy: DataArray,
    co2_below_canopy: DataArray,
    mixing: bool,
) -> DataArray:
    r"""Vertical mixing of CO\ :sub:`2`\.

    Args:
        co2_above_canopy: CO\ :sub:`2`\ concentration above canopy, [ppm]
        co2_within_canopy: CO\ :sub:`2`\ concentration within canopy, [ppm]
        co2_below_canopy: CO\ :sub:`2`\ concentration below canopy, [ppm]
        mixing: flag if mixing is true or false
    """

    if mixing:
        raise (NotImplementedError)
    else:
        co2_profile_mixed = xr.concat(
            [
                co2_above_canopy,
                co2_within_canopy,
                co2_below_canopy,
            ],
            dim="atmosphere_layers",
        )

    return co2_profile_mixed
