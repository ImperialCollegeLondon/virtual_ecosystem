"""Test module for energy_balance.py."""

from contextlib import nullcontext as does_not_raise

import pytest
import xarray as xr
from xarray import DataArray


# TODO introduce error
def test_calculate_initial_absorbed_radiation():
    """Test initial absorbed radiation."""

    from virtual_rainforest.models.abiotic import energy_balance
    from virtual_rainforest.models.abiotic.energy_balance import (
        EnergyBalanceConstants as const,
    )

    result = energy_balance.calculate_initial_absorbed_radiation(
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


# TODO sort out types
def test_temp_conductivity_interpolation():
    """Test for temp conductivity interpolation."""

    from virtual_rainforest.models.abiotic import energy_balance
    from virtual_rainforest.models.abiotic.energy_balance import (
        EnergyBalanceConstants as const,
    )

    result2 = energy_balance.temp_conductivity_interpolation(
        min_conductivity=const.max_leaf_conductivity,
        max_conductivity=const.max_leaf_air_conductivity,
    )

    xr.testing.assert_allclose(result2, DataArray[[1, 1, 1]])
