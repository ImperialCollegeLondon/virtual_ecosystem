"""Test module for abiotic.wind.py."""

import numpy as np
import pytest
from numpy.testing import assert_allclose


def test_calculate_zero_plane_displacement(dummy_climate_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_zero_plane_displacement,
    )

    data = dummy_climate_data

    result = calculate_zero_plane_displacement(
        canopy_height=data["layer_heights"][1].to_numpy(),
        leaf_area_index=data["leaf_area_index"][1].to_numpy(),
        zero_plane_scaling_parameter=7.5,
        denominator_tolerance=1e-10,
    )

    assert_allclose(result, data["zero_plane_displacement"].to_numpy())


def test_calculate_roughness_length_momentum(dummy_climate_data):
    """Test roughness length governing momentum transfer."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_roughness_length_momentum,
    )

    data = dummy_climate_data

    result = calculate_roughness_length_momentum(
        canopy_height=data["layer_heights"][1].to_numpy(),
        leaf_area_index=data["leaf_area_index"][1].to_numpy(),
        zero_plane_displacement=data["zero_plane_displacement"].to_numpy(),
        substrate_surface_roughness_length=0.003,
        roughness_element_drag_coefficient=0.3,
        roughness_sublayer_depth_parameter=0.193,
        max_ratio_wind_to_friction_velocity=0.3,
        von_karman_constant=0.4,
        min_roughness_length=0.01,
        denominator_tolerance=1e-10,
    )

    assert_allclose(
        result, data["roughness_length_momentum"].to_numpy(), rtol=1e-3, atol=1e-3
    )


def test_calculate_wind_profile(dummy_climate_data, fixture_core_components):
    """Test calculate wind profile."""

    from virtual_ecosystem.models.abiotic.wind import calculate_wind_profile

    lyr_str = fixture_core_components.layer_structure
    data = dummy_climate_data

    result = calculate_wind_profile(
        reference_wind_speed=np.abs(
            data["wind_speed_ref"].isel(time_index=0)
        ).to_numpy(),
        reference_height=data["layer_heights"][0].to_numpy() + 10.0,
        wind_heights=data["layer_heights"][lyr_str.index_filled_atmosphere].to_numpy(),
        roughness_length=data["roughness_length_momentum"].to_numpy(),
        zero_plane_displacement=data["zero_plane_displacement"].to_numpy(),
        min_wind_speed=0.001,
        denominator_tolerance=1e-10,
    )

    exp_wind = np.array(
        [
            [0.34011, 0.53909, 0.78857, 1.4318],
            [0.28038, 0.43823, 0.61038, np.nan],
            [0.001, 0.001, np.nan, np.nan],
            [0.001, np.nan, np.nan, np.nan],
            [0.001, 0.001, 0.001, 0.5780],
        ]
    )

    assert_allclose(result, exp_wind, rtol=1e-3, atol=1e-3)


def test_calculate_friction_velocity(dummy_climate_data):
    """Test calculating friction velocity."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_friction_velocity,
    )

    data = dummy_climate_data

    result = calculate_friction_velocity(
        reference_wind_speed=np.abs(
            data["wind_speed_ref"].isel(time_index=0)
        ).to_numpy(),
        reference_height=data["layer_heights"][0].to_numpy() + 10.0,
        roughness_length=data["roughness_length_momentum"].to_numpy(),
        zero_plane_displacement=data["zero_plane_displacement"].to_numpy(),
        von_karman_constant=0.4,
        denominator_tolerance=1e-10,
    )
    exp_friction_velocity = np.array([0.07348, 0.114846, 0.159962, 0.100417])
    assert_allclose(result, exp_friction_velocity, rtol=1e-3, atol=1e-3)


