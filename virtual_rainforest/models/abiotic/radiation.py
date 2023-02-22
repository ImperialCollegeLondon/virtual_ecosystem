"""The `abiotic.radiation` module.

The radiation balance at the top of the canopy at a given location depends on

1. extra-terrestrial radiation (affected by the earth's orbit, date, and location),
2. terrestrial radiation (affected by atmospheric composition and clouds),
3. topography (elevation, slope and aspect),
4. surface albedo (vegetation type and fraction of vegetation/bare soil), and
5. emitted longwave radiation.

The preprocessing module takes extra-terrestrial radiation as an input and adjusts for
the effects of topography (slope and aspect). Here, the effects of atmospheric
filtering (elevation-dependent) and cloud cover are added to calculate photosynthetic
photon flux density (PPFD) at the top of the canopy which is a crucial input to the
plant module. The implementation is based on :cite:t:`davis_simple_2017`.

Cloud cover and surface albedo also determine how much of the shortwave radiation that
reaches the top of the canopy is reflected and how much remains to be absorbed via
photosynthesis and re-emitted as longwave radiation by vegetation and forest floor.
At this stage, scattering and re-absorption of longwave radiation are not considered.

# TODO include time dimension, i.e. calculate toc radiation and ppdf for full time
# series (possibly as part of AbioticModel) and update other variables for each time
# step with inputs from other modules via the data object (for example absorbed
# radiation from the plant module)
"""

from dataclasses import dataclass
from typing import Union

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.base_model import InitialisationError
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER


# In the future, we want to import the RadiationConstants dataclass here
@dataclass
class RadiationConstants:
    """Radiation constants dataclass."""

    cloudy_transmissivity: float = 0.25
    """Cloudy transmittivity :cite:p:`linacre_estimating_1968`"""
    transmissivity_coefficient: float = 0.50
    """Angular coefficient of transmittivity :cite:p:`linacre_estimating_1968`"""
    flux_to_energy: float = 2.04
    """From flux to energy conversion, umol J-1 :cite:p:`meek_generalized_1984`"""
    stefan_boltzmann_constant: float = 5.67e-8
    """Stefan-Boltzmann constant W m-2 K-4"""
    soil_emissivity: float = 0.95
    """Soil emissivity, default for tropical rainforest"""
    canopy_emissivity: float = 0.95
    """Canopy emissivity, default for tropical rainforest"""
    beer_regression: float = 2.67e-5
    """Parameter in equation for atmospheric transmissivity based on regression of
    Beer's radiation extinction function :cite:p:`allen_assessing_1996`"""
    celsius_to_kelvin: float = 273.15
    """Factor to convert temperature in Celsius to absolute temperature in Kelvin"""
    albedo_vis_default: float = 0.03
    """Default value for visible light albedo."""
    albedo_shortwave_default: float = 0.17
    """Default value for shortwave light albedo."""


