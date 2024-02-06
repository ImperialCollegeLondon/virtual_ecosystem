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


def test_initialise_conductivities(dummy_climate_data, fixture_core_components):
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

    coords = {
        "layers": np.arange(15),
        "layer_roles": (
            "layers",
            fixture_core_components.layer_structure.layer_roles,
        ),
        "cell_id": [0, 1, 2],
    }

    air_cond_values = np.repeat(
        a=[3.84615385, 3.33333333, 6.66666667, np.nan], repeats=[1, 11, 1, 2]
    )
    exp_air_cond = DataArray(
        np.broadcast_to(air_cond_values, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords=coords,
        name="air_conductivity",
    )

    leaf_vap_values = np.repeat(
        a=[0.25, 0.254389, 0.276332, 0.298276, np.nan, 0.316928, 0.32, np.nan],
        repeats=[1, 1, 1, 1, 7, 1, 1, 2],
    )
    exp_leaf_vap_cond = DataArray(
        np.broadcast_to(leaf_vap_values, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords=coords,
        name="leaf_vapor_conductivity",
    )

    leaf_air_values = np.repeat(
        a=[0.13, 0.133762, 0.152571, 0.171379, np.nan, 0.187367, 0.19, np.nan],
        repeats=[1, 1, 1, 1, 7, 1, 1, 2],
    )
    exp_leaf_air_cond = DataArray(
        np.broadcast_to(leaf_air_values, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords=coords,
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

    np.testing.assert_allclose(result, np.array([80, 8, 0]), rtol=1e-04, atol=1e-04)


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
        aerodynamic_resistance=np.array([1250.0, 1250.0, 1250.0]),
    )
    np.testing.assert_allclose(
        result,
        np.array([4.408, 0.0, -4.408]),
        rtol=1e-04,
        atol=1e-04,
    )


def test_calculate_latent_heat_flux_from_soil_evaporation():
    """Test evaporation to latent heat flux conversion works correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_latent_heat_flux_from_soil_evaporation,
    )

    result = calculate_latent_heat_flux_from_soil_evaporation(
        soil_evaporation=np.array([0.001, 0.01, 0.1]),
        latent_heat_vaporisation=np.array([2254.0, 2254.0, 2254.0]),
    )
    np.testing.assert_allclose(result, np.array([2.254, 22.54, 225.4]))


def test_update_surface_temperature():
    """Test surface temperature with positive and negative radiation flux."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        update_surface_temperature,
    )

    result = update_surface_temperature(
        topsoil_temperature=np.array([297, 297, 297]),
        surface_net_radiation=np.array([100, 0, -100]),
        surface_layer_depth=np.array([0.1, 0.1, 0.1]),
        grid_cell_area=100,
        update_interval=43200,
        specific_heat_capacity_soil=AbioticConsts.specific_heat_capacity_soil,
        volume_to_weight_conversion=1000.0,
    )

    np.testing.assert_allclose(result, np.array([297.00016, 297.0, 296.99984]))


def test_calculate_ground_heat_flux():
    """Test graound heat flux is calculated correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_ground_heat_flux,
    )

    result = calculate_ground_heat_flux(
        soil_absorbed_radiation=np.array([100, 50, 0]),
        topsoil_longwave_emission=np.array([10, 10, 10]),
        topsoil_sensible_heat_flux=np.array([10, 10, 10]),
        topsoil_latent_heat_flux=np.array([10, 10, 10]),
    )
    np.testing.assert_allclose(result, np.array([70, 20, -30]))


def test_calculate_soil_heat_balance(dummy_climate_data):
    """Test full surface heat balance is run correctly."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_soil_heat_balance,
    )

    data = dummy_climate_data
    data["shortwave_radiation_surface"] = DataArray(
        np.array([100, 10, 0]), dims="cell_id"
    )
    data["soil_evaporation"] = DataArray(np.array([0.001, 0.01, 0.1]), dims="cell_id")
    data["molar_density_air"] = DataArray(
        np.full((15, 3), 38), dims=["layers", "cell_id"]
    )
    data["specific_heat_air"] = DataArray(
        np.full((15, 3), 29), dims=["layers", "cell_id"]
    )
    data["aerodynamic_resistance_surface"] = DataArray(np.repeat(1250.0, 3))
    data["latent_heat_vaporisation"] = DataArray(
        np.full((15, 3), 2254.0), dims=["layers", "cell_id"]
    )

    result = calculate_soil_heat_balance(
        data=data,
        topsoil_layer_index=13,
        update_interval=43200,
        abiotic_consts=AbioticConsts,
        core_consts=CoreConsts,
    )

    # Check if all variables were created
    var_list = [
        "soil_absorption",
        "longwave_emission_soil",
        "sensible_heat_flux_soil",
        "latent_heat_flux_soil",
        "ground_heat_flux",
    ]

    variables = [var for var in result if var not in var_list]
    assert variables

    np.testing.assert_allclose(result["soil_absorption"], np.array([87.5, 8.75, 0.0]))
    np.testing.assert_allclose(
        result["longwave_emission_soil"],
        np.repeat(0.007258, 3),
        rtol=1e-04,
        atol=1e-04,
    )
    np.testing.assert_allclose(
        result["sensible_heat_flux_soil"],
        np.repeat(3.397735, 3),
        rtol=1e-04,
        atol=1e-04,
    )
    np.testing.assert_allclose(
        result["latent_heat_flux_soil"],
        np.array([2.254, 22.54, 225.4]),
        rtol=1e-04,
        atol=1e-04,
    )
    np.testing.assert_allclose(
        result["ground_heat_flux"],
        np.array([81.841, -17.195, -228.805]),
        rtol=1e-04,
        atol=1e-04,
    )

    var_list = [
        "soil_absorption",
        "longwave_emission_soil",
        "sensible_heat_flux_soil",
        "latent_heat_flux_soil",
        "ground_heat_flux",
    ]
    variables = [var for var in result if var not in var_list]
    assert variables
