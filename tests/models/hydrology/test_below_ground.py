"""Test module for hydrology.below_ground.py."""

import numpy as np
import pytest


@pytest.mark.parametrize("n_layers", [2, 4])
def test_calculate_vertical_flow_uniform_profile(n_layers):
    """Uniform moisture gives gravity-driven flow at every interface."""

    from virtual_ecosystem.models.hydrology.below_ground import (
        calculate_vertical_flow,
    )

    moisture = np.full((n_layers, 2), 0.3)
    thickness = np.ones((n_layers, 2))
    depth = np.arange(n_layers, dtype=float) + 0.5

    theta_s = 0.5
    theta_r = 0.1
    ks = 1e-8  # m/s
    n_parameter = 2.0
    pore_connectivity = 0.5
    seconds_per_day = 86400.0

    result = calculate_vertical_flow(
        soil_moisture=moisture,
        soil_layer_thickness=thickness,
        soil_layer_depth=depth,
        soil_moisture_saturation=theta_s,
        soil_moisture_residual=theta_r,
        saturated_hydraulic_conductivity=ks,
        air_entry_potential_inverse=1.0,
        van_genuchten_nonlinearity_parameter=n_parameter,
        pore_connectivity_parameter=pore_connectivity,
        seconds_to_day=seconds_per_day,
        denominator_tolerance=1e-6,
    )

    # Se = 0.5 in every layer, so K(theta) is the same throughout.
    se = (0.3 - theta_r) / (theta_s - theta_r)
    m_parameter = 1.0 - 1.0 / n_parameter
    expected_k = (
        ks
        * se**pore_connectivity
        * (1.0 - (1.0 - se ** (1.0 / m_parameter)) ** m_parameter) ** 2
    )
    expected_flow = expected_k * seconds_per_day * 1000.0  # mm/day

    assert result["vertical_flow"].shape == moisture.shape
    np.testing.assert_allclose(
        result["vertical_flow"],
        expected_flow,
        rtol=1e-10,
    )
    assert np.all(np.isfinite(result["matric_potential"]))
    assert np.all(np.isfinite(result["effective_saturation"]))


def test_calculate_vertical_flow_is_nonnegative_and_capped():
    """Downward-only flow respects donor water and receiver pore space."""
    from virtual_ecosystem.models.hydrology.below_ground import (
        calculate_vertical_flow,
    )

    moisture = np.full((3, 2), 0.3)
    thickness = np.full((3, 2), 1e-6)
    residual = 0.1
    saturation = 0.5

    result = calculate_vertical_flow(
        soil_moisture=moisture,
        soil_layer_thickness=thickness,
        soil_layer_depth=np.array([0.5, 1.5, 2.5]),
        soil_moisture_saturation=saturation,
        soil_moisture_residual=residual,
        saturated_hydraulic_conductivity=1e-8,
        air_entry_potential_inverse=1.0,
        van_genuchten_nonlinearity_parameter=2.0,
        pore_connectivity_parameter=0.5,
        seconds_to_day=86400.0,
        denominator_tolerance=1e-6,
    )

    flow = result["vertical_flow"]
    available_water_mm = (moisture - residual) * thickness * 1000.0
    receiver_space_mm = (saturation - moisture) * thickness * 1000.0

    assert np.all(np.isfinite(flow))
    assert np.all(flow >= 0.0)
    assert np.all(flow[:-1] <= available_water_mm[:-1])
    assert np.all(flow[:-1] <= receiver_space_mm[1:])
    assert np.all(flow[-1] <= available_water_mm[-1])


def test_update_soil_moisture(fixture_hydrology_constants):
    """Test soil moisture update."""

    from virtual_ecosystem.models.hydrology.below_ground import update_soil_moisture

    layer_thickness = np.array([[100, 100, 100], [900, 900, 900], [900, 900, 900]])
    exp_result = np.array(
        [[20.0, 51.0, 47.0], [289.0, 459.0, 459.0], [300.0, 459.0, 459.0]]
    )

    result = update_soil_moisture(
        soil_moisture=np.array([[30, 60, 50], [300, 600, 500], [300, 600, 500]]),
        vertical_flow=np.array([[10, 2, 3], [10, 2, 3], [15, 25, 35]]),
        transpiration=np.array([10, 2, 3]),
        subsurface_stormflow=np.array([1, 1, 1]),
        soil_moisture_saturation=fixture_hydrology_constants.soil_moisture_saturation
        * layer_thickness,
        soil_moisture_residual=fixture_hydrology_constants.soil_moisture_residual
        * layer_thickness,
    )

    np.testing.assert_allclose(result, exp_result, rtol=0.001)


