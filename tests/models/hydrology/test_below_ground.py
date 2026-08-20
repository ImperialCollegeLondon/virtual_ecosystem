"""Test module for hydrology.below_ground.py."""

import numpy as np
import pytest


@pytest.mark.parametrize(
    "soilm_sat, soilm_res, hydr_con, nonlin_par, gw_cap",
    [
        (0.6, 0.1, 0.001, 2.0, 0.9),
        (
            np.full((2, 3), 0.6),
            np.full((2, 3), 0.1),
            np.full((2, 3), 0.001),
            np.repeat(2.0, 3),
            np.repeat(0.9, 3),
        ),
    ],
)
def test_calculate_vertical_flow(
    soilm_sat,
    soilm_res,
    hydr_con,
    nonlin_par,
    gw_cap,
):
    """Test vertical flow with float or DataArray input."""

    from virtual_ecosystem.models.hydrology.below_ground import calculate_vertical_flow

    soil_moisture = np.array([[0.3, 0.4, 0.6], [0.3, 0.4, 0.6]])
    layer_thickness = np.full((2, 3), 0.5)
    layer_depth = np.array([0.5, 1])
    result = calculate_vertical_flow(
        soil_moisture=soil_moisture,
        soil_layer_thickness=layer_thickness,
        soil_layer_depth=layer_depth,
        soil_moisture_saturation=soilm_sat,
        soil_moisture_residual=soilm_res,
        saturated_hydraulic_conductivity=hydr_con,
        air_entry_potential_inverse=0.01,
        van_genuchten_nonlinearily_parameter=nonlin_par,
        pore_connectivity_parameter=0.5,
        groundwater_capacity=gw_cap,
        seconds_to_day=86400,
        denominator_tolerance=0.001,
    )

    exp_matric_pot = np.array(
        [
            [-228.448392, -132.986526, -0.001],
            [-228.448392, -132.986526, -0.001],
        ]
    )
    exp_flow = np.array(
        [
            [0.000385, 0.002699, 0.00025],
            [0.000385, 0.002699, 0.0009],
        ]
    )
    exp_efsat = np.array(
        [
            [0.401, 0.601, 1.0],
            [0.401, 0.601, 1.0],
        ]
    )
    np.testing.assert_allclose(result["matric_potential"], exp_matric_pot, rtol=0.001)
    np.testing.assert_allclose(result["vertical_flow"], exp_flow, rtol=0.001)
    np.testing.assert_allclose(result["effective_saturation"], exp_efsat, rtol=0.001)


def test_update_soil_moisture(fixture_hydrology_constants):
    """Test soil moisture update."""

    from virtual_ecosystem.models.hydrology.below_ground import update_soil_moisture

    layer_thickness = np.array([[100, 100, 100], [900, 900, 900], [900, 900, 900]])
    exp_result = np.array(
        [[20.0, 51.0, 47.0], [290.0, 459.0, 459.0], [300.0, 459.0, 459.0]]
    )

    result = update_soil_moisture(
        soil_moisture=np.array([[30, 60, 50], [300, 600, 500], [300, 600, 500]]),
        vertical_flow=np.array([[10, 2, 3], [10, 2, 3], [15, 25, 35]]),
        transpiration=np.array([10, 2, 3]),
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
    expected_potentials = np.repeat(-67.927471, 3)
    actual_potentials = calculate_matric_potential(
        effective_saturation=np.repeat(0.5, 3),
        air_entry_potential_inverse=constants.air_entry_potential_inverse,
        van_genuchten_nonlinearily_parameter=(
            constants.van_genuchten_nonlinearily_parameter
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
