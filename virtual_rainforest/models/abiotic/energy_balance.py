r"""The ``models.abiotic.energy_balance`` module calculates the energy balance for the
Virtual Rainforest. Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapor exchange attain steady state and heat
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
:math:`e_{L}` the effective vapor pressure of the leaf, :math:`e_{A}` the vapor
pressure of air and :math:`p_{A}` atmospheric pressure. :math:`g_{Ha}` is the heat
conductance between leaf and atmosphere, :math:`g_{v}` represents the conductance
for vapor loss from the leaves as a function of the stomatal conductance :math:`g_{c}`.

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. We use a linearisation approach to solve the equation for
leaf temperature and air temperature simultaneously after
:cite:t:`maclean_microclimc_2021`, see TODO put name of equation here.

The soil energy balance functions are described in
:mod:`~virtual_rainforest.models.abiotic.soil_energy_balance`.

The conductivities are calculated as described in
:mod:`~virtual_rainforest.models.abiotic.conductivities`.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_rainforest.models.abiotic_simple.microclimate import (
    calculate_saturation_vapour_pressure,
)


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
    air_temperature: NDArray[np.float32],
    absorbed_radiation: NDArray[np.float32],
    canopy_temperature_ini_factor: float,
) -> NDArray[np.float32]:
    """Initialise canopy temperature.

    Args:
        air_temperature: Air temperature, [C]
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation
        absorbed_radiation: Shortwave radiation absorbed by canopy

    Returns:
        Initial canopy temperature, [C]
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
        air_temperature: Air temperature, [C]
        topofcanopy_radiation: Top of canopy radiation, [W m-2]
        leaf_area_index: Leaf area index, [m m-2]
        layer_heights: Layer heights, [m]
        light_extinction_coefficient: Light extinction coefficient for canopy
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation

    Returns:
        Dictionary with absorbed radiation (canopy), canopy temperature, sensible
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


def calculate_slope_of_saturated_pressure_curve(
    temperature: NDArray[np.float32],
) -> NDArray[np.float32]:
    r"""Calculate slope of the saturated pressure curve.

    TODO move factors to constants

    Args:
        temperature: Temperature, [C]

    Returns:
        Slope of the saturated pressure curve, :math:`\Delta_{v}`
    """

    return (
        4098
        * (0.6108 * np.exp(17.27 * temperature / (temperature + 237.3)))
        / (temperature + 237.3) ** 2
    )


