"""Test module for abiotic.energy_balance.py."""

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.constants import CoreConsts
from virtual_rainforest.models.abiotic.constants import AbioticConsts


def test_initialise_absorbed_radiation(dummy_climate_data):
    """Test initial absorbed radiation has correct dimensions."""

    from virtual_rainforest.models.abiotic.energy_balance import (
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

    from virtual_rainforest.models.abiotic.energy_balance import (
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

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_slope_of_saturated_pressure_curve,
    )

    result = calculate_slope_of_saturated_pressure_curve(
        temperature=np.full((4, 3), 20.0)
    )
    exp_result = np.full((4, 3), 0.14474)
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_initialise_canopy_and_soil_fluxes(dummy_climate_data):
    """Test that canopy and soil fluxes initialised correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
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

    from virtual_rainforest.models.abiotic.energy_balance import (
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

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_leaf_and_air_temperature,
    )
    from virtual_rainforest.models.abiotic_simple.constants import AbioticSimpleConsts

    result = calculate_leaf_and_air_temperature(
        data=dummy_climate_data,
        time_index=1,
        true_canopy_layers=np.full((3, 3), 1.0),
        leaf_emissivity=0.8,
        stefan_boltzmann_constant=CoreConsts.stefan_boltzmann_constant,
        saturation_vapour_pressure_factor1=(
            AbioticSimpleConsts.saturation_vapour_pressure_factor1
        ),
        saturation_vapour_pressure_factor2=(
            AbioticSimpleConsts.saturation_vapour_pressure_factor2
        ),
        saturation_vapour_pressure_factor3=(
            AbioticSimpleConsts.saturation_vapour_pressure_factor3
        ),
    )

    exp_air_temp = DataArray(
        np.concatenate(
            (
                np.array(
                    [
                        [30.0, 30.0, 30.0],
                        [29.232091, 29.232091, 29.232091],
                        [29.232091, 29.232091, 29.232091],
                        [29.232091, 29.232091, 29.232091],
                    ],
                ),
                np.full((7, 3), np.nan),
                np.array([[18, 18, 18], [18, 18, 18]]),
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
                        [30.033482, 30.033482, 30.033482],
                        [29.059657, 29.059657, 29.059657],
                        [27.394892, 27.394892, 27.394892],
                    ],
                ),
                np.full((11, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )
    exp_vapor_pressure = DataArray(
        np.concatenate(
            (
                np.array(
                    [
                        [0.14, 0.14, 0.14],
                        [0.325057, 0.325057, 0.325057],
                        [0.325057, 0.325057, 0.325057],
                        [0.325057, 0.325057, 0.325057],
                    ],
                ),
                np.full((7, 3), np.nan),
                np.full((2, 3), 0.207284),
                np.full((2, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )

    np.testing.assert_allclose(result["leaf_temperature"], exp_leaf_temp)
    np.testing.assert_allclose(result["air_temperature"], exp_air_temp)
    np.testing.assert_allclose(
        result["vapor_pressure"], exp_vapor_pressure, rtol=1e-04, atol=1e-04
    )
