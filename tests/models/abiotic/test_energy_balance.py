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


def test_calculate_air_heat_conductivity_above(dummy_climate_data):
    """Test heat conductivity above canopy."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_air_heat_conductivity_above,
    )

    result = calculate_air_heat_conductivity_above(
        height_above_canopy=dummy_climate_data["layer_heights"][0],
        zero_displacement_height=np.array([0.0, 25.312559, 27.58673]),
        canopy_height=dummy_climate_data["layer_heights"][1],
        friction_velocity=np.array([0.051866, 0.163879, 0.142353]),
        molar_density_air=np.repeat(28.96, 3),
        adiabatic_correction_heat=np.array([0.003044, -0.036571, 0.042159]),
        von_karmans_constant=CoreConsts.von_karmans_constant,
    )
    np.testing.assert_allclose(
        result,
        np.array([5.067245, 5.147202, 2.508593]),
        rtol=1e-04,
        atol=1e-04,
    )


def test_calculate_air_heat_conductivity_canopy():
    """Test calculate air heat conductivity in canopy."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_air_heat_conductivity_canopy,
    )

    result = calculate_air_heat_conductivity_canopy(
        attenuation_coefficient=np.repeat(13.0, 3),
        mean_mixing_length=np.repeat(1.3, 3),
        molar_density_air=np.repeat(28.96, 3),
        upper_height=np.repeat(10.0, 3),
        lower_height=np.repeat(5.0, 3),
        relative_turbulence_intensity=np.repeat(15.0, 3),
        top_of_canopy_wind_speed=np.repeat(1.0, 3),
        diabatic_correction_momentum=np.repeat(0.03, 3),
        canopy_height=np.repeat(30.0, 3),
    )
    np.testing.assert_allclose(
        result,
        np.array([5.45304, 5.45304, 5.45304]),
        rtol=1e-04,
        atol=1e-04,
    )


def test_calculate_leaf_air_heat_conductivity():
    """Test calculation of leaf air heat conductivity."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_leaf_air_heat_conductivity,
    )

    result = calculate_leaf_air_heat_conductivity(
        temperature=np.full((3, 3), 20.0),
        wind_speed=np.full((3, 3), 1.0),
        characteristic_dimension_surface=np.full((3, 3), 0.1),
        temperature_difference=np.full((3, 3), 1.0),
        molar_density_air=np.full((3, 3), 28.96),
        kinematic_viscosity_parameter1=AbioticConsts.kinematic_viscosity_parameter1,
        kinematic_viscosity_parameter2=AbioticConsts.kinematic_viscosity_parameter2,
        thermal_diffusivity_parameter1=AbioticConsts.thermal_diffusivity_parameter1,
        thermal_diffusivity_parameter2=AbioticConsts.thermal_diffusivity_parameter2,
        grashof_parameter=AbioticConsts.grashof_parameter,
        forced_conductance_parameter=AbioticConsts.forced_conductance_parameter,
        positive_free_conductance_parameter=(
            AbioticConsts.positive_free_conductance_parameter
        ),
        negative_free_conductance_parameter=(
            AbioticConsts.negative_free_conductance_parameter
        ),
    )
    np.testing.assert_allclose(result, np.full((3, 3), 0.15279), rtol=1e-04, atol=1e-04)


def test_calculate_leaf_vapor_conductivity():
    """Test calculate leaf vapor conductivity."""

    from virtual_rainforest.models.abiotic.energy_balance import (
        calculate_leaf_vapor_conductivity,
    )

    result = calculate_leaf_vapor_conductivity(
        leaf_air_conductivity=np.repeat(5.0, 3),
        stomatal_conductance=np.repeat(5.0, 3),
    )
    np.testing.assert_allclose(result, np.repeat(2.5, 3), rtol=1e-04, atol=1e-04)
