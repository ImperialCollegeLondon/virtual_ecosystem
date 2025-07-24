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


def test_calculate_ventilation_rate_scalar():
    """Test calculate ventilation rate scalar."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_ventilation_rate,
    )

    ra = 50.0
    h = 20.0
    expected = 1.0 / 1000.0

    result = calculate_ventilation_rate(ra, h)
    assert np.isclose(result, expected)


def test_calculate_ventilation_rate_array():
    """Test calculate ventilation rate array."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_ventilation_rate,
    )

    ra = np.array([10.0, 50.0, 0.0])
    h = np.array([2.0, 20.0, 1.0])
    expected = np.array([5.0e-02, 1.0e-03, 1.0e03])

    result = calculate_ventilation_rate(ra, h)
    np.testing.assert_allclose(result, expected)


def test_calculate_ventilation_rate_zero_denominator():
    """Test calculate ventilation rate scalar."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_ventilation_rate,
    )

    ra = 0.0
    h = 0.0
    expected = 1.0 / 1e-3

    result = calculate_ventilation_rate(ra, h)
    assert np.isclose(result, expected)


def test_calculate_mixing_coefficients():
    """Test mixing coefficients."""
    from virtual_ecosystem.models.abiotic.wind import (
        calculate_mixing_coefficients_canopy,
    )

    layer_midpoints = np.array([[0.1, 0.5, 0.9], [0.2, 0.6, 0.8]])
    canopy_height = np.repeat(1.0, 3)
    friction_velocity = np.repeat(0.3, 3)
    k = 0.4
    expected = np.array([[0.00972, 0.015, 0.00108], [0.01536, 0.01152, 0.00384]])

    result = calculate_mixing_coefficients_canopy(
        layer_midpoints, canopy_height, friction_velocity, k
    )

    assert result.shape == layer_midpoints.shape
    assert np.all(result >= 0)
    np.testing.assert_allclose(result, expected, rtol=1e-6)


def test_mix_and_ventilate(dummy_climate_data, fixture_core_components):
    """Test mixing and ventilation."""

    from virtual_ecosystem.models.abiotic.wind import (
        mix_and_ventilate,
    )

    lystr = fixture_core_components.layer_structure
    data = dummy_climate_data
    input_variable = data["relative_humidity"][lystr.index_filled_atmosphere].to_numpy()

    layer_thickness = np.array(
        [
            [2.0, 2.0, 2.0, 2.0],
            [10.0, 10.0, 10.0, 10.0],
            [5.0, 5.0, 5.0, 5.0],
            [2.0, 2.0, 2.0, 2.0],
            [0.25, 0.25, 0.25, 0.25],
        ]
    )
    exp_result = np.array(
        [
            [77.700816, 65.401632, 53.102448, 40.803264],
            [90.341644, 90.341644, 90.341644, 90.341644],
            [92.70733, 92.70733, 92.70733, 92.70733],
            [96.313381, 96.313381, 96.313381, 96.313381],
            [100.0, 100.0, 100.0, 100.0],
        ]
    )

    result = mix_and_ventilate(
        input_variable=input_variable,
        layer_thickness=layer_thickness,
        mixing_coefficient=np.full((5, 4), 0.001),
        ventilation_rate=np.array([0.01, 0.02, 0.03, 0.04]),
        time_interval=3600.0,
    )
    np.testing.assert_allclose(result, exp_result)


def test_advect_from_toplayer():
    """Test advection of moisture from top layer."""

    from virtual_ecosystem.models.abiotic.wind import (
        advect_water_from_toplayer,
    )

    specific_humidity = np.array([0.010, 0.008, 0.006])
    layer_thickness = np.array([10.0, 10.0, 10.0])
    density_air = np.array([1.2, 1.1, 1.0])
    wind_speed = np.array([1.0, 0.5, 2.0])
    time_interval = 3600.0

    expected_specific_humidity = np.array([0, 0, 0])

    result = advect_water_from_toplayer(
        specific_humidity=specific_humidity,
        layer_thickness=layer_thickness,
        density_air=density_air,
        wind_speed=wind_speed,
        characteristic_length=100,
        time_interval=time_interval,
    )

    np.testing.assert_allclose(result, expected_specific_humidity)


def test_calculate_aerodynamic_resistance(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculate aerodynamic resistance."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_aerodynamic_resistance,
    )

    lyr_str = fixture_core_components.layer_structure
    data = dummy_climate_data_varying_canopy

    exp_ra = np.array(
        [
            [132.547453, 55.117259, 191.29905, 4947.049913],
            [110.234517, 38.424838, np.nan, np.nan],
            [76.849677, np.nan, np.nan, np.nan],
        ]
    )

    result = calculate_aerodynamic_resistance(
        wind_heights=data["layer_heights"][lyr_str.index_filled_canopy],
        roughness_length=np.repeat(0.3, 4),
        zero_plane_displacement=np.array([0.0, 10.0, 15.0, 25.0]),
        wind_speed=np.array([1.0, 2.0, 0.5, 0.01]),
        von_karman_constant=0.4,
    )
    np.testing.assert_allclose(result, exp_ra, rtol=1e-3, atol=1e-3)