class Radiation:
    """Radiation class.

    This class uses a :class:`~virtual_rainforest.core.data.Data` object to populate
    and store radiation-related attributes which serve as inputs to other modules.
    Elevation information from a digital elevation model is used for the topographic
    adjustment of incoming shortwave radiation. The gross radiation that reaches the top
    of the canopy is reduced as it penetrates through the canopy (the absorption by
    individual canopy layers is provided by the plants module). What remains is the net
    shortwave radiation at the surface (= forest floor), which is an input to the
    :class:`~virtual_rainforest.models.abiotic.Energy_balance` class. Top of canopy
    photosynthetic photon flux density (PPFD) is the key input for
    `virtual_rainforest.models.plants` which calculates photosythesis and GPP.
    Longwave radiation from individual canopy layers and longwave radiation from soil
    serve as inputs to the :class:`~virtual_rainforest.models.abiotic.Energy_balance`
    class.

    PPFD and top-of-canopy radiation could be calculated in the AbioticModel __init__
    for all timesteps provided in data. Something like a `calculate_radiation_balance`
    function could then update the `longwave_canopy`,`longwave_soil` and
    `netsurface_radiation` attributes with each time step. This is currently not fully
    implemented.

    Creating an instance of this class expects a `data` object that contains the
    following variables:
    * elevation: elevation above sea level, [m]
    * shortwave_in: downward shortwave radiation, [J m-2]
    * canopy_temperature: canopy temperature of individual layers, [C]
    * surface_temperature: surface soil temperature, [C]
    * canopy_absorption: absorption by canopy, [J m-2]

    The `data` object can also optionally provide these variables, but will default to
    the values given below:
    * albedo_vis: visible light albedo, albeoo_vis_default = 0.03
    * albedo_shortwave: shortwave albedo, albedo_shortwave_default = 0.17
    * sunshine_fraction: fraction of sunshine hours, between 0 (100% cloud cover)
    and 1 (cloud free sky), default = 1

    The ``const`` argument takes an instance of class
    :class:`~virtual_rainforest.models.abiotic.radiation.RadiationConstants`, which
    provides a user modifiable set of required constants.

    Args:
        data: A Virtual Rainforest Data object.
        const: A RadiationConstants instance.
    """

    def __init__(
        self, data: Data, const: RadiationConstants = RadiationConstants()
    ) -> None:
        # check that elevation is above sea level
        # TODO check if equation permits negative values -> set to sea level
        if data["elevation"].any() < 0:
            to_raise = InitialisationError(
                "Initial elevation contains at least one negative value!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Set the default values if variables not provided in data
        sunshine_fraction: Union[DataArray, float]
        if "sunshine_fraction" not in data:
            sunshine_fraction = 1
        else:
            sunshine_fraction = data["sunshine_fraction"]

        albedo_vis: Union[DataArray, float]
        if "albedo_vis" not in data:
            albedo_vis = const.albedo_vis_default
        else:
            albedo_vis = data["albedo_vis"]

        albedo_shortwave: Union[DataArray, float]
        if "albedo_shortwave" not in data:
            albedo_shortwave = const.albedo_shortwave_default
        else:
            albedo_shortwave = data["albedo_shortwave"]

        # calculate atmospheric transmissivity (tau), unitless
        tau = calculate_atmospheric_transmissivity(
            data["elevation"],
            sunshine_fraction,
            const.cloudy_transmissivity,
            const.transmissivity_coefficient,
            const.beer_regression,
        )

        # ppfd and topofcanopy_radiation radiation could be calculated across all time
        # steps in the abiotic module __init__. Leaving here for now.
        self.ppfd: DataArray = calculate_ppfd(
            tau=tau,
            shortwave_in=data["shortwave_in"],
            albedo_vis=albedo_vis,
            flux_to_energy=const.flux_to_energy,
        )
        """Top of canopy photosynthetic photon flux density, [mol m-2]"""

        self.topofcanopy_radiation: DataArray = calculate_topofcanopy_radiation(
            tau=tau,
            shortwave_in=data["shortwave_in"],
            albedo_shortwave=albedo_shortwave,
        )
        """Top of canopy downward shortwave radiation, [J m-2]"""

        self.longwave_canopy: DataArray = calculate_longwave_radiation(
            temperature=data["canopy_temperature"],
            emissivity=const.canopy_emissivity,
            stefan_boltzmann_constant=const.stefan_boltzmann_constant,
            celsius_to_kelvin=const.celsius_to_kelvin,
        )
        """Longwave radiation from canopy layers, [J m-2]"""

        self.longwave_soil: DataArray = calculate_longwave_radiation(
            temperature=data["surface_temperature"],
            emissivity=const.soil_emissivity,
            stefan_boltzmann_constant=const.stefan_boltzmann_constant,
            celsius_to_kelvin=const.celsius_to_kelvin,
        )
        """Longwave radiation from soil, [J m-2]"""

        self.netradiation_surface: DataArray = calculate_netradiation_surface(
            topofcanopy_radiation=self.topofcanopy_radiation,
            canopy_absorption=data["canopy_absorption"],
            longwave_canopy=self.longwave_canopy,
            longwave_soil=self.longwave_soil,
        )
        """Net shortwave radiation at the surface (= forest floor), [J m-2]"""


# helper functions
def calculate_atmospheric_transmissivity(
    elevation: DataArray,
    sunshine_fraction: DataArray = DataArray([1.0], dims=["cell_id"]),
    cloudy_transmissivity: float = RadiationConstants.cloudy_transmissivity,
    transmissivity_coefficient: float = RadiationConstants.transmissivity_coefficient,
    beer_regression: float = RadiationConstants.beer_regression,
    # const: RadiationConstants = RadiationConstants() ## alternative approach
) -> DataArray:
    """Calculate atmospheric transmissivity (tau).

    Atmospheric transmissivity (tau)influences the surface energy balance by determining
    the fraction of incoming solar radiation reaching the surface to the one at the top
    of the atmosphere. The main factors affecting tau are fraction of sunshine hours and
    elevation, and atmospheric composition (represented by transmissivity coefficients
    here).

    Args:
        elevation: elevation above sea level, [m]
        sunshine_fraction: fraction of sunshine hours, between 0 (100% cloud cover)
            and 1 (cloud free sky), default = 1
        cloudy_transmissivity: cloudy transmittivity :cite:p:`linacre_estimating_1968`,
            default set in config
        transmissivity_coefficient: angular coefficient of transmittivity
            :cite:p:`linacre_estimating_1968`, default set in config
        beer_regression: parameter in equation for atmospheric transmissivity based on
            regression of Beer's radiation extinction function
            :cite:p:`allen_assessing_1996`, default set in config

    Returns:
        atmospheric transmissivity, unitless
    """

    # check sunshine fraction between 0 and 1
    if not np.all(np.logical_and(0 <= sunshine_fraction, sunshine_fraction <= 1)):
        to_raise = InitialisationError(
            "The fraction of sunshine hours needs to be between 0 and 1!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    # calculate transmissivity
    tau_o = cloudy_transmissivity + transmissivity_coefficient * sunshine_fraction
    return tau_o * (1.0 + beer_regression * elevation)


def calculate_ppfd(
    tau: DataArray,
    shortwave_in: DataArray,
    albedo_vis: Union[DataArray, float] = RadiationConstants.albedo_vis_default,
    flux_to_energy: float = RadiationConstants.flux_to_energy,
) -> DataArray:
    """Calculate top of canopy photosynthetic photon flux density, [mol m-2].

    Args:
        tau: atmospheric transmissivity, unitless
        shortwave_in: downward shortwave radiation, [J m-2]
        albedo_vis: visible light albedo, albedo_vis_default = 0.03
        flux_to_energy: flux to energy conversion factor, [umol J-1],default from config

    Returns:
        photosynthetic photon flux density, [mol m-2]

    Reference: :cite:t:`davis_simple_2017`
    """

    return (1.0e-6) * flux_to_energy * (1.0 - albedo_vis) * tau * shortwave_in


def calculate_topofcanopy_radiation(
    tau: DataArray,
    shortwave_in: DataArray,
    albedo_shortwave: Union[
        DataArray, float
    ] = RadiationConstants.albedo_shortwave_default,
) -> DataArray:
    """Calculate top of canopy shortwave radiation, [J m-2].

    Args:
        tau: atmospheric transmissivity, unitless
        shortwave_in: downward shortwave radiation, [J m-2]
        albedo_shortwave: shortwave albedo, albedo_shortwave_default = 0.17

    Returns:
        top of canopy radiation shortwave radiation, [J m-2]
    """

    return (1.0 - albedo_shortwave) * tau * shortwave_in


def calculate_longwave_radiation(
    temperature: DataArray,
    emissivity: float = 0.95,
    stefan_boltzmann_constant: float = RadiationConstants.stefan_boltzmann_constant,
    celsius_to_kelvin: float = RadiationConstants.celsius_to_kelvin,
) -> DataArray:
    """Calculate longwave emission, [J m-2].

    Longwave radiation is calculated following the Stefan-Boltzmann law as a function of
    surface temperature (in Kelvin) to the fourth power.

    Args:
        temperature: canopy or soil temperature of n layers, [C]; the array size is
            set to max number of layers (n_max) and filled with NaN where n < n_max
        emissivity: canopy or soil emissivity, default=0.95
        stefan_boltzmann_constant: Stefan-Boltzmann constant [W m-2 K-4]
        celsius_to_kelvin: factor to convert temperature in Celsius to absolute
            temperature in Kelvin

    Returns:
        longwave radiation from n individual canopy layers or soil, [J m-2]
    """
    # TODO add sanity check for temperature and in celsius?
    # longwave emission canopy
    return (
        emissivity * stefan_boltzmann_constant * (celsius_to_kelvin + temperature) ** 4
    )


def calculate_netradiation_surface(
    topofcanopy_radiation: DataArray,
    canopy_absorption: DataArray,
    longwave_canopy: DataArray,
    longwave_soil: DataArray,
) -> DataArray:
    """Calculate net shortwave radiation at the surface, [J m-2].

    The net shortwave radiation (RN) at the forest floor is calculated as
    `topofcanopy_radiation` - `canopy_absorption` (summed over all canopy layers)
    - `longwave_canopy` (summed over all canopy layers) - `longwave_soil`.

    Canopy_absorption and longwave_canopy must include the dimension `canopy_layers` and
    have the correct length (length of cell_id).

    Args:
        topofcanopy_radiation: top of canopy radiation shortwave radiation, [J m-2]
        canopy_absorption: shortwave radiation absorbed by canopy layers, [J m-2]
        longwave_canopy: longwave radiation from canopy layers, [J m-2]
        longwave_soil: longwave radiation from soil layers, [J m-2]

    Returns:
        net shortwave radiation at the surface ( = forest floor), [J m-2]
    """

    return (
        topofcanopy_radiation
        - canopy_absorption.sum(dim="canopy_layers")
        - longwave_canopy.sum(dim="canopy_layers")
        - longwave_soil
    )
