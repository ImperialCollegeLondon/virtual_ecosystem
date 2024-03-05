"""Test module for abiotic.energy_balance.py."""

import numpy as np
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_initialise_absorbed_radiation(dummy_climate_data):
    """Test initial absorbed radiation has correct dimensions."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_absorbed_radiation,
    )

    d = dummy_climate_data
    leaf_area_index_true = d["leaf_area_index"][
        d["leaf_area_index"]["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    layer_heights_canopy = d["layer_heights"][
        d["leaf_area_index"]["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")

    result = initialise_absorbed_radiation(
        topofcanopy_radiation=d["topofcanopy_radiation"].isel(time_index=0).to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.T.to_numpy(),  # TODO check why .T needed
        light_extinction_coefficient=0.01,
    )

    np.testing.assert_allclose(
        result,
        np.array(
            [
                [9.516258, 8.610666, 7.791253],
                [9.516258, 8.610666, 7.791253],
                [9.516258, 8.610666, 7.791253],
            ]
        ),
    )


def test_initialise_canopy_temperature(dummy_climate_data):
    """Test that canopy temperature is initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_temperature,
    )

    d = dummy_climate_data
    air_temperature = d["air_temperature"][
        d["leaf_area_index"]["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    absorbed_radiation = np.array([[9.516258, 8.610666, 7.791253]] * 3)

    exp_result = np.array(
        [
            [29.940158, 29.931102, 29.922908],
            [28.966333, 28.957277, 28.949083],
            [27.301568, 27.292512, 27.284318],
        ]
    )
    result = initialise_canopy_temperature(
        air_temperature=air_temperature,
        absorbed_radiation=absorbed_radiation,
        canopy_temperature_ini_factor=0.01,
    )
    np.testing.assert_allclose(result, exp_result)


def test_calculate_slope_of_saturated_pressure_curve():
    """Test calculation of slope of saturated pressure curve."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_slope_of_saturated_pressure_curve,
    )

    result = calculate_slope_of_saturated_pressure_curve(
        temperature=np.full((4, 3), 20.0)
    )
    exp_result = np.full((4, 3), 0.14474)
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_initialise_canopy_and_soil_fluxes(dummy_climate_data):
    """Test that canopy and soil fluxes initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_and_soil_fluxes,
    )

    result = initialise_canopy_and_soil_fluxes(
        air_temperature=dummy_climate_data["air_temperature"],
        topofcanopy_radiation=(
            dummy_climate_data["topofcanopy_radiation"].isel(time_index=0)
        ),
        leaf_area_index=dummy_climate_data["leaf_area_index"],
        layer_heights=dummy_climate_data["layer_heights"],
        light_extinction_coefficient=0.01,
        canopy_temperature_ini_factor=0.01,
    )

    for var in [
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "canopy_absorption",
    ]:
        assert var in result

    np.testing.assert_allclose(
        result["canopy_absorption"][1:4].to_numpy(),
        np.array([[9.516258, 8.610666, 7.791253]] * 3),
    )
    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        np.testing.assert_allclose(result[var][1:4].to_numpy(), np.zeros((3, 3)))
        np.testing.assert_allclose(result[var][12].to_numpy(), np.zeros(3))


def test_calculate_longwave_emission():
    """Test that longwave radiation is calculated correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_longwave_emission,
    )

    result = calculate_longwave_emission(
        temperature=np.array([290.0, 290.0, 290.0]),
        emissivity=AbioticConsts.soil_emissivity,
        stefan_boltzmann=CoreConsts.stefan_boltzmann_constant,
    )
    np.testing.assert_allclose(
        result,
        np.array([320.843847, 320.843847, 320.843847]),
        rtol=1e-04,
        atol=1e-04,
    )


def test_calculate_leaf_and_air_temperature(dummy_climate_data):
    """Test updating leaf and air temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_leaf_and_air_temperature,
    )
    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts

    result = calculate_leaf_and_air_temperature(
        data=dummy_climate_data,
        time_index=1,
        topsoil_layer_index=13,
        abiotic_constants=AbioticConsts,
        abiotic_simple_constants=AbioticSimpleConsts,
        core_constants=CoreConsts,
    )

    exp_air_temp = DataArray(
        np.concatenate(
            (
                np.array(
                    [
                        [30.0, 30.0, 30.0],
                        [29.999967, 29.999967, 29.999967],
                        [29.995432, 29.995432, 29.995432],
                        [29.504507, 29.504507, 29.504507],
                    ],
                ),
                np.full((7, 3), np.nan),
                np.array([[20.0, 20.0, 20.0], [20.0, 20.0, 20.0]]),
                np.full((2, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )

    exp_leaf_temp = DataArray(
        np.concatenate(
            (
                np.full((1, 3), np.nan),
                np.array(
                    [
                        [30.112604, 30.112604, 30.112604],
                        [29.13954, 29.13954, 29.13954],
                        [27.425342, 27.425342, 27.425342],
                    ],
                ),
                np.full((11, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )
    exp_vapour_pressure = DataArray(
        np.concatenate(
            (
                np.array(
                    [
                        [0.14, 0.14, 0.14],
                        [0.14001, 0.14001, 0.14001],
                        [0.141365, 0.141365, 0.141365],
                        [0.275612, 0.275612, 0.275612],
                    ],
                ),
                np.full((7, 3), np.nan),
                np.full((2, 3), 0.218826),
                np.full((2, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )

    exp_vpd = DataArray(
        np.concatenate(
            (
                np.array(
                    [
                        [0.098781, 0.098781, 0.098781],
                        [0.098788, 0.098788, 0.098788],
                        [0.099756, 0.099756, 0.099756],
                        [0.196887, 0.196887, 0.196887],
                    ],
                ),
                np.full((7, 3), np.nan),
                np.full((2, 3), 0.2),
                np.full((2, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )

    exp_gv = DataArray(
        np.concatenate(
            [
                [
                    [np.nan, np.nan, np.nan],
                    [0.186217, 0.186217, 0.186217],
                    [0.185638, 0.185638, 0.185638],
                    [0.184646, 0.184646, 0.184646],
                ],
                [[np.nan, np.nan, np.nan]] * 11,
            ],
        ),
        dims=["layers", "cell_id"],
    )
    np.testing.assert_allclose(result["air_temperature"], exp_air_temp)
    np.testing.assert_allclose(result["leaf_temperature"], exp_leaf_temp)
    np.testing.assert_allclose(
        result["vapour_pressure"], exp_vapour_pressure, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["vapour_pressure_deficit"], exp_vpd, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_vapour_conductivity"], exp_gv, rtol=1e-04, atol=1e-04
    )
