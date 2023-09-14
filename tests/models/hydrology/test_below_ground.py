"""Test module for hydrology.below_ground.py."""


import numpy as np
import pytest

from virtual_rainforest.models.hydrology.constants import HydroConsts


@pytest.mark.parametrize(
    "soilm_cap, soilm_res, hydr_con, hydr_grad, nonlin_par, gw_cap",
    [
        (
            HydroConsts.soil_moisture_capacity,
            HydroConsts.soil_moisture_residual,
            HydroConsts.hydraulic_conductivity,
            HydroConsts.hydraulic_gradient,
            HydroConsts.nonlinearily_parameter,
            HydroConsts.groundwater_capacity,
        ),
        (
            np.array([[0.9, 0.9, 0.9], [0.9, 0.9, 0.9]]),
            np.array([[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]),
            np.array([[0.001, 0.001, 0.001], [0.001, 0.001, 0.001]]),
            np.array([[0.01, 0.01, 0.01], [0.01, 0.01, 0.01]]),
            np.array([2, 2, 2]),
            np.array([0.9, 0.9, 0.9]),
        ),
    ],
)
def test_calculate_vertical_flow(
    soilm_cap,
    soilm_res,
    hydr_con,
    hydr_grad,
    nonlin_par,
    gw_cap,
):
    """Test vertical flow with float or DataArray input."""

    from virtual_rainforest.models.hydrology.below_ground import calculate_vertical_flow

    soil_moisture = np.array([[0.3, 0.6, 0.9], [0.3, 0.6, 0.9]])
    layer_thickness = np.array([[500, 500, 500], [500, 500, 500]])

    result = calculate_vertical_flow(
        soil_moisture,
        layer_thickness,
        soilm_cap,
        soilm_res,
        hydr_con,
        hydr_grad,
        nonlin_par,
        gw_cap,
        2.628e6,
    )
    exp_flow = np.array(
        [
            [1.311692, 98.98647, 2601.720],
            [1.31169, 98.986, 2601.720],
        ]
    )
    np.testing.assert_allclose(result, exp_flow, rtol=0.001)


def test_update_soil_moisture():
    """Test soil moisture update."""

    from virtual_rainforest.models.hydrology.below_ground import update_soil_moisture

    soil_moisture = np.array([[30, 60, 50], [300, 600, 500], [300, 600, 500]])
    vertical_flow = np.array([[10, 2, 3], [10, 2, 3], [15, 25, 35]])
    evapotranspiration = np.array([10, 2, 3])
    layer_thickness = np.array([[100, 100, 100], [900, 900, 900], [900, 900, 900]])
    exp_result = np.array([[20, 58, 47], [290.0, 598.0, 497.0], [300.0, 600.0, 500.0]])

    result = update_soil_moisture(
        soil_moisture,
        vertical_flow,
        evapotranspiration,
        HydroConsts.soil_moisture_capacity * layer_thickness,
        HydroConsts.soil_moisture_residual * layer_thickness,
    )

    np.testing.assert_allclose(result, exp_result, rtol=0.001)