def test_calculate_matric_potential(fixture_hydrology_constants):
    """Test that function to convert soil moisture to a water potential works."""
    from virtual_ecosystem.models.hydrology.below_ground import (
        calculate_matric_potential,
    )

    constants = fixture_hydrology_constants
    expected_potentials = np.repeat(-68.197326, 3)
    actual_potentials = calculate_matric_potential(
        effective_saturation=np.repeat(0.5, 3),
        air_entry_potential_inverse=constants.air_entry_potential_inverse,
        van_genuchten_nonlinearity_parameter=(
            constants.van_genuchten_nonlinearity_parameter
        ),
        denominator_tolerance=0.001,
    )

    np.testing.assert_allclose(actual_potentials, expected_potentials, rtol=0.001)


def test_update_groundwater_storage(dummy_climate_data, fixture_hydrology_constants):
    """Test the update_groundwater_storage() function."""

    from virtual_ecosystem.models.hydrology.below_ground import (
        update_groundwater_storage,
    )

    data = dummy_climate_data
    result = update_groundwater_storage(
        groundwater_storage=np.array(data["groundwater_storage"]),
        vertical_flow_to_groundwater=np.array([2, 4, 5, 5]),
        bypass_flow=np.array([2, 4, 5, 5]),
        max_percolation_rate_uzlz=fixture_hydrology_constants.max_percolation_rate_uzlz,
        groundwater_loss=fixture_hydrology_constants.groundwater_loss,
        reservoir_const_upper_groundwater=fixture_hydrology_constants.reservoir_const_upper_groundwater,
        reservoir_const_lower_groundwater=fixture_hydrology_constants.reservoir_const_lower_groundwater,
    )

    exp_groundwat = np.array(
        [[451.3, 385.3, 307.3, 227.3], [501.7, 471.7, 391.7, 301.7]]
    )
    exp_upper_flow = np.array([22.565, 19.265, 15.365, 11.365])
    exp_lower_flow = np.array([25.085, 23.585, 19.585, 15.085])
    np.testing.assert_allclose(result["groundwater_storage"], exp_groundwat, rtol=1e-05)
    np.testing.assert_allclose(result["subsurface_flow"], exp_upper_flow, rtol=1e-05)
    np.testing.assert_allclose(result["baseflow"], exp_lower_flow, rtol=1e-5)


def test_upper_flow_clamped_to_zero(fixture_hydrology_constants):
    """Ensure negative groundwater outflow is clamped to zero."""

    from virtual_ecosystem.models.hydrology.below_ground import (
        update_groundwater_storage,
    )

    # Force a negative scenario
    groundwater_storage = np.array(
        [
            [-10, -5, -1, -0.1],  # upper zone goes negative
            [100, 100, 100, 100],  # lower zone normal
        ]
    )

    result = update_groundwater_storage(
        groundwater_storage=groundwater_storage,
        vertical_flow_to_groundwater=np.zeros(4),
        bypass_flow=np.zeros(4),
        max_percolation_rate_uzlz=fixture_hydrology_constants.max_percolation_rate_uzlz,
        groundwater_loss=fixture_hydrology_constants.groundwater_loss,
        reservoir_const_upper_groundwater=fixture_hydrology_constants.reservoir_const_upper_groundwater,
        reservoir_const_lower_groundwater=fixture_hydrology_constants.reservoir_const_lower_groundwater,
    )

    # This is the key assertion:
    assert np.all(result["subsurface_flow"] >= 0)
    assert np.all(result["baseflow"] >= 0)
    assert np.all(result["groundwater_storage"][0] >= 0)


@pytest.mark.parametrize(
    "effective_saturation,root_soil_moisture,transpiration,coeff,exponent,expected",
    [
        (
            np.array([0.5]),
            np.array([100.0]),
            np.array([20.0]),
            0.1,
            2.0,
            np.array([2.0]),
        ),
        (
            np.array([0.0]),
            np.array([100.0]),
            np.array([20.0]),
            0.1,
            2.0,
            np.array([0.0]),
        ),
        (
            np.array([0.8]),
            np.array([10.0]),
            np.array([20.0]),
            0.1,
            2.0,
            np.array([0.0]),
        ),
    ],
)
def test_calculate_subsurface_stormflow_parametrized(
    effective_saturation,
    root_soil_moisture,
    transpiration,
    coeff,
    exponent,
    expected,
):
    """Test subsurface stormflow."""
    from virtual_ecosystem.models.hydrology.below_ground import (
        calculate_subsurface_stormflow,
    )

    result = calculate_subsurface_stormflow(
        effective_saturation=effective_saturation,
        root_soil_moisture=root_soil_moisture,
        transpiration=transpiration,
        stormflow_coefficient=coeff,
        saturation_exponent=exponent,
    )

    np.testing.assert_allclose(result, expected)
