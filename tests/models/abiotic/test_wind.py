"""Test module for abiotic.wind.py."""

import numpy as np
from numpy.testing import assert_allclose


def test_calculate_zero_plane_displacement(dummy_climate_data_varying_canopy):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_zero_plane_displacement,
    )

    result = calculate_zero_plane_displacement(
        canopy_height=dummy_climate_data_varying_canopy["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([0.0, np.nan, 7.0, 0.0]),
        zero_plane_scaling_parameter=7.5,
    )

    assert_allclose(result, np.array([0.0, 0.0, 25.86256, 0.0]))


def test_calculate_roughness_length_momentum(dummy_climate_data_varying_canopy):
    """Test roughness length governing momentum transfer."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_roughness_length_momentum,
    )

    result = calculate_roughness_length_momentum(
        canopy_height=dummy_climate_data_varying_canopy["layer_heights"][1].to_numpy(),
        leaf_area_index=np.array([np.nan, 0.0, 7, 0.0]),
        zero_plane_displacement=np.array([0.0, 0.0, 27.58673, 0.0]),
        substrate_surface_roughness_length=0.003,
        roughness_element_drag_coefficient=0.3,
        roughness_sublayer_depth_parameter=0.193,
        max_ratio_wind_to_friction_velocity=0.3,
        von_karman_constant=0.4,
        min_roughness_length=0.01,
    )

    assert_allclose(
        result, np.array([0.01, 0.01666, 0.524479, 0.01]), rtol=1e-3, atol=1e-3
    )


def test_calculate_wind_profile(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test calculate wind profile."""

    from virtual_ecosystem.models.abiotic.wind import calculate_wind_profile

    lyr_str = fixture_core_components.layer_structure
    data = dummy_climate_data_varying_canopy

    result = calculate_wind_profile(
        reference_wind_speed=data["wind_speed_ref"].isel(time_index=0).to_numpy(),
        reference_height=data["layer_heights"][0].to_numpy() + 10.0,
        wind_heights=data["layer_heights"][lyr_str.index_filled_atmosphere].to_numpy(),
        roughness_length=np.array([0.01, 0.01666, 0.524479, 0.01]),
        zero_plane_displacement=np.array([0, 0, 25, 0]),
        min_wind_speed=0.001,
    )

    exp_wind = np.array(
        [
            [0.967405, 0.965281, 0.744923, 0.967405],
            [0.959669, 0.957041, 0.648195, 0.001],
            [0.911069, 0.905273, 0.001, 0.001],
            [0.827986, 0.001, 0.001, 0.001],
            [0.275995, 0.228813, 0.001, 0.275995],
        ]
    )

    assert_allclose(result, exp_wind, rtol=1e-3, atol=1e-3)


def test_calculate_friction_velocity(dummy_climate_data_varying_canopy):
    """Test calculating friction velocity."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_friction_velocity,
    )

    data = dummy_climate_data_varying_canopy

    result = calculate_friction_velocity(
        reference_wind_speed=data["wind_speed_ref"].isel(time_index=0).to_numpy(),
        reference_height=data["layer_heights"][0].to_numpy() + 10.0,
        roughness_length=np.array([0.01, 0.01666, 0.524479, 0.01]),
        zero_plane_displacement=np.array([0, 0, 25, 0]),
        von_karman_constant=0.4,
    )
    exp_friction_velocity = np.array([0.047945, 0.05107, 0.11499, 0.047945])
    assert_allclose(result, exp_friction_velocity, rtol=1e-3, atol=1e-3)


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
    assert_allclose(result, expected)


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
        layer_midpoints=layer_midpoints,
        canopy_height=canopy_height,
        friction_velocity=friction_velocity,
        von_karman_constant=k,
        max_mixing_coefficient=1000.0,
    )

    assert result.shape == layer_midpoints.shape
    assert np.all(result >= 0)
    assert_allclose(result, expected, rtol=1e-6)


def test_clamp_variable_within_limits():
    """Test clamping of variable within limits."""

    from virtual_ecosystem.models.abiotic.wind import clamp_variable_within_limits

    # Set limits
    limits = (4, 6)

    # Cells with mix of issues: undershoot and overshoot, can be absorbed by a single
    # cell vs need to spread further up into canopy, empty layers and complete, and mix
    # of under and overshoot. Two cases explicitly test the edge case where undershoot
    # and overshoot cannot be absorbed within the canopy, leading to out of limit values
    # in the top layer.

    n = np.nan
    variable = np.array(
        [
            [5, 5, 5, 5, 5, 4, 5, 5, 5, 5, 5, 5],
            [5, 5, 5, 5, 5, 4, 5, 5, 5, 5, 5, 8],
            [5, 5, 5, 5, 3, 4, 5, 5, 5, 7, 5, 2],
            [5, n, 5, n, n, 4, 4, 5, n, n, 7, 7],
            [5, 5, 3, 3, 5, 0, 2, 7, 7, 7, 9, 3],
        ]
    )

    variable_expected = np.array(
        [
            [5, 5, 5, 5, 5, 0, 5, 5, 5, 6, 7, 5],
            [5, 5, 5, 5, 4, 4, 4, 5, 5, 6, 6, 6],
            [5, 5, 5, 4, 4, 4, 4, 5, 6, 6, 6, 4],
            [5, n, 4, n, n, 4, 4, 6, n, n, 6, 6],
            [5, 5, 4, 4, 5, 4, 4, 6, 6, 6, 6, 4],
        ]
    )

    clamped_variable = clamp_variable_within_limits(variable=variable, limits=limits)

    assert_allclose(clamped_variable, variable_expected)

    # sanity checks: the column sums should be maintained.
    assert_allclose(variable.sum(axis=0), clamped_variable.sum(axis=0))


def test_next_valid_above(dummy_climate_data_varying_canopy):
    """Test next valid above."""
    from virtual_ecosystem.models.abiotic.wind import next_valid_above

    data = dummy_climate_data_varying_canopy
    arr = data["air_temperature"].to_numpy()

    result = next_valid_above(arr)

    expected = np.array(
        [
            [-1, -1, -1, -1],
            [0, 0, 0, 0],
            [1, 1, 1, 0],
            [2, 2, 1, 0],
            [3, 2, 1, 0],
            [3, 2, 1, 0],
            [3, 2, 1, 0],
            [3, 2, 1, 0],
            [3, 2, 1, 0],
            [3, 2, 1, 0],
            [3, 2, 1, 0],
            [3, 2, 1, 0],
            [11, 11, 11, 11],
            [11, 11, 11, 11],
        ]
    )

    assert np.array_equal(result, expected)


def test_next_valid_below(dummy_climate_data_varying_canopy):
    """Test next valid below."""
    from virtual_ecosystem.models.abiotic.wind import next_valid_below

    data = dummy_climate_data_varying_canopy
    arr = data["air_temperature"].to_numpy()

    result = next_valid_below(arr)

    expected = np.array(
        [
            [1, 1, 1, 11],
            [2, 2, 11, 11],
            [3, 11, 11, 11],
            [11, 11, 11, 11],
            [11, 11, 11, 11],
            [11, 11, 11, 11],
            [11, 11, 11, 11],
            [11, 11, 11, 11],
            [11, 11, 11, 11],
            [11, 11, 11, 11],
            [11, 11, 11, 11],
            [-1, -1, -1, -1],
            [-1, -1, -1, -1],
            [-1, -1, -1, -1],
        ]
    )

    assert np.array_equal(result, expected)


def test_mix_and_ventilate():
    """Test mixing and ventilation within bounds."""

    from virtual_ecosystem.models.abiotic.wind import (
        mix_and_ventilate,
    )

    mixing_coefficient = np.array(
        [
            [0.001, 0.001, 0.001, 0.001],
            [0.005, 0.005, 0.005, np.nan],
            [0.01, 0.01, np.nan, np.nan],
            [0.001, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
            [0.012, 0.012, 0.012, 0.012],
            [np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
        ]
    )
    ventilation_rate = np.array([0.001, 0.001, 0.001, 0.001])

    input_humidity = np.array(
        [
            [95.0, 95.0, 95.0, 95.0],
            [110.0, 100.0, 100.0, np.nan],
            [100.0, 100.0, np.nan, np.nan],
            [90.0, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
            [100.0, 100.0, 100.0, 100.0],
            [np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
        ],
    )

    exp_result = np.array(
        [
            [104.89, 95.005, 95.005, 95.005],
            [100.0, 99.975, 99.975, np.nan],
            [100.0, 100.0, np.nan, np.nan],
            [90.02, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
            [99.88, 100.0, 100.0, 99.995],
            [np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
        ]
    )

    result = mix_and_ventilate(
        input_variable=input_humidity,
        mixing_coefficient=mixing_coefficient,
        ventilation_rate=ventilation_rate,
        limits=(0, 100),
    )
    assert_allclose(result, exp_result, rtol=1e-6, atol=1e-6)


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

    assert_allclose(result, expected_specific_humidity)


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
            [132.547453, 66.273726, 98.940998, np.nan],
            [110.234517, 55.117259, np.nan, np.nan],
            [76.849677, np.nan, np.nan, np.nan],
        ]
    )

    result = calculate_aerodynamic_resistance(
        wind_heights=data["layer_heights"][lyr_str.index_filled_canopy],
        roughness_length=np.repeat(0.3, 4),
        zero_plane_displacement=np.array([0.0, 0.0, 25.0, 0.0]),
        wind_speed=np.array([1.0, 2.0, 0.5, 0.01]),
        von_karman_constant=0.4,
    )
    assert_allclose(result, exp_ra, rtol=1e-3, atol=1e-3)


def calculate_aerodynamic_resistance_understorey():
    """Test calculate aerodynamic resistance below canopy."""

    from virtual_ecosystem.models.abiotic.wind import (
        compute_aerodynamic_resistance_understorey,
    )

    min_ws = 0.1
    coef = 33.0

    # Case 1: normal wind speeds
    ws = np.array([1.0, 2.0])
    result = compute_aerodynamic_resistance_understorey(ws, min_ws, coef)
    expected = coef / ws
    assert np.allclose(result, expected)

    # Case 2: wind speed below minimum → clipped
    ws = np.array([0.01, 0.05])
    result = compute_aerodynamic_resistance_understorey(ws, min_ws, coef)
    expected = coef / min_ws
    assert np.all(result == expected)

    # Case 3: zero wind speed → clipped
    ws = np.array([0.0])
    result = compute_aerodynamic_resistance_understorey(ws, min_ws, coef)
    expected = np.array([coef / min_ws])
    assert np.allclose(result, expected)
