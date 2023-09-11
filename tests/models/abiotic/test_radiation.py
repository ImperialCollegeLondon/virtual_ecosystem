"""Test module for abiotic.radiation.py."""

from contextlib import nullcontext as does_not_raise

import pytest
import xarray as xr
from xarray import DataArray

from virtual_rainforest.core.exceptions import InitialisationError


@pytest.fixture
def dummy_data():
    """Creates a dummy data object for use in tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=2, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["elevation"] = DataArray([100, 1000], dims=["cell_id"])
    data["shortwave_in"] = DataArray([100000, 100000], dims=["cell_id"])
    data["sunshine_fraction"] = DataArray([0.5, 1.0], dims=["cell_id"])
    data["canopy_temperature"] = DataArray(
        [
            [25, 22, 20],
            [25, 22, 20],
        ],
        dims=["cell_id", "canopy_layers"],
    )
    data["surface_temperature"] = DataArray([20, 20], dims=["cell_id"])
    data["canopy_absorption"] = DataArray(
        [
            [300, 200, 100],
            [300, 200, 100],
        ],
        dims=["cell_id", "canopy_layers"],
    )

    return data


def test_class_ini(dummy_data):
    """Test class initialisation with dummy data object."""

    from virtual_rainforest.models.abiotic import radiation

    result = radiation.Radiation(dummy_data)
    xr.testing.assert_allclose(
        result.ppfd, DataArray([0.099204, 0.1523725], dims="cell_id")
    )


def test_simple_atmospheric_transmissivity():
    """Test atmospheric tansmissivity across elevation and sunshine fractions."""

    from virtual_rainforest.models.abiotic import radiation

    result = radiation.calculate_atmospheric_transmissivity(
        DataArray([100, 1000], dims="cell_id"), DataArray([0.5, 1.0], dims="cell_id")
    )
    xr.testing.assert_allclose(result, DataArray([0.501335, 0.770025], dims="cell_id"))


@pytest.mark.parametrize(
    argnames="elev, sun_frac, exp_err",
    argvalues=[
        pytest.param(
            DataArray([100, 1000], dims="cell_id"),
            DataArray([0.5, 1.0], dims="cell_id"),
            does_not_raise(),
            id="standard_array_should_get",
        ),
        pytest.param(
            DataArray([100, 1000], dims="cell_id"),
            DataArray([0.5, 1.5], dims="cell_id"),
            pytest.raises(InitialisationError),
            id="InitialisationError_error",
        ),
    ],
)
def test_calculate_atmospheric_transmissivity(elev, sun_frac, exp_err):
    """Test sunshine fractions in range or raise error."""

    from virtual_rainforest.models.abiotic import radiation

    with exp_err:
        radiation.calculate_atmospheric_transmissivity(
            elevation=elev, sunshine_fraction=sun_frac
        )


@pytest.mark.parametrize(
    argnames="input, exp_ppfd",
    argvalues=[
        pytest.param(
            {
                "tau": DataArray([0.501335, 0.770025], dims="cell_id"),
                "shortwave_in": DataArray([100000, 1000000], dims="cell_id"),
                "albedo_vis": DataArray([0.03, 0.03], dims="cell_id"),
            },
            DataArray([0.099204, 1.523725], dims="cell_id"),
            id="standard_array_should_get",
        ),
        pytest.param(
            {
                "tau": DataArray([0.501335, 0.770025], dims="cell_id"),
                "shortwave_in": DataArray([100000, 1000000], dims="cell_id"),
            },
            DataArray([0.099204, 1.523725], dims="cell_id"),
            id="check_default",
        ),
    ],
)
def test_calc_ppfd(input, exp_ppfd):
    """Test default albedo_vis and correct ppfd."""

    from virtual_rainforest.models.abiotic import radiation

    result = radiation.calculate_ppfd(**input)
    xr.testing.assert_allclose(result, exp_ppfd)


@pytest.mark.parametrize(
    argnames="input, exp_toc",
    argvalues=[
        pytest.param(
            {
                "tau": DataArray([0.501335, 0.770025], dims="cell_id"),
                "shortwave_in": DataArray([100000, 1000000], dims="cell_id"),
                "albedo_shortwave": DataArray([0.2, 0.2], dims="cell_id"),
            },
            DataArray([40106.8, 616020.0], dims="cell_id"),
            id="standard_array_should_get",
        ),
        pytest.param(
            {
                "tau": DataArray([0.501335, 0.770025], dims="cell_id"),
                "shortwave_in": DataArray([100000, 1000000], dims="cell_id"),
            },
            DataArray([41610.805, 639120.75], dims="cell_id"),
            id="check_default",
        ),
    ],
)
def test_calc_tocradiation(input, exp_toc):
    """Test default albedo_shortwave and correct top of canopy radiation."""

    from virtual_rainforest.models.abiotic import radiation

    result = radiation.calculate_topofcanopy_radiation(**input)
    xr.testing.assert_allclose(result, exp_toc)


@pytest.mark.parametrize(
    argnames="input, exp_result",
    argvalues=[
        pytest.param(
            DataArray([20, 20], dims="cell_id"),
            DataArray([397.80135516, 397.80135516], dims="cell_id"),
            id="soil_longwave",
        ),
        pytest.param(
            DataArray([[25, 22, 20], [25, 22, 20]], dims=["cell_id", "canopy_layers"]),
            DataArray(
                [
                    [425.64341497, 408.76886994, 397.80135516],
                    [425.64341497, 408.76886994, 397.80135516],
                ],
                dims=["cell_id", "canopy_layers"],
            ),
            id="canopy_longwave",
        ),
    ],
)
def calc_longwave_radiation(input, exp_result):
    """Test longwave radiation calculated with correct dimensions."""

    from virtual_rainforest.models.abiotic import radiation

    result = radiation.calculate_longwave_radiation(input)
    xr.testing.assert_allclose(result, exp_result)


@pytest.mark.parametrize(
    argnames="toc_rad, canopy_abs, lw_canopy, lw_soil, exp_result",
    argvalues=[
        pytest.param(
            DataArray([100000, 100000], dims="cell_id"),
            DataArray([[25, 25, 25], [25, 25, 25]], dims=["cell_id", "canopy_layers"]),
            DataArray([[20, 20, 20], [20, 20, 20]], dims=["cell_id", "canopy_layers"]),
            DataArray([20, 20], dims="cell_id"),
            DataArray([99845, 99845], dims=["cell_id"]),
            id="soil_longwave",
        ),
    ],
)
def test_calculate_netradiation(toc_rad, canopy_abs, lw_canopy, lw_soil, exp_result):
    """Test sum across canopy layers."""

    from virtual_rainforest.models.abiotic import radiation

    result = radiation.calculate_netradiation_surface(
        toc_rad, canopy_abs, lw_canopy, lw_soil
    )
    xr.testing.assert_allclose(result, exp_result)
