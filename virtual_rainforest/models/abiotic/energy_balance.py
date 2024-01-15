r"""The ``models.abiotic.energy_balance`` module calculates the energy balance for the
Virtual Rainforest. Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapour exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly. Under steady-state,
the balance equation for the leaves in each canopy layer is as follows (after
:cite:t:`maclean_microclimc_2021`):

.. math::
    R_{abs} - R_{em} - H - \lambda E
    = R_{abs} - \epsilon_{s} \sigma T_{L}^{4} - c_{P}g_{Ha}(T_{L} - T_{A})
    - \lambda g_{v} \frac {e_{L} - e_{A}}{p_{A}} = 0

where :math:`R_{abs}` is absorbed radiation, :math:`R_{em}` emitted radiation, :math:`H`
the sensible heat flux, :math:`\lambda E` the latent heat flux, :math:`\epsilon_{s}` the
emissivity of the leaf, :math:`\sigma` the Stefan-Boltzmann constant, :math:`T_{L}` the
absolute temperature of the leaf, :math:`T_{A}` the absolute temperature of the air
surrounding the leaf, :math:`\lambda` the latent heat of vaporisation of water,
:math:`e_{L}` the effective vapour pressure of the leaf, :math:`e_{A}` the vapor
pressure of air and :math:`p_{A}` atmospheric pressure. :math:`g_{Ha}` is the heat
conductance between leaf and atmosphere, :math:`g_{v}` represents the conductance
for vapor loss from the leaves as a function of the stomatal conductance.

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. We use a linearisation approach to solve the equation for
leaf temperature and air temperature simultaneously, see
:cite:t:`maclean_microclimc_2021`.

For soils, the sensible and latent heat fluxes are given by:

:math:`H^{S} = \frac {\rho_{air} C_{air} (T_{S} - T_{b}^{A})}{r_{A}}`

:math:`Q^{S} = \frac {\rho_{air} \lambda (q_{*}(T_{b}^{A}) - q_{b}^{A})}{r_{A}}`

Where :math:`T_{S}` is the soil surface temperature, :math:`T_{b}^{A}` and
:math:`q_{b}^{A}` are the temperature and specific humidity of the bottom air layer and
:math:`r_{A}` is the aerodynamic resistance of the soil surface, given by

:math:`r_{A} = \frac {C_{S}}{u_{b}}`

Where :math:`u_{b}` is the wind speed in the bottom air layer and :math:`C_{S}` is the
soil surface heat transfer coefficient.

In the soil, heat storage is almost always significant. Thus, Fourier's Law is combined
with the continuity equation to obtain a time dependant differential equation that
describes soil temperature as a function of depth and time. A numerical solution can be
achieved by dividing the soil into discrete layers. Each layer is assigned a node,
:math:`i`, at depth, :math:`z_{i}`, and with heat storage, :math:`C_{h_{i}}`, and nodes
are numbered sequentially downward such that node :math:`i+1` represents the
node for the soil layer immediately below. Conductivity, :math:`k_{i}`, represents
conductivity between nodes :math:`i` and :math:`i+1`. The energy balance equation for
node :math:`i` is then given by

.. math::
    \kappa_{i}(T_{i+1} - T_{i})- \kappa_{i-1}(T_{i} - T_{i-1})
    = \frac{C_{h_{i}}(T_{i}^{j+1} - T_{i}^{j})(z_{i+1} - z_{i-1})}{2 \Delta t}

where :math:`\Delta t` is the time increment, conductance,
:math:`\kappa_{i}=k_{i}/(z_{i+1} - z_{i})`,  and superscript :math:`j` indicates the
time at which temperature is determined. This equation can be re-arranged and solved for
:math:`T_{j+1}` by Gaussian elimination using the Thomas algorithm.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray


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

    :math:`I(z) = I_{0} * exp(-k * LAI * z)`

    Args:
        topofcanopy_radiation: top of canopy radiation shortwave radiation, [J m-2]
        leaf_area_index: leaf area index of each canopy layer, [m m-1]
        layer_heights: layer heights, [m]
        light_extinction_coefficient: light extinction coefficient, [m-1]

    Returns:
        shortwave radiation absorbed by canopy layers, [J m-2]
    """

    absorbed_radiation = np.zeros_like(leaf_area_index)
    penetrating_radiation = np.zeros_like(leaf_area_index)
    layer_depths = np.abs(np.diff(layer_heights, axis=1, append=0))
    for i in range(len(layer_heights[0])):
        penetrating_radiation[:, i] = topofcanopy_radiation * (
            np.exp(
                -light_extinction_coefficient
                * leaf_area_index[:, i]
                * layer_depths[:, i]
            )
        )
        absorbed_radiation[:, i] = topofcanopy_radiation - penetrating_radiation[:, i]
        topofcanopy_radiation -= topofcanopy_radiation - penetrating_radiation[:, i]

    return absorbed_radiation


