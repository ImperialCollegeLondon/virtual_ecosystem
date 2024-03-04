"""Test module for abiotic.conductivities.py."""

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.constants import CoreConsts
from virtual_rainforest.models.abiotic.constants import AbioticConsts


def test_initialise_conductivities(dummy_climate_data, fixture_core_components):
    """Test conductivities are initialised correctly."""

    from virtual_rainforest.models.abiotic.conductivities import (
        initialise_conductivities,
    )

    result = initialise_conductivities(
        layer_heights=dummy_climate_data["layer_heights"],
        initial_air_conductivity=50.0,
        top_leaf_vapour_conductivity=0.32,
        bottom_leaf_vapour_conductivity=0.25,
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
        a=[np.nan, 0.254389, 0.276332, 0.298276, np.nan],
        repeats=[1, 1, 1, 1, 11],
    )
    exp_leaf_vap_cond = DataArray(
        np.broadcast_to(leaf_vap_values, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords=coords,
        name="leaf_vapour_conductivity",
    )

    leaf_air_values = np.repeat(  # TODO there should be only 3 values
        a=[np.nan, 0.133762, 0.152571, 0.171379, np.nan],
        repeats=[1, 1, 1, 1, 11],
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
        result["leaf_vapour_conductivity"], exp_leaf_vap_cond, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_air_conductivity"], exp_leaf_air_cond, rtol=1e-04, atol=1e-04
    )


def test_interpolate_along_heights(dummy_climate_data):
    """Test linear interpolation along heights."""

    from virtual_rainforest.models.abiotic.conductivities import (
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


def test_interpolate_along_heights_arrays(dummy_climate_data):
    """Test linear interpolation along heights with arrays of boundary values."""

    from virtual_rainforest.models.abiotic.conductivities import (
        interpolate_along_heights,
    )

    layer_heights = dummy_climate_data["layer_heights"]
    atmosphere_layers = layer_heights[layer_heights["layer_roles"] != "soil"]
    result = interpolate_along_heights(
        start_height=layer_heights[-3].to_numpy(),
        end_height=layer_heights[-0].to_numpy(),
        target_heights=(layer_heights[atmosphere_layers.indexes].to_numpy()),
        start_value=np.repeat(50.0, 3),
        end_value=np.repeat(20.0, 3),
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


def test_calculate_air_heat_conductivity_above(dummy_climate_data):
    """Test heat conductivity above canopy."""

    from virtual_rainforest.models.abiotic.conductivities import (
        calculate_air_heat_conductivity_above,
    )

    result = calculate_air_heat_conductivity_above(
        height_above_canopy=dummy_climate_data["layer_heights"][0],
        zero_displacement_height=(
            dummy_climate_data["zero_displacement_height"].to_numpy()
        ),
        canopy_height=dummy_climate_data["layer_heights"][1],
        friction_velocity=dummy_climate_data["friction_velocity"][0].to_numpy(),
        molar_density_air=dummy_climate_data["molar_density_air"][0].to_numpy(),
        diabatic_correction_heat=(
            dummy_climate_data["diabatic_correction_heat"][0].to_numpy()
        ),
        von_karmans_constant=CoreConsts.von_karmans_constant,
    )
    np.testing.assert_allclose(result, np.repeat(705.63476, 3), rtol=1e-04, atol=1e-04)


def test_calculate_air_heat_conductivity_canopy(dummy_climate_data):
    """Test calculate air heat conductivity in canopy."""

    from virtual_rainforest.models.abiotic.conductivities import (
        calculate_air_heat_conductivity_canopy,
    )

    result = calculate_air_heat_conductivity_canopy(
        attenuation_coefficient=(
            dummy_climate_data["attenuation_coefficient"][1].to_numpy()
        ),
        mean_mixing_length=dummy_climate_data["mean_mixing_length"].to_numpy(),
        molar_density_air=dummy_climate_data["molar_density_air"][1].to_numpy(),
        upper_height=np.repeat(10.0, 3),
        lower_height=np.repeat(5.0, 3),
        relative_turbulence_intensity=(
            dummy_climate_data["relative_turbulence_intensity"][1].to_numpy()
        ),
        top_of_canopy_wind_speed=np.repeat(1.0, 3),
        diabatic_correction_momentum=(
            dummy_climate_data["diabatic_correction_momentum"][1].to_numpy()
        ),
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
    )
    exp_result = np.array([7.899376, 7.899376, 7.899376])
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_leaf_air_heat_conductivity(dummy_climate_data):
    """Test calculation of leaf air heat conductivity."""

    from virtual_rainforest.models.abiotic.conductivities import (
        calculate_leaf_air_heat_conductivity,
    )

    result = calculate_leaf_air_heat_conductivity(
        temperature=dummy_climate_data["air_temperature"].to_numpy(),
        wind_speed=dummy_climate_data["wind_speed"].to_numpy(),
        characteristic_dimension_leaf=0.1,
        temperature_difference=(
            dummy_climate_data["leaf_temperature"]
            - dummy_climate_data["air_temperature"]
        ).to_numpy(),
        molar_density_air=dummy_climate_data["molar_density_air"].to_numpy(),
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

    exp_result = np.concatenate(
        [
            [[np.nan, np.nan, np.nan]],
            [
                [0.065242, 0.065242, 0.065242],
                [0.065062, 0.065062, 0.065062],
                [0.064753, 0.064753, 0.064753],
            ],
            [[np.nan, np.nan, np.nan]] * 11,
        ]
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_leaf_vapour_conductivity():
    """Test calculate leaf vapour conductivity."""

    from virtual_rainforest.models.abiotic.conductivities import (
        calculate_leaf_vapour_conductivity,
    )

    result = calculate_leaf_vapour_conductivity(
        leaf_air_conductivity=np.repeat(5.0, 3),
        stomatal_conductance=np.repeat(5.0, 3),
    )
    np.testing.assert_allclose(result, np.repeat(2.5, 3), rtol=1e-04, atol=1e-04)


def test_calculate_current_conductivities(dummy_climate_data):
    """Test update current conductivities."""

    from virtual_rainforest.models.abiotic.conductivities import (
        calculate_current_conductivities,
    )

    result = calculate_current_conductivities(
        data=dummy_climate_data,
        characteristic_dimension_leaf=0.01,
        von_karmans_constant=CoreConsts.von_karmans_constant,
        abiotic_constants=AbioticConsts,
    )
    exp_gt = np.concatenate(
        [
            [
                [7.056348e02, 7.056348e02, 7.056348e02],
                [6.514515e04, 6.514515e04, 6.514515e04],
                [4.714156e02, 4.714156e02, 4.714156e02],
                [4.169318, 4.169318, 4.169318],
            ],
            [[np.nan, np.nan, np.nan]] * 8,
            [
                [589.115653, 589.115653, 589.115653],
                [455.163607, 455.163607, 455.163607],
                [np.nan, np.nan, np.nan],
            ],
        ]
    )

    exp_gv = np.concatenate(
        [
            [
                [np.nan, np.nan, np.nan],
                [0.186217, 0.186217, 0.186217],
                [0.185638, 0.185638, 0.185638],
                [0.184646, 0.184646, 0.184646],
            ],
            [[np.nan, np.nan, np.nan]] * 11,
        ]
    )
    exp_gha = np.concatenate(
        [
            [
                [np.nan, np.nan, np.nan],
                [0.188558, 0.188558, 0.188558],
                [0.187965, 0.187965, 0.187965],
                [0.186947, 0.186947, 0.186947],
            ],
            [[np.nan, np.nan, np.nan]] * 11,
        ]
    )

    exp_gtr = np.concatenate(
        [
            [
                [np.nan, np.nan, np.nan],
                [6.514515e04, 6.514515e04, 6.514515e04],
                [4.678095e02, 4.678095e02, 4.678095e02],
                [4.114899, 4.114899, 4.114899],
            ],
            [[np.nan, np.nan, np.nan]] * 8,
            [
                [59.602899, 59.602899, 59.602899],
                [20.156303, 20.156303, 20.156303],
                [np.nan, np.nan, np.nan],
            ],
        ]
    )

    np.testing.assert_allclose(
        result["air_heat_conductivity"], exp_gt, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_air_heat_conductivity"], exp_gha, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_vapour_conductivity"], exp_gv, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["conductivity_from_ref_height"], exp_gtr, rtol=1e-04, atol=1e-04
    )
