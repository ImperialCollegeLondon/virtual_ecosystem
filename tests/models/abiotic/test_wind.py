"""Test module for abiotic.wind.py."""

import numpy as np


def test_calculate_zero_plane_displacement(dummy_climate_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_zero_plane_displacement,
    )

    result = calculate_zero_plane_displacement(
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([0.0, np.nan, 7.0, 7.0]),
        zero_plane_scaling_parameter=7.5,
    )

    np.testing.assert_allclose(result, np.array([0.0, 0.0, 25.86256, 25.86256]))


def test_calculate_roughness_length_momentum(dummy_climate_data):
    """Test roughness length governing momentum transfer."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_roughness_length_momentum,
    )

    result = calculate_roughness_length_momentum(
        canopy_height=dummy_climate_data["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([np.nan, 0.0, 7, 7]),
        zero_plane_displacement=np.array([0.0, 0.0, 27.58673, 27.58673]),
        substrate_surface_drag_coefficient=0.003,
        roughness_element_drag_coefficient=0.3,
        roughness_sublayer_depth_parameter=0.193,
        max_ratio_wind_to_friction_velocity=0.3,
        von_karman_constant=0.4,
        min_roughness_length=0.01,
    )

    np.testing.assert_allclose(
        result, np.array([0.01, 0.01666, 0.524479, 0.524479]), rtol=1e-3, atol=1e-3
    )


def test_calculate_wind_profile(dummy_climate_data, fixture_core_components):
    """Test calculate wind profile."""

    from virtual_ecosystem.models.abiotic.wind import calculate_wind_profile

    lyr_str = fixture_core_components.layer_structure

    result = calculate_wind_profile(
        reference_wind_speed=dummy_climate_data["wind_speed_ref"]
        .isel(time_index=0)
        .to_numpy(),
        reference_height=dummy_climate_data["layer_heights"][0].to_numpy() + 10.0,
        wind_heights=dummy_climate_data["layer_heights"][
            lyr_str.index_filled_atmosphere
        ].to_numpy(),
        roughness_length=np.repeat(0.3, 4),
        zero_plane_displacement=np.array([0, 10, 25, 25]),
        min_wind_speed=0.001,
    )

    exp_wind = np.array(
        [
            [0.944971, 0.919761, 0.780217, 0.780217],
            [0.931911, 0.899351, 0.696874, 0.696874],
            [0.84986, 0.750916, 0.001, 0.001],
            [0.709594, 0.001, 0.001, 0.001],
            [0.001, 0.001, 0.001, 0.001],
        ]
    )

    np.testing.assert_allclose(result, exp_wind, rtol=1e-3, atol=1e-3)


def test_calculate_friction_velocity(dummy_climate_data):
    """Test calculating friction velocity."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_friction_velocity,
    )

    result = calculate_friction_velocity(
        reference_wind_speed=dummy_climate_data["wind_speed_ref"]
        .isel(time_index=0)
        .to_numpy(),
        reference_height=dummy_climate_data["layer_heights"][0].to_numpy() + 10.0,
        roughness_length=np.repeat(0.3, 4),
        zero_plane_displacement=np.array([0, 10, 25, 25]),
        von_karman_constant=0.4,
    )
    exp_friction_velocity = np.array([0.080945, 0.085658, 0.099079, 0.099079])
    np.testing.assert_allclose(result, exp_friction_velocity, rtol=1e-3, atol=1e-3)
