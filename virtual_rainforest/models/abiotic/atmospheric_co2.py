r"""The ``models.abiotic.atmospheric_co2`` module calculates the within- and below-
canopy :math:`\ce{CO2}` profile for the Virtual Rainforest.

Based on external inputs, the module interpolates an initial vertical
:math:`\ce{CO2}` profile which is then modified by plant net carbon assimilation and
soil and animal respiration and vertically mixed based on the wind profiles above,
within, and below the canopy (the mixing is currently not implemented).

TODO cross-check input variable names with other modules
TODO update indexing vertical dimension
"""  # noqa: D205, D415

import xarray as xr
from xarray import DataArray


def calculate_co2_profile(
    atmospheric_co2_topofcanopy: DataArray,
    plant_net_co2_assimilation: DataArray,
    soil_respiration: DataArray,
    animal_respiration: DataArray,
    atmosphere_layers: int,  # from config?
    initialisation_method: str = "homogenous",
    mixing: bool = False,
) -> DataArray:
    r"""Calculate :math:`\ce{CO2}` profile.

    Args:
        atmospheric_co2_topofcanopy: atmospheric :math:`\ce{CO2}` at the top pf canopy,
            [ppm]
        plant_net_co2_assimilation: plant net :math:`\ce{CO2}` assimilation, [ppm]
        soil_respiration: soil respiration, [ppm]
        animal_respiration: animal respiration, [ppm]
        atmosphere_layers: number of atmosphere layers for which :math:`\ce{CO2}`
            concentration is calculated
        initialisation_method: interpolation method, default copies top-of-canopy
            :math:`\ce{CO2}` concentration to all vertical levels
        mixing: flag if mixing is true or false

    Returns:
        vertical profile of :math:`\ce{CO2}` concentrations, [ppm]
    """

    # initialise CO2 profile
    initial_co2_profile = initialise_co2_profile(
        atmospheric_co2_topofcanopy=atmospheric_co2_topofcanopy,
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
        mixing=mixing,
    )

    return co2_profile_mixed


# helper functions
def initialise_co2_profile(
    atmospheric_co2_topofcanopy: DataArray,
    atmosphere_layers: int,
    initialisation_method: str = "homogenous",
) -> DataArray:
    r"""Initialise :math:`\ce{CO2}` profile.

    Args:
        atmospheric_co2_topofcanopy: atmospheric :math:`\ce{CO2}` concentration at the
            top of canopy, [ppm]
        atmosphere_layers: number of atmosphere layers for which :math:`\ce{CO2}`
             concentration is calculated
        initialisation_method: interpolation method for initial :math:`\ce{CO2}`
            profile, default copies atmospheric :math:`\ce{CO2}` concentration to all
            vertical levels

    Returns:
        initial vertical :math:`\ce{CO2}` profile, [ppm]
    """

    if initialisation_method != "homogenous":
        raise (NotImplementedError("This method is not implemented"))

    else:
        initial_co2_profile = DataArray(
            atmospheric_co2_topofcanopy.expand_dims(
                dim={"atmosphere_layers": atmosphere_layers}
            )
        )
    return initial_co2_profile


def calculate_co2_within_canopy(
    initial_co2_profile: DataArray,
    plant_net_co2_assimilation: DataArray,
) -> DataArray:
    r"""Calculate :math:`\ce{CO2}` concentration within canopy.

    This function subtracts the net :math:`\ce{CO2}` assimilation of plants from the
    atmospheric :math:`\ce{CO2}` level. Make sure that the initial_co2_profile has the
    same dimensions as the canopy.

    Args:
        initial_co2_profile: initial :math:`\ce{CO2}` profile, [ppm]
        plant_net_co2_assimilation: plant net canron assimilation, [ppm]

    Returns:
        :math:`\ce{CO2}` concentration within canopy, [ppm]
    """
    plant_net_co2_assimilation_newaxis = plant_net_co2_assimilation.rename(
        {"canopy_layers": "atmosphere_layers"}
    )
    return initial_co2_profile - plant_net_co2_assimilation_newaxis


def calculate_co2_below_canopy(
    initial_co2_profile: DataArray,
    soil_respiration: DataArray,
    animal_respiration: DataArray,
) -> DataArray:
    r"""Calculate :math:`\ce{CO2}` concentration below canopy.

    This function adds the net respiration of soil organisms and animals to the
    atmospheric :math:`\ce{CO2}` level. Make sure that the initial_co2_profile has the
    same dimensions as layers below canopy.

    Args:
        initial_co2_profile: initial :math:`\ce{CO2}` profile, [ppm]
        soil_respiration: soil respiration, [ppm]
        animal_respiration: animal respiration, [ppm]

    Returns:
        :math:`\ce{CO2}` concentration below canopy, [ppm]
    """
    return initial_co2_profile + soil_respiration + animal_respiration


def vertical_mixing_co2(
    co2_above_canopy: DataArray,
    co2_within_canopy: DataArray,
    co2_below_canopy: DataArray,
    mixing: bool,
) -> DataArray:
    r"""Vertical mixing of :math:`\ce{CO2}`.

    Args:
        co2_above_canopy: :math:`\ce{CO2}` concentration above canopy, [ppm]
        co2_within_canopy: :math:`\ce{CO2}` concentration within canopy, [ppm]
        co2_below_canopy: :math:`\ce{CO2}` concentration below canopy, [ppm]
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
