"""The ``models.abiotic.atmospheric_co2`` module calculates the within- and below-
canopy CO2 profile for the Virtual Rainforest.

Based on external inputs, the module interpolates a vertical CO2 profile which is
then modified by plant net carbon assimilation and soil and animal respiration and
vertically mixed based on the windprofiles above, within, and below the canopy (the
mixing is currently not implemented).
"""  # noqa: D205, D415


import xarray as xr
from xarray import DataArray

# data object use?


def calculate_co2_profile(
    ambient_atmsopheric_co2: DataArray,
    plant_net_co2_assimilation: DataArray,
    soil_respiration: DataArray,
    animal_respiration: DataArray,
    atmosphere_layers: int,
    method: str,
) -> DataArray:
    """Calculate CO2 profile."""
    # initialise CO2 profile
    initial_co2_profile = initialise_co2_profile(
        ambient_atmsopheric_co2=ambient_atmsopheric_co2,
        atmosphere_layers=atmosphere_layers,
        method=method,
    )

    # Calculate CO2 within canopy
    co2_within_canopy = calculate_co2_within_canopy(
        initial_co2_profile=initial_co2_profile,
        plant_net_co2_assimilation=plant_net_co2_assimilation,
    )
    # Calculate CO2 below canopy
    co2_below_canopy = calculate_co2_below_canopy(
        initial_co2_profile=initial_co2_profile,
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

    # update data object


# helper functions
def initialise_co2_profile(
    ambient_atmsopheric_co2: DataArray,
    atmosphere_layers: int,
    method: str = "homogenous",
) -> DataArray:
    """Initialise CO2 profile.

    Args:
        ambient_atmsopheric_co2: ambient CO2 concentraion, [ppm],
        atmosphere_layers: number of atmosphere layers
        method: interpolation method, default copies ambient CO2 to all vertical levels

    Returns:
        initial vertical CO2 profile, [ppm]
    """

    if method != "homogenous":
        raise (NotImplementedError("This method is not implemented"))

    else:
        initial_co2_profile = DataArray(
            ambient_atmsopheric_co2.expand_dims(
                dim={"atmosphere_layers": atmosphere_layers}
            )
        )
    return initial_co2_profile


def calculate_co2_within_canopy(
    initial_co2_profile: DataArray,
    plant_net_co2_assimilation: DataArray,
) -> DataArray:
    """Calculate CO2 concentration within canopy.

    This function subtracts the net CO2 assimilation of plants from the ambient CO2
    level. Make sure that the initial_co2_profile has the same dimensions as the canopy.

    Args:
        initial_co2_profile: initial CO2 profile, [ppm]
        plant_net_co2_assimilation: plant net canron assimilation, [ppm]

    Returns:
        CO2 concentration within canopy [ppm]
    """

    return initial_co2_profile - plant_net_co2_assimilation


def calculate_co2_below_canopy(
    initial_co2_profile: DataArray,
    soil_respiration: DataArray,
    animal_respiration: DataArray,
) -> DataArray:
    """Calculate CO2 concentration below canopy.

    This function adds the net respiration of soil organisms and animals to the ambient
    CO2 level. Make sure that the initial_co2_profile has the same dimensions as layers
    below canopy.

    Args:
        initial_co2_profile: initial CO2 profile, [ppm]
        soil_respiration: soil respiration, [ppm]
        animal_respiration: animal respiration, [ppm]

    Returns:
        CO2 concentration below canopy, [ppm]
    """
    return initial_co2_profile + soil_respiration + animal_respiration


def vertical_mixing_co2(
    co2_above_canopy: DataArray,
    co2_within_canopy: DataArray,
    co2_below_canopy: DataArray,
    mixing: bool,
) -> DataArray:
    """Vertical mixing of CO2.

    Args:
        co2_above_canopy: CO2 concentration above canopy, [ppm]
        co2_within_canopy: CO2 concentration within canopy, [ppm]
        co2_below_canopy:CO2 concentration below canopy, [ppm]
        mixing: flag if mixing true or false
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