def test_calculate_ventilation_rate():
    """Test calculate ventilation rate."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_ventilation_rate,
    )

    aerodynamic_resistance = np.array([10.0, 50.0, 0.0, 10.0])
    characteristic_height = np.array([2.0, 20.0, 1.0, 0.0])
    expected = np.array([5.0e-02, 1.0e-03, 1.0e10, 1.0e-01])

    result = calculate_ventilation_rate(
        aerodynamic_resistance=aerodynamic_resistance,
        characteristic_height=characteristic_height,
        understorey_ventilation_rate=0.1,
        surface_layer_height=0.1,
        denominator_tolerance=1e-10,
    )
    assert_allclose(result, expected)


def test_calculate_ventilation_rate_zero_denominator():
    """Test calculate ventilation rate scalar."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_ventilation_rate,
    )

    aerodynamic_resistance = 0.0
    characteristic_height = 10.0
    expected = 1.0e10

    result = calculate_ventilation_rate(
        aerodynamic_resistance=aerodynamic_resistance,
        characteristic_height=characteristic_height,
        understorey_ventilation_rate=0.1,
        surface_layer_height=0.1,
        denominator_tolerance=1e-10,
    )
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
        max_mixing_coefficient=1.0,
        denominator_tolerance=1e-10,
    )

    assert result.shape == layer_midpoints.shape
    assert np.all(result >= 0)
    assert_allclose(result, expected, rtol=1e-6)

    # Test zero canopy height edge case
    zero_canopy_height = np.zeros(3)
    layer_midpoints_zero = np.array([[np.nan, np.nan, np.nan], [0.1, 0.1, 0.1]])
    expected_zero_canopy = k * friction_velocity * layer_midpoints_zero

    zero_result = calculate_mixing_coefficients_canopy(
        layer_midpoints=layer_midpoints_zero,
        canopy_height=zero_canopy_height,
        friction_velocity=friction_velocity,
        von_karman_constant=k,
        max_mixing_coefficient=1.0,
        denominator_tolerance=1e-10,
    )

    assert_allclose(zero_result, expected_zero_canopy)


class TestClampVariableWithinLimits:
    """Tests for clamp_variable_within_limits."""

    @pytest.mark.parametrize(
        "variable, limits, expected",
        [
            # No clamping needed — values within limits unchanged
            (
                np.array([[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]], dtype=float),
                (0.0, 1.0),
                np.array([[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]], dtype=float),
            ),
            # Upper clamp — residual propagates up one layer
            (
                np.array([[0.0, 0.0], [0.0, 0.0], [1.5, 1.5]], dtype=float),
                (0.0, 1.0),
                np.array([[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]], dtype=float),
            ),
            # Lower clamp — negative residual propagates up
            (
                np.array([[0.5, 0.5], [0.0, 0.0], [-0.5, -0.5]], dtype=float),
                (0.0, 1.0),
                np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], dtype=float),
            ),
            # Residual propagates across multiple layers
            (
                np.array([[0.0, 0.0], [0.9, 0.9], [1.5, 1.5]], dtype=float),
                (0.0, 1.0),
                np.array([[0.4, 0.4], [1.0, 1.0], [1.0, 1.0]], dtype=float),
            ),
            # Cell-varying NDArray limits — each cell clamped independently
            (
                np.array([[0.0, 0.0], [0.0, 0.0], [1.5, 1.5]], dtype=float),
                (np.array([0.0, 0.0]), np.array([1.0, 2.0])),
                np.array([[0.0, 0.0], [0.5, 0.0], [1.0, 1.5]], dtype=float),
            ),
        ],
    )
    def test_clamping(self, variable, limits, expected):
        """Clamping behaviour: no clamp, upper, lower, multi-layer, and array limits."""

        from virtual_ecosystem.models.abiotic.wind import clamp_variable_within_limits

        result = clamp_variable_within_limits(variable.copy(), limits)
        np.testing.assert_allclose(result, expected)

    def test_nan_skipped_and_residual_carried(self):
        """NaN cells are skipped and residuals carried to next valid layer above."""

        from virtual_ecosystem.models.abiotic.wind import clamp_variable_within_limits

        variable = np.array(
            [[0.0], [np.nan], [1.5]],
            dtype=float,
        )
        result = clamp_variable_within_limits(variable, limits=(0.0, 1.0))

        np.testing.assert_allclose(result[2], [1.0])  # clamped
        assert np.isnan(result[1])  # NaN preserved
        np.testing.assert_allclose(result[0], [0.5])  # residual absorbed

    def test_column_total_conserved(self):
        """Column totals are conserved when all residuals can be absorbed."""

        from virtual_ecosystem.models.abiotic.wind import clamp_variable_within_limits

        variable = np.array([[0.0, 0.0], [0.0, 0.0], [1.5, 0.8]], dtype=float)
        original_total = variable.sum(axis=0).copy()
        result = clamp_variable_within_limits(variable, limits=(0.0, 1.0))
        np.testing.assert_allclose(result.sum(axis=0), original_total)

    def test_top_layer_can_exceed_limits(self):
        """Top layer is allowed to exceed limits if residuals cannot be absorbed."""

        from virtual_ecosystem.models.abiotic.wind import clamp_variable_within_limits

        variable = np.array([[0.9], [1.5]], dtype=float)
        result = clamp_variable_within_limits(variable, limits=(0.0, 1.0))
        assert result[0] > 1.0