def calculate_leaf_and_air_temperature(
    air_temperature: NDArray[np.float32],
    air_temperature_ref: NDArray[np.float32],
    vapor_pressure_ref: NDArray[np.float32],
    topsoil_temperature: NDArray[np.float32],
    true_canopy_layers: NDArray[np.float32],
    leaf_air_heat_conductivity: NDArray[np.float32],
    conductivity_from_ref_height: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    leaf_emissivity: NDArray[np.float32],
    latent_heat_vaporisation: NDArray[np.float32],
    leaf_vapor_conductivity: NDArray[np.float32],
    atmospheric_pressure: NDArray[np.float32],
    absorbed_radiation: NDArray[np.float32],
    specific_heat_air: NDArray[np.float32],
    stefan_boltzmann_constant: float | NDArray[np.float32],
    saturation_vapour_pressure_factor1: float,
    saturation_vapour_pressure_factor2: float,
    saturation_vapour_pressure_factor3: float,
) -> dict[str, DataArray]:
    r"""Calculate leaf and air temperature under steady state.

    The air temperature surrounding the leaf :math:`T_{A}` is assumed to be influenced
    by leaf temperature :math:`T_{L}`, soil temperature :math:`T_{0}`, and reference air
    temperature :math:`T_{R}` as follows:

    .. math::
        g_{tR} c_{p} (T_{R} - T_{A})
        + g_{t0} c_{p} (T_{0} - T_{A})
        + g_{L} c_{p} (T_{L} - T_{A}) = 0

    where :math:`c_{p}` is the specific heat of air at constant pressure and
    :math:`g_{tR}`, :math:`g_{t0}` and :math:`g_{L}` are conductance from reference
    height, the ground and from the leaf, respectively.
    :math:`g_{L} = 1/(1/g_{HA} + 1/g_{z})` where :math:`g_{HA}` is leaf boundary layer
    conductance and :math:`g_{z}` is the sub-canopy turbulent conductance at the height
    of the leaf over the mean distance between the leaf and the air.

    Defining :math:`T_{L} - T_{A}` as :math:`\Delta T` and rearranging gives:

    .. math:: T_{A} = a_{A} + b_{A} \Delta T_{L}

    where :math:`a_{A} = \frac{(g_{tR} T_{R} + g_{t0} T_{0})}{(g_{tR} + g_{t0})}` and
    :math:`b_{A} = \frac{g_{L}}{(g_{tR} + g_{t0})}` .

    The sensible heat flux between the leaf and the air is given by

    .. math:: g_{Ha} c_{p} (T_{L} - T_{A}) = b_{H} \Delta T_{L}

    where :math:`b_{H} = g_{Ha} c_{p}`. The equivalent vapor flux equation is

    .. math:: g_{tR}(e_{R} - e_{a}) + g_{t0} (e_{0} - e_{a}) + g_{v} (e_{L} - e_{a}) = 0

    where :math:`e_{L}`, :math:`e_{A}`, :math:`e_{0}` and :math:`e_{R}` are the vapor
    pressure of the leaf, air, soil and air at reference height, respectively, and
    :math:`g_{v}` is leaf conductance for vapor given by
    :math:`g_{v} = \frac{1}{(\frac{1}{g_{c} + g_{L})}}` where :math:`g_{c}` is stomatal
    conductance. Assuming the leaf to be saturated, and approximated by
    :math:`e_{s} [T_{R}]+\Delta_{v} [T_{R}]\Delta T_{L}` where :math:`\Delta_{v}` is the
    slope of the saturated pressure curve at temperature :math:`T_{R}`, and rearranging
    gives

    .. math:: e_{a} = a_{E} + b_{E} \Delta T_{L}

    where :math:`a_{E} = \frac{(g_{tR} e_{R} + g_{t0} e_{0} + g_{v} e_{s}[T_{R}])}
    {(g_{tR} + g_{t0} + g_{v})}` and
    :math:`b_{E} = \frac{\Delta_{V} [T_{R}])}{(g_{tR} + g_{t0} + g_{v})}`.

    The latent heat term is given by

    .. math:: \lambda E = \frac{\lambda g_{v}}{p_{a}} (e_{L} - e_{A})

    Substituting :math:`e_{A}` for its linearized form, again assuming :math:`e_{L}`
    is approximated by :math:`e_{s} [T_{R}]+\Delta_{v} [T_{R}]\Delta T_{L}`, and
    rearranging gives:

    .. math:: \lambda E = a_{L} + b_{L} \Delta T_{L},

    where :math:`a_{L} = \frac{\lambda g_{v}}{p_{a}} (e_{s} [T_{R}] - a_{E})` and
    :math:`b_{L} = \frac{\lambda g_{v}}{p_{a}} (\Delta_{V} [T_{R}] - b_{E})`.

    The radiation emitted by the leaf :math:`R_{em}` is given by the Stefan Boltzmann
    law and can be linearised as follows:

    .. math:: R_{em} = a_{R} + b_{R} \Delta T_{L}

    where :math:`a_{R} = \epsilon_{s} \sigma a_{A}^{4}` and
    :math:`b_{R} = 4 \epsilon_{s} \sigma (a_{A}^{3} b_{A} + T_{R}^{3})`.

    The full heat balance equation for the difference between leaf and canopy air
    temperature becomes

    .. math:: \Delta T_{L} = \frac{R_{abs} - a_{R} - a_{L}}{(1 + b_{R} + b_{L} + b_{H})}

    The equation is then used to calculate air and leaf temperature as follows:

    .. math:: T_{A} = a_{A} + b_{A} \Delta T_{L}

    and

    .. math:: T_{L} = T_{A} + \Delta T_{L}.

    """

    output = {}

    # Calculate vapor pressures
    soil_saturated_vapor_pressure = calculate_saturation_vapour_pressure(
        temperature=DataArray(topsoil_temperature),
        factor1=saturation_vapour_pressure_factor1,
        factor2=saturation_vapour_pressure_factor2,
        factor3=saturation_vapour_pressure_factor3,
    )
    soil_vapor_pressure = soil_moisture * soil_saturated_vapor_pressure
    saturated_vapor_pressure_ref = calculate_saturation_vapour_pressure(
        temperature=DataArray(air_temperature_ref),
        factor1=saturation_vapour_pressure_factor1,
        factor2=saturation_vapour_pressure_factor2,
        factor3=saturation_vapour_pressure_factor3,
    )

    # Calculate conductivity from soil
    conductivity_from_soil = soil_moisture * soil_saturated_vapor_pressure

    # Factors from leaf and air temperature linearisation TODO for each layer loop
    a_A_list = []
    for layer in range(0, len(true_canopy_layers)):
        a_A_layer = (
            (conductivity_from_ref_height[layer] * air_temperature_ref)
            + conductivity_from_soil * topsoil_temperature
        ) / (conductivity_from_ref_height[layer] + conductivity_from_soil)
        a_A_list.append(a_A_layer)
    a_A = np.vstack(a_A_list)

    b_A_list = []
    for layer in range(0, len(true_canopy_layers)):
        b_A_layer = leaf_air_heat_conductivity[layer] / (
            conductivity_from_ref_height[layer] + conductivity_from_soil
        )
        b_A_list.append(b_A_layer)
    b_A = np.vstack(b_A_list)

    # Factors from longwave radiative flux linearisation
    a_R = leaf_emissivity * stefan_boltzmann_constant * a_A**4
    b_R = (
        4
        * leaf_emissivity
        * stefan_boltzmann_constant
        * (a_A**3 * b_A + air_temperature_ref**3)
    )

    # Factors from vapor pressure linearisation
    delta_v_ref = calculate_slope_of_saturated_pressure_curve(air_temperature_ref)

    a_E_list = []
    for layer in range(0, len(true_canopy_layers)):
        a_E_layer = (
            conductivity_from_ref_height[layer] * vapor_pressure_ref
            + conductivity_from_soil * soil_vapor_pressure
            + leaf_vapor_conductivity[layer] * saturated_vapor_pressure_ref
        ) / (
            conductivity_from_ref_height[layer]
            + conductivity_from_soil
            + leaf_vapor_conductivity[layer]
        )
        a_E_list.append(a_E_layer)
    a_E = np.vstack(a_E_list)

    b_E_list = []
    for layer in range(0, len(true_canopy_layers)):
        b_E_layer = delta_v_ref / (
            conductivity_from_ref_height[layer]
            + conductivity_from_soil
            + leaf_vapor_conductivity[layer]
        )
        b_E_list.append(b_E_layer)
    b_E = np.vstack(b_E_list)

    # Factors from latent heat flux linearisation
    a_L_list = []
    for layer in range(0, len(true_canopy_layers)):
        a_L_layer = (
            latent_heat_vaporisation[layer] * leaf_vapor_conductivity[layer]
        ) / (atmospheric_pressure[layer] * (saturated_vapor_pressure_ref - a_E[layer]))
        a_L_list.append(a_L_layer)
    a_L = np.vstack(a_L_list)

    b_L_list = []
    for layer in range(0, len(true_canopy_layers)):
        b_L_layer = (
            latent_heat_vaporisation[layer] * leaf_vapor_conductivity[layer]
        ) / (atmospheric_pressure[layer] * (delta_v_ref - b_E[layer]))
        b_L_list.append(b_L_layer)
    b_L = np.vstack(b_L_list)

    # Factor from sensible heat flux linearisation
    b_H_list = []
    for layer in range(0, len(true_canopy_layers)):
        b_H_layer = leaf_air_heat_conductivity[layer] * specific_heat_air[layer]
        b_H_list.append(b_H_layer)
    b_H = np.vstack(b_H_list)

    # Calculate new leaf and air temperature
    delta_leaf_temperature = (absorbed_radiation - a_R - a_L) / (1 + b_R + b_L + b_H)
    new_air_temperature = a_A + b_A * delta_leaf_temperature
    new_leaf_temperature = (
        air_temperature[1 : len(true_canopy_layers) + 1] + delta_leaf_temperature
    )

    # Create arrays and return for data object
    output["air_temperature"] = DataArray(
        np.vstack(
            [
                air_temperature_ref,
                new_air_temperature,
                np.full((7, 3), np.nan),
                air_temperature[-3:-1],
                np.full((2, 3), np.nan),
            ]
        ),
        dims=["layers", "cell_id"],
    )
    output["leaf_temperature"] = DataArray(
        np.vstack(
            [
                np.repeat(np.nan, 3),
                new_leaf_temperature,
                np.full((11, 3), np.nan),
            ]
        ),
        dims=["layers", "cell_id"],
    )

    # TODO return VPD profile

    return output
