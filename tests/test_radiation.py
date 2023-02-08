"""Test module for abiotic.radiation.py."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest

# from virtual_rainforest.core.model import InitialisationError


@pytest.fixture
def dummy_data():
    """Creates a dummy data object for use in tests."""

    from xarray import DataArray

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
        dims=["cell_id", "canopy_layer"],
    )
    data["surface_temperature"] = DataArray([20, 20], dims=["cell_id"])
    data["canopy_absorption"] = DataArray(
        [
            [300, 200, 100],
            [300, 200, 100],
        ],
        dims=["cell_id", "canopy_layer"],
    )

    return data


def test_radiation_class(dummy_data):
    """Test elevation above zero."""

    from virtual_rainforest.models.abiotic.radiation import Radiation

    result = Radiation(dummy_data)

    # Extremely circular test that checks that the results are what they were when we
    # ran this the first time
    assert np.allclose(
        result.netradiation_surface, np.array([39380.78991513, 61682.05986709])
    )


# @pytest.mark.parametrize(
#     argnames="elev, exp_err, exp_message",
#     argvalues=[
#         pytest.param(np.array([100.0, 1000.0]), does_not_raise(), ()),
#         pytest.param(
#             np.array([-100.0, 1000.0]),
#             pytest.raises(InitialisationError),
#             ("Initial elevation contains at least one negative value!"),
#         ),
#     ],
# )
# def test_radiation_class_errors(elev, exp_err, exp_message):
#     """Test elevation above zero."""

#     from virtual_rainforest.models.abiotic.radiation import Radiation

#     with exp_err:
#         result = Radiation()

#         assert result.elevation.all() == elev.all()


@pytest.mark.parametrize(
    argnames="elev, sun_frac, exp_tau, exp_err",
    argvalues=[
        pytest.param(
            np.array([100, 1000]),
            np.array([0.5, 1.0]),
            np.array([0.501335, 0.770025]),
            does_not_raise(),
            id="standard_array_should_get",
        ),
        pytest.param(
            np.array([100, 1000]),
            np.array([-0.5, 1.5]),
            (),
            pytest.raises(ValueError),
            id="value_error_sf",
        ),
    ],
)
def test_calculate_atmospheric_transmissivity(elev, sun_frac, exp_tau, exp_err):
    """Test atmospheric tansmissivity across elevation and sunshine fractions."""

    from virtual_rainforest.models.abiotic import radiation

    with exp_err:
        result = radiation.calculate_atmospheric_transmissivity(elev, sun_frac)

        assert np.allclose(result, exp_tau)


@pytest.mark.parametrize(
    argnames="exp_tau, exp_err",
    argvalues=[
        pytest.param(
            np.array([0.501335, 0.770025]),
            does_not_raise(),
            id="using_data_object_should_get",
        ),
    ],
)
def test_calculate_atmospheric_transmissivity_data(dummy_data, exp_tau, exp_err):
    """Test atmospheric tansmissivity across elevation and sunshine fractions."""

    from virtual_rainforest.models.abiotic import radiation

    with exp_err:
        result = radiation.calculate_atmospheric_transmissivity(
            dummy_data["elevation"], dummy_data["sunshine_fraction"]
        )

        assert np.allclose(result, exp_tau)


@pytest.mark.parametrize(
    argnames="input_args, exp_ppfd, exp_err, exp_message",
    argvalues=[
        pytest.param(
            {
                "shortwave_in": np.array([100000, 100000]),
                "elevation": np.array([100, 100]),
                "sunshine_fraction": np.array([0.5, 1.0]),
            },
            np.array([0.09920417, 0.14880625]),
            does_not_raise(),
            (),
            id="standard_array_should_get",
        ),
        pytest.param(
            {
                "shortwave_in": np.array([100000, 100000]),
                "elevation": np.array([100, 100]),
            },
            np.array([0.14880625, 0.14880625]),
            does_not_raise(),
            ("The sunshine fraction is set to default = 1"),
            id="no_sf_should_get",
        ),
    ],
)
def test_calc_ppfd(input_args, exp_ppfd, exp_err, exp_message):
    """Test default sunshine fraction and correct ppfd."""
    from virtual_rainforest.models.abiotic import radiation

    with exp_err:

        result = radiation.calculate_ppfd(**input_args)
        assert np.allclose(result, exp_ppfd)


@pytest.mark.parametrize(
    argnames="sw_in, tau, exp_toc_radiation, exp_err",
    argvalues=[
        pytest.param(
            np.array([100000, 10000000]),
            np.array([0.75200, 0.770025]),
            np.array([62251.24974629, 6225127.97051887]),
            does_not_raise(),
            id="standard_array_should_get",
        ),
    ],
)
def test_calc_topofcanopy_radiation(sw_in, tau, exp_toc_radiation, exp_err):
    """Simple check for correct numbers, better test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    with exp_err as err:
        result = radiation.calculate_topofcanopy_radiation(sw_in, tau)

    if not err:
        assert np.allclose(result, exp_toc_radiation)


@pytest.mark.parametrize(
    argnames="temp_canopy, temp_soil, exp_lw, exp_err",
    argvalues=[
        pytest.param(
            np.array(
                [
                    [25, 22, 20],
                    [25, 22, 20],
                ]
            ),
            np.array([20, 20]),
            np.array(
                [
                    [425.64341497, 408.76886994, 397.80135516, 397.80135516],
                    [425.64341497, 408.76886994, 397.80135516, 397.80135516],
                ],
            ),
            does_not_raise(),
            id="standard_array_should_get",
        ),
    ],
)
def test_calc_longwave_radiation(temp_canopy, temp_soil, exp_lw, exp_err):
    """Simple check for correct numbers, better test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    with exp_err:
        result = radiation.calculate_longwave_radiation(temp_canopy, temp_soil)

        assert np.allclose(result, exp_lw)


@pytest.mark.parametrize(
    argnames="toc_radiation, lw_rad, rad_absorbed, exp_netrad, exp_err",
    argvalues=[
        pytest.param(
            np.array([10000, 100000]),
            np.array([[25, 25, 25, 25], [25, 25, 25, 25]]),
            np.array([[20, 20, 20], [20, 20, 20]]),
            np.array([9840, 99840]),
            does_not_raise(),
            id="standard_array_should_get",
        ),
    ],
)
def test_calc_netradiation_surface(
    toc_radiation, lw_rad, rad_absorbed, exp_netrad, exp_err
):
    """Simple check for correct numbers, better test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    with exp_err:
        result = radiation.calculate_netradiation_surface(
            toc_radiation, lw_rad, rad_absorbed
        )

        assert np.allclose(result, exp_netrad)
