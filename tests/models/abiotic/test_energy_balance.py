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
                    [20.0, 20.0],
                    [18.75, 13.75],
                    [17.5, 7.5],
                    [16.25, 1.25],
                    [15.0, -5.0],
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


# ----------------------------------------------------------------------------
@pytest.fixture
def dummy_data():
    """Creates a dummy data object for use in tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=2, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["leaf_area_index"] = DataArray(
        [[3, 3], [2, 2], [1, 1]], dims=["canopy_layers", "cell_id"]
    )
    data["canopy_height"] = DataArray([5, 30], dims=["cell_id"])
    data["absorbed_radiation"] = DataArray(
        [[30, 30], [20, 20], [10, 10]], dims=["canopy_layers", "cell_id"]
    )
    data["topofcanopy_radiation"] = DataArray([1000, 10000], dims=["cell_id"])
    data["air_temperature_2m"] = DataArray([20, 20], dims=["cell_id"])

    data["mean_annual_temperature"] = DataArray([10, 10], dims=["cell_id"])
    data["relative_humidity_2m"] = DataArray([80, 90], dims=["cell_id"])
    data["atmospheric_pressure_2m"] = DataArray([100, 100], dims=["cell_id"])
    data["soil_depth"] = DataArray([1, 2], dims=["cell_id"])
    data["wind_speed_10m"] = DataArray([1, 10], dims=["cell_id"])

    return data


def test_class(dummy_data):
    """Test initialisation of EnergyBalance class attributes."""
    from virtual_rainforest.models.abiotic.energy_balance import (
        EnergyBalance,
        EnergyBalanceConstants,
    )

    dummy = EnergyBalance(data=dummy_data, const=EnergyBalanceConstants)

    xr.testing.assert_allclose(
        dummy.absorbed_radiation,
        DataArray(
            [[29.554466, 295.544665], [19.216109, 192.16109], [9.464891, 94.648909]],
            dims=["canopy_layers", "cell_id"],
        ),
    )
    xr.testing.assert_allclose(
        dummy.atmospheric_pressure, dummy_data["atmospheric_pressure_2m"]
    )
    xr.testing.assert_allclose(
        dummy.sensible_heat_flux,
        DataArray([[0, 0], [0, 0], [0, 0]], dims=["canopy_layers", "cell_id"]),
    )
    xr.testing.assert_allclose(
        dummy.latent_heat_flux,
        DataArray([[0, 0], [0, 0], [0, 0]], dims=["canopy_layers", "cell_id"]),
    )
    xr.testing.assert_allclose(
        dummy.ground_heat_flux, DataArray([0, 0], dims=["cell_id"])
    )
    xr.testing.assert_allclose(
        dummy.diabatic_correction_factor, DataArray([0, 0], dims=["cell_id"])
    )
    xr.testing.assert_allclose(
        dummy.air_temperature,
        DataArray(
            [[20, 20], [17.5, 17.5], [15.0, 15.0]],
        ),
    )
    xr.testing.assert_allclose(
        dummy.soil_temperature,
        DataArray(
            [[12.5, 12.5], [10.0, 10]],
        ),
    )
    xr.testing.assert_allclose(
        dummy.canopy_temperature,
        DataArray(
            [[20.3, 20.3], [20.2, 20.2], [20.1, 20.1]],
            dims=["canopy_layers", "cell_id"],
        ),
    )
    xr.testing.assert_allclose(
        dummy.height_of_above_canopy, dummy_data["canopy_height"]
    )
    xr.testing.assert_allclose(
        dummy.relative_humidity,
        DataArray(
            [[80, 90], [80, 90], [80, 90]],
            dims=["canopy_layers", "cell_id"],
        ),
    )
    xr.testing.assert_allclose(
        dummy.air_conductivity,
        DataArray(
            [
                [40.0, 6.666667],
                [20.0, 3.333333],
                [20.0, 3.333333],
                [16.666667, 16.666667],
            ],
            dims=["canopy_layers", "cell_id"],
        ),
    )
    xr.testing.assert_allclose(
        dummy.leaf_conductivity,
        DataArray(
            [0.25, 0.285, 0.32],
            dims=["canopy_layers"],
        ),
    )
    xr.testing.assert_allclose(
        dummy.canopy_wind_speed,
        DataArray(
            [[0.333333, 0.033333], [0.666667, 0.066667], [1.0, 0.1]],
            dims=["canopy_layers", "cell_id"],
        ),
    )

    xr.testing.assert_allclose(
        dummy.canopy_node_heights,
        DataArray(
            [[0.033333, 0.005556], [0.1, 0.016667], [0.166667, 0.027778]],
            dims=["canopy_layers", "cell_id"],
        ),
    )
    xr.testing.assert_allclose(
        dummy.soil_node_depths,
        DataArray(
            [[0.0, 0.373712], [0.0, 0.373712]],
            dims=["soil_layers", "cell_id"],
        ),
    )
