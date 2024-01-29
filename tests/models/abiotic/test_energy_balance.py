"""Test module for abiotic.abiotic_model.energy_balance.py."""

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


def test_initialise_conductivities(dummy_climate_data, layer_roles_fixture):
    """Test conductivities are initialised correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        initialise_conductivities,
    )

    result = initialise_conductivities(
        layer_heights=dummy_climate_data["layer_heights"],
        initial_air_conductivity=50.0,
        top_leaf_vapor_conductivity=0.32,
        bottom_leaf_vapor_conductivity=0.25,
        top_leaf_air_conductivity=0.19,
        bottom_leaf_air_conductivity=0.13,
    )

    air_cond_values = np.repeat(
        a=[3.84615385, 3.33333333, 6.66666667, np.nan], repeats=[1, 11, 1, 2]
    )
    exp_air_cond = DataArray(
        np.broadcast_to(air_cond_values, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles_fixture),
            "cell_id": [0, 1, 2],
        },
        name="air_conductivity",
    )

    leaf_vap_values = np.repeat(
        a=[0.25, 0.254389, 0.276332, 0.298276, np.nan, 0.316928, 0.32, np.nan],
        repeats=[1, 1, 1, 1, 7, 1, 1, 2],
    )
    exp_leaf_vap_cond = DataArray(
        np.broadcast_to(leaf_vap_values, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles_fixture),
            "cell_id": [0, 1, 2],
        },
        name="leaf_vapor_conductivity",
    )

    leaf_air_values = np.repeat(
        a=[0.13, 0.133762, 0.152571, 0.171379, np.nan, 0.187367, 0.19, np.nan],
        repeats=[1, 1, 1, 1, 7, 1, 1, 2],
    )
    exp_leaf_air_cond = DataArray(
        np.broadcast_to(leaf_air_values, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles_fixture),
            "cell_id": [0, 1, 2],
        },
        name="leaf_air_conductivity",
    )

    np.testing.assert_allclose(
        result["air_conductivity"], exp_air_cond, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_vapor_conductivity"], exp_leaf_vap_cond, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_air_conductivity"], exp_leaf_air_cond, rtol=1e-04, atol=1e-04
    )


def test_interpolate_along_heights(dummy_climate_data):
    """Test linear interpolation along heights."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        interpolate_along_heights,
    )

    layer_heights = dummy_climate_data["layer_heights"]
    atmosphere_layers = layer_heights[layer_heights["layer_roles"] != "soil"]
    result = interpolate_along_heights(
        start_height=layer_heights[-3].to_numpy(),
        end_height=layer_heights[-0].to_numpy(),
        target_heights=(layer_heights[atmosphere_layers.indexes].to_numpy()),
        start_value=50.0,
        end_value=20.0,
    )
    exp_result = np.concatenate(
        [
            [
                [20.0, 20.0, 20.0],
                [21.88087774, 21.88087774, 21.88087774],
                [31.28526646, 31.28526646, 31.28526646],
                [40.68965517, 40.68965517, 40.68965517],
            ],
            [[np.nan, np.nan, np.nan]] * 7,
            [[48.68338558, 48.68338558, 48.68338558], [50.0, 50.0, 50.0]],
        ],
        axis=0,
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_soil_absorption():
    """Test that soil absorption is calculated correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_soil_absorption,
    )

    result = calculate_soil_absorption(
        shortwave_radiation_surface=np.array([100, 10, 0]),
        surface_albedo=np.array([0.2, 0.2, 0.2]),
    )

    np.testing.assert_allclose(result, np.array([80, 8, 0]))


def test_calculate_soil_longwave_emission():
    """Test that longwave radiation is calculated correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_soil_longwave_emission,
    )

    result = calculate_soil_longwave_emission(
        topsoil_temperature=np.array([290, 290, 290]),
        soil_emissivity=AbioticConsts.soil_emissivity,
        stefan_boltzmann=CoreConsts.stefan_boltzmann_constant,
    )
    np.testing.assert_allclose(result, np.array([320.843847, 320.843847, 320.843847]))


def test_calculate_sensible_heat_flux_soil():
    """Test sensible heat from soil is calculated correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_sensible_heat_flux_soil,
    )

    result = calculate_sensible_heat_flux_soil(
        air_temperature_surface=np.array([290, 290, 290]),
        topsoil_temperature=np.array([295, 290, 285]),
        molar_density_air=np.array([38, 38, 38]),
        specific_heat_air=np.array([29, 29, 29]),
        wind_speed_surface=np.array([0.1, 0.1, 0.1]),
        soil_surface_heat_transfer_coefficient=12.5,
    )
    np.testing.assert_allclose(result, np.array([4.408, 0.0, -4.408]))


def test_calculate_latent_heat_flux_from_soil_evaporation():
    """Test evaporation to latent heat flux conversion works correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_latent_heat_flux_from_soil_evaporation,
    )

    result = calculate_latent_heat_flux_from_soil_evaporation(
        soil_evaporation=np.array([0.001, 0.01, 0.1]),
        latent_heat_vaporisation=2254.0,
    )
    np.testing.assert_allclose(result, np.array([2.254, 22.54, 225.4]))
