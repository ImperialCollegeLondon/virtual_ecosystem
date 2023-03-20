"""Test atmospheric_co2.py."""

from contextlib import nullcontext as does_not_raise

import pytest
import xarray as xr
from xarray import DataArray


@pytest.fixture
def dummy_data():
    """Creates a dummy data object with input data for use in atmospheric CO2 tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=2, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["atmospheric_co2"] = DataArray([390, 395], dims=["cell_id"])
    data["plant_net_co2_assimilation"] = DataArray(
        [[30, 30], [20, 20], [10, 10]], dims=["canopy_layers", "cell_id"]
    )
    data["soil_respiration"] = DataArray([30, 35], dims=["cell_id"])
    data["animal_respiration"] = DataArray([30, 35], dims=["cell_id"])

    return data


def test_calculate_co2_profile(dummy_data):
    """Test default values."""

    from virtual_rainforest.models.abiotic import atmospheric_co2

    data = dummy_data
    result = atmospheric_co2.calculate_co2_profile(
        atmospheric_co2_topofcanopy=data["atmospheric_co2"],
        plant_net_co2_assimilation=data["plant_net_co2_assimilation"],
        soil_respiration=data["soil_respiration"],
        animal_respiration=data["animal_respiration"],
        atmosphere_layers=5,
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[390, 360, 370, 380, 450], [395, 365, 375, 385, 465]],
            dims=["cell_id", "atmosphere_layers"],
        ),
    )


@pytest.mark.parametrize(
    argnames="method,exp_err",
    argvalues=[
        pytest.param(
            "homogenous",
            does_not_raise(),
            id="standard_array_should_get",
        ),
        pytest.param(
            "cubic",
            pytest.raises(NotImplementedError),
            id="NotImplementedError_error",
        ),
    ],
)
def test_initialise_co2_profile(dummy_data, method, exp_err):
    """Test that CO2 profile is initialised correctly."""

    from virtual_rainforest.models.abiotic import atmospheric_co2

    data = dummy_data

    with exp_err:
        result = atmospheric_co2.initialise_co2_profile(
            atmospheric_co2_topofcanopy=data["atmospheric_co2"],
            atmosphere_layers=5,
            initialisation_method=method,
        )

        xr.testing.assert_allclose(
            result,
            DataArray(
                [[390, 395], [390, 395], [390, 395], [390, 395], [390, 395]],
                dims=["atmosphere_layers", "cell_id"],
            ),
        )


def test_calculate_co2_within_canopy(dummy_data):
    """Test that CO2 in canopy is exchanged correctly."""

    from virtual_rainforest.models.abiotic import atmospheric_co2

    data = dummy_data
    initial_co2_profile = DataArray(
        [[400, 400], [400, 400], [400, 400]],
        dims=["atmosphere_layers", "cell_id"],
    )
    result = atmospheric_co2.calculate_co2_within_canopy(
        initial_co2_profile=initial_co2_profile,
        plant_net_co2_assimilation=data["plant_net_co2_assimilation"],
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[370, 370], [380, 380], [390, 390]],
            dims=["atmosphere_layers", "cell_id"],
        ),
    )


def test_calculate_co2_below_canopy(dummy_data):
    """Test correct addition of values."""

    from virtual_rainforest.models.abiotic import atmospheric_co2

    data = dummy_data

    initial_co2_profile = DataArray(
        [[400, 400], [400, 400], [400, 400], [400, 400], [300, 300]],
        dims=["atmosphere_layers", "cell_id"],
    )
    result = atmospheric_co2.calculate_co2_below_canopy(
        initial_co2_profile=initial_co2_profile.isel(atmosphere_layers=0),
        soil_respiration=data["soil_respiration"],
        animal_respiration=data["animal_respiration"],
    )

    xr.testing.assert_allclose(result, DataArray([460, 470], dims="cell_id"))


@pytest.mark.parametrize(
    argnames="input,method,exp_err",
    argvalues=[
        pytest.param(
            {
                "co2_above_canopy": DataArray([400, 400], dims="cell_id"),
                "co2_within_canopy": DataArray(
                    [[350, 350], [340, 340], [330, 330]],
                    dims=["atmosphere_layers", "cell_id"],
                ),
                "co2_below_canopy": DataArray([400, 400], dims="cell_id"),
            },
            False,
            does_not_raise(),
            id="standard_array_should_get",
        ),
        pytest.param(
            {
                "co2_above_canopy": DataArray([400, 400], dims="cell_id"),
                "co2_within_canopy": DataArray(
                    [[350, 350], [350, 350], [350, 350]],
                    dims=["atmosphere_layers", "cell_id"],
                ),
                "co2_below_canopy": DataArray([400, 400], dims="cell_id"),
            },
            True,
            pytest.raises(NotImplementedError),
            id="NotImplementedError_error",
        ),
    ],
)
def test_vertical_mixing_co2(input, method, exp_err):
    """Test if exception is raised as mixed in correct order."""

    from virtual_rainforest.models.abiotic import atmospheric_co2

    with exp_err:
        result = atmospheric_co2.vertical_mixing_co2(**input, mixing=method)

        xr.testing.assert_allclose(
            result,
            DataArray(
                [[400, 350, 340, 330, 400], [400, 350, 340, 330, 400]],
                dims=["cell_id", "atmosphere_layers"],
            ),
        )