def test_next_valid_above(dummy_climate_data):
    """Test next valid above."""
    from virtual_ecosystem.models.abiotic.wind import next_valid_above

    data = dummy_climate_data
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


def test_next_valid_below(dummy_climate_data):
    """Test next valid below."""
    from virtual_ecosystem.models.abiotic.wind import next_valid_below

    data = dummy_climate_data
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


def test_mix_and_ventilate(dummy_climate_data, fixture_core_components):
    """Test mixing and ventilation within bounds."""

    from virtual_ecosystem.models.abiotic.wind import (
        mix_and_ventilate,
    )

    data = dummy_climate_data
    lyrstr = fixture_core_components.layer_structure

    mixing_coefficient = data["mixing_coefficient"].to_numpy()
    ventilation_rate = data["ventilation_rate"].to_numpy()

    input_temp = data["air_temperature"].to_numpy()
    input_humidity = data["relative_humidity"].to_numpy()
    input_humidity[2, :] = np.array([105, 102, np.nan, np.nan])

    exp_temp = np.full_like(input_humidity, np.nan)
    exp_temp[lyrstr.index_filled_atmosphere] = np.array(
        [
            [21.964, 22.868, 23.748, 24.92],
            [21.74, 22.424, 23.197, np.nan],
            [20.626, 21.22, np.nan, np.nan],
            [19.249, np.nan, np.nan, np.nan],
            [18.521, 19.088, 20.155, 23.08],
        ]
    )
    exp_hum = np.full_like(input_humidity, np.nan)
    exp_hum[lyrstr.index_filled_atmosphere] = np.array(
        [
            [90.36, 82.66, 73.12, 67.56],
            [96.19, 86.1, 75.78, np.nan],
            [100.0, 100.0, np.nan, np.nan],
            [96.54, np.nan, np.nan, np.nan],
            [98.91, 96.24, 93.1, 80.44],
        ]
    )

    result_hum = mix_and_ventilate(
        input_variable=input_humidity,
        mixing_coefficient=mixing_coefficient,
        ventilation_rate=ventilation_rate,
        limits=(0, np.repeat(100, 4)),
        surface_index=lyrstr.index_surface_scalar,
    )
    assert_allclose(result_hum, exp_hum, rtol=1e-6, atol=1e-6)

    result_temp = mix_and_ventilate(
        input_variable=input_temp,
        mixing_coefficient=mixing_coefficient,
        ventilation_rate=ventilation_rate,
        limits=(-20, np.repeat(80, 4)),
        surface_index=lyrstr.index_surface_scalar,
    )
    assert_allclose(result_temp, exp_temp, rtol=1e-6, atol=1e-6)


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


def test_calculate_aerodynamic_resistance(dummy_climate_data, fixture_core_components):
    """Test calculate aerodynamic resistance."""

    from virtual_ecosystem.models.abiotic.wind import (
        calculate_aerodynamic_resistance,
    )

    lyr_str = fixture_core_components.layer_structure
    data = dummy_climate_data

    exp_ra = np.array(
        [
            [58.24231, 32.3568, 18.2007, np.nan],
            [100.0, 100.0, np.nan, np.nan],
            [100.0, np.nan, np.nan, np.nan],
        ]
    )

    result = calculate_aerodynamic_resistance(
        wind_heights=data["layer_heights"][lyr_str.index_filled_canopy],
        roughness_length=data["roughness_length_momentum"].to_numpy(),
        zero_plane_displacement=data["zero_plane_displacement"].to_numpy(),
        wind_speed=data["wind_speed"][lyr_str.index_filled_canopy].to_numpy(),
        von_karman_constant=0.4,
        fallback_resistance=100.0,
        denominator_tolerance=1e-10,
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
