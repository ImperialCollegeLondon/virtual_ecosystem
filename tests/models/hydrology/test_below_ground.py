"""Test module for hydrology.below_ground.py."""

import numpy as np
import pytest

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.hydrology.constants import HydroConsts


@pytest.mark.parametrize(
    "soilm_cap, soilm_res, hydr_con, nonlin_par, gw_cap",
    [
        (
            CoreConsts.soil_moisture_capacity,
            HydroConsts.soil_moisture_residual,
            HydroConsts.hydraulic_conductivity,
            HydroConsts.van_genuchten_nonlinearily_parameter,
            HydroConsts.groundwater_capacity,
        ),
        (
            np.array([[0.9, 0.9, 0.9], [0.9, 0.9, 0.9]]),
            np.array([[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]),
            np.array([[0.001, 0.001, 0.001], [0.001, 0.001, 0.001]]),
            np.array([2, 2, 2]),
            np.array([0.9, 0.9, 0.9]),
        ),
    ],
)
def test_calculate_vertical_flow(
    soilm_cap,
    soilm_res,
    hydr_con,
    nonlin_par,
    gw_cap,
):
    """Test vertical flow with float or DataArray input."""

    from virtual_ecosystem.models.hydrology.below_ground import calculate_vertical_flow

    soil_moisture = np.array([[0.3, 0.6, 0.9], [0.3, 0.6, 0.9]])
    layer_thickness = np.array([[500, 500, 500], [500, 500, 500]])
    layer_depth = np.array([500, 1000])
    result = calculate_vertical_flow(
        soil_moisture=soil_moisture,
        soil_layer_thickness=layer_thickness,
        soil_layer_depth=layer_depth,
        soil_moisture_capacity=soilm_cap,
        soil_moisture_residual=soilm_res,
        saturated_hydraulic_conductivity=hydr_con,
        air_entry_potential_inverse=1.0,
        van_genuchten_nonlinearily_parameter=nonlin_par,
        pore_connectivity_parameter=0.5,
        groundwater_capacity=gw_cap,
        seconds_to_day=86400,
    )

    exp_matric_pot = np.array(
        [
            [-3.872983, -1.249, 0.0],
            [-3.872983, -1.249, 0.0],
        ]
    )
    exp_flow = np.array(
        [
            [4.355972e-02, 3.287222e00, 8.640000e01],
            [4.355972e-02, 3.287222e00, 8.640000e01],
        ]
    )
    np.testing.assert_allclose(result["matric_potential"], exp_matric_pot, rtol=0.001)
    np.testing.assert_allclose(result["vertical_flow"], exp_flow, rtol=0.001)


def test_update_soil_moisture():
    """Test soil moisture update."""

    from virtual_ecosystem.models.hydrology.below_ground import update_soil_moisture

    soil_moisture = np.array([[30, 60, 50], [300, 600, 500], [300, 600, 500]])
    vertical_flow = np.array([[10, 2, 3], [10, 2, 3], [15, 25, 35]])
    evapotranspiration = np.array([10, 2, 3])
    layer_thickness = np.array([[100, 100, 100], [900, 900, 900], [900, 900, 900]])
    exp_result = np.array([[20, 58, 47], [290.0, 598.0, 497.0], [300.0, 600.0, 500.0]])

    result = update_soil_moisture(
        soil_moisture,
        vertical_flow,
        evapotranspiration,
        CoreConsts.soil_moisture_capacity * layer_thickness,
        HydroConsts.soil_moisture_residual * layer_thickness,
    )

    np.testing.assert_allclose(result, exp_result, rtol=0.001)


def test_calculate_matric_potential():
    """Test that function to convert soil moisture to a water potential works."""
    from virtual_ecosystem.models.hydrology.below_ground import (
        calculate_matric_potential,
    )

    constants = HydroConsts()
    expected_potentials = np.repeat(-17.320508, 3)
    actual_potentials = calculate_matric_potential(
        effective_saturation=np.repeat(0.5, 3),
        air_entry_potential_inverse=constants.air_entry_potential_inverse,
        van_genuchten_nonlinearily_parameter=(
            constants.van_genuchten_nonlinearily_parameter
        ),
    )

    np.testing.assert_allclose(actual_potentials, expected_potentials, rtol=0.001)


def test_update_groundwater_storage(dummy_climate_data):
    """Test the update_groundwater_storage() function."""

    from virtual_ecosystem.models.hydrology.below_ground import (
        update_groundwater_storage,
    )
    from virtual_ecosystem.models.hydrology.constants import HydroConsts

    data = dummy_climate_data
    result = update_groundwater_storage(
        groundwater_storage=np.array(data["groundwater_storage"]),
        vertical_flow_to_groundwater=np.array([2, 4, 5, 5]),
        bypass_flow=np.array([2, 4, 5, 5]),
        max_percolation_rate_uzlz=HydroConsts.max_percolation_rate_uzlz,
        groundwater_loss=HydroConsts.groundwater_loss,
        reservoir_const_upper_groundwater=HydroConsts.reservoir_const_upper_groundwater,
        reservoir_const_lower_groundwater=HydroConsts.reservoir_const_lower_groundwater,
    )

    exp_groundwater = np.array([[453, 457, 459, 459], [450.0, 450.0, 450.0, 450]])
    exp_upper_flow = np.array([22.65, 22.85, 22.95, 22.95])
    exp_lower_flow = np.array([22.5, 22.5, 22.5, 22.5])
    np.testing.assert_allclose(result["groundwater_storage"], exp_groundwater)
    np.testing.assert_allclose(result["subsurface_flow"], exp_upper_flow)
    np.testing.assert_allclose(result["baseflow"], exp_lower_flow)