def initialise_canopy_temperature(
    air_temperature: NDArray,
    absorbed_radiation: NDArray,
    canopy_temperature_ini_factor: float,
) -> NDArray:
    """Initialise canopy temperature.

    Args:
        air_temperature: air temperature, [C]
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation
        absorbed_radiation: shortwave radiation absorbed by canopy
    Returns:
        initial canopy temperature, [C]
    """
    return air_temperature + canopy_temperature_ini_factor * absorbed_radiation


def initialise_canopy_and_soil_fluxes(
    air_temperature: DataArray,
    topofcanopy_radiation: DataArray,
    leaf_area_index: DataArray,
    layer_heights: DataArray,
    light_extinction_coefficient: float,
    canopy_temperature_ini_factor: float,
) -> dict[str, DataArray]:
    """Initialise canopy temperature and energy fluxes.

    This function initializes the following variables to run the first step of the
    energy balance routine: absorbed radiation (canopy), canopy temperature, sensible
    and latent heat flux (canopy and soil), and ground heat flux.

    Args:
        air_temperature: air temperature, [C]
        topofcanopy_radiation: top of canopy radiation, [W m-2]
        leaf_area_index: Leaf area index, [m m-2]
        layer_heights: Layer heights, [m]
        light_extinction_coefficient: Light extinction coefficient for canopy
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation

    Returns:
        dictionnary with absorbed radiation (canopy), canopy temperature, sensible
            and latent heat flux (canopy and soil), and ground heat flux.
    """

    output = {}
    # select canopy layers with leaf area index != nan
    leaf_area_index_true = leaf_area_index[
        leaf_area_index["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    layer_heights_canopy = layer_heights[
        leaf_area_index["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    air_temperature_canopy = air_temperature[
        leaf_area_index["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")

    # Initialize absorbed radiation DataArray
    absorbed_radiation = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="canopy_absorption",
    )

    # calculate absorbed radiation
    initial_absorbed_radiation = initialise_absorbed_radiation(
        topofcanopy_radiation=topofcanopy_radiation.to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.T.to_numpy(),  # TODO check if .T is needed
        light_extinction_coefficient=light_extinction_coefficient,
    )

    # Replace np.nan with new values and write in output dict
    absorbed_radiation[layer_heights_canopy.indexes] = initial_absorbed_radiation
    output["canopy_absorption"] = absorbed_radiation

    # Initialize canopy temperature
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
    canopy_temperature[layer_heights_canopy.indexes] = initial_canopy_temperature
    output["canopy_temperature"] = canopy_temperature

    # Initialise sensible heat flux with zeros and write in output dict
    sensible_heat_flux = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="canopy_temperature",
    )
    sensible_heat_flux[layer_heights_canopy.indexes] = 0
    sensible_heat_flux[layer_heights["layer_roles"] == "surface"] = 0
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
    ground_heat_flux[layer_heights["layer_roles"] == "surface"] = 0
    output["ground_heat_flux"] = ground_heat_flux

    return output
