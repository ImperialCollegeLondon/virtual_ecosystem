"""Test module for energy_balance.py."""

from contextlib import nullcontext as does_not_raise

import pytest
import xarray as xr
from xarray import DataArray


# TODO test error
def test_initialise_absorbed_radiation():
    """Test initial absorbed radiation."""

    from virtual_rainforest.models.abiotic import energy_balance
    from virtual_rainforest.models.abiotic.energy_balance import (
        EnergyBalanceConstants as const,
    )

    result = energy_balance.initialise_absorbed_radiation(
        topofcanopy_radiation=DataArray([100, 100], dims=["cell_id"]),
        leaf_area_index=DataArray(
            [[3, 3], [2, 2], [1, 1]], dims=["canopy_layers", "cell_id"]
        ),
        canopy_layers=3,
        light_extinction_coefficient=const.light_extinction_coefficient,
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [
                [2.95544665, 2.95544665],
                [1.9216109, 1.9216109],
                [0.94648909, 0.94648909],
            ],
            dims=["canopy_layers", "cell_id"],
        ),
    )


@pytest.mark.parametrize(
    argnames="input, exp_output, exp_err",
    argvalues=[
        pytest.param(
            {
                "temperature_top": DataArray([20, 20], dims="cell_id"),
                "temperature_bottom": DataArray([15, -5], dims="cell_id"),
                "canopy_layers": 3,
                "soil_layers": 2,
                "option": "linear",
            },
            DataArray(
                [
                    [
                        [15.0, -5.0],
                        [16.25, 1.25],
                        [17.5, 7.5],
                        [18.75, 13.75],
                        [20.0, 20.0],
                    ]
                ]
            ),
            does_not_raise(),
            id="standard_array_should_get",
        ),
    ],
)
def test_temperature_interpolation(input, exp_output, exp_err):
    """Test temperature interpolation method."""

    from virtual_rainforest.models.abiotic import energy_balance

    with exp_err:
        result1 = energy_balance.temperature_interpolation(**input)

    xr.testing.assert_allclose(result1, exp_output)


def test_initialise_canopy_temperature():
    """Test initialisation of canopy temperature profile."""

    from virtual_rainforest.models.abiotic import energy_balance

    result = energy_balance.initialise_canopy_temperature(
        air_temperature=DataArray([20, 10], dims="cell_id"),
        absorbed_radiation=DataArray(
            [[100, 100], [100, 100], [100, 100]],
            dims=["canopy_layers", "cell_id"],
        ),
    )

    xr.testing.assert_allclose(
        result,
        DataArray([[21, 11], [21, 11], [21, 11]], dims=["canopy_layers", "cell_id"]),
    )


# -----------------------------------------
# the following tests are not complete or functions are not correct


def test_initialise_air_temperature_conductivity():
    """Test."""
    from virtual_rainforest.models.abiotic import energy_balance

    result = energy_balance.initialise_air_temperature_conductivity(
        canopy_height=DataArray([20, 20], dims="cell_id")
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[10.0, 10.0], [5.0, 5.0], [5.0, 5.0], [16.666667, 16.666667]],
            dims=["canopy_layers", "cell_id"],
        ),
    )


# TODO test error for not implemented method
def test_temperature_conductivity_interpolation():
    """Test for temp conductivity interpolation."""

    from virtual_rainforest.models.abiotic import energy_balance
    from virtual_rainforest.models.abiotic.energy_balance import (
        EnergyBalanceConstants as const,
    )

    result2 = energy_balance.temperature_conductivity_interpolation(
        min_conductivity=const.max_leaf_conductivity,
        max_conductivity=const.max_leaf_air_conductivity,
    )

    xr.testing.assert_allclose(
        result2, DataArray([0.32, 0.255, 0.19], dims="canopy_layers")
    )


def test_set_canopy_node_heights():
    """Test."""

    from virtual_rainforest.models.abiotic import energy_balance

    result = energy_balance.set_canopy_node_heights(
        canopy_height=DataArray([20, 10], dims="cell_id")
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[0.00833333, 0.01666667], [0.025, 0.05], [0.04166667, 0.08333333]],
            dims=["canopy_layers", "cell_id"],
        ),
    )


def test_set_soil_node_depths():
    """Test."""
    from virtual_rainforest.models.abiotic import energy_balance

    result = energy_balance.set_soil_node_depths(
        soil_depth=DataArray([1.0, 2.0], dims="cell_id")
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[0.0, 0.37371231], [0.0, 0.37371231]],
            dims=["soil_layers", "cell_id"],
        ),
    )


def test_set_initial_canopy_windspeed():
    """Test."""
    from virtual_rainforest.models.abiotic import energy_balance

    result = energy_balance.set_initial_canopy_windspeed(
        wind_speed_10m=DataArray([1.0, 2.0], dims="cell_id")
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[0.33333333, 0.16666667], [0.66666667, 0.33333333], [1.0, 0.5]],
            dims=["canopy_layers", "cell_id"],
        ),
    )


def test_class():
    """Test initialisation of EnergyBalance class."""
    pass


def test_run_energy_balance():
    """Test run energy balance."""
    pass
