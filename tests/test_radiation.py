"""Test module for abiotic.radiation.py."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest

from virtual_rainforest.models.abiotic import radiation


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

    with exp_err as err:
        result = radiation.calculate_atmospheric_transmissivity(elev, sun_frac)

        # if no error is raised
    if not err:
        assert np.allclose(result, exp_tau)


@pytest.mark.parametrize(
    argnames="sw_in, elev, tau, exp_ppfd, exp_err",
    argvalues=[
        pytest.param(
            np.array([100000, 10000000]),
            np.array([100, 1000]),
            np.array(
                [
                    0.75200,
                    0.770025,
                ]
            ),
            np.array([0.124203, 12.90113]),
            does_not_raise(),
            id="standard_array_should_get",
        ),
    ],
)
def test_calc_ppfd(sw_in, elev, tau, exp_ppfd, exp_err):
    """Simple check for correct numbers, better test to be decided."""

    with exp_err as err:
        result = radiation.calculate_ppfd(sw_in, elev, tau)

    if not err:
        assert np.allclose(result, exp_ppfd)


@pytest.mark.parametrize(
    argnames="sw_in, tau, exp_toc_radiation, exp_err",
    argvalues=[
        pytest.param(
            np.array([100000, 10000000]),
            np.array([0.75200, 0.770025]),
            np.array([62250.83312, 6225127.97052]),
            does_not_raise(),
            id="standard_array_should_get",
        ),
    ],
)
def test_calc_topofcanopy_radiation(sw_in, tau, exp_toc_radiation, exp_err):
    """Simple check for correct numbers, better test to be decided."""

    with exp_err as err:
        result = radiation.calculate_topofcanopy_radiation(sw_in, tau)

    if not err:
        assert np.allclose(result, exp_toc_radiation)


@pytest.mark.parametrize(
    argnames="temp_canopy, temp_soil, result, exp_err",
    argvalues=[
        pytest.param(
            np.array(
                [
                    [25, 25],
                    [22, 22],
                    [20, 20],
                ]
            ),
            np.array([20, 20]),
            np.array(
                [
                    [425.64341497, 425.64341497],
                    [408.76886994, 408.76886994],
                    [397.80135516, 397.80135516],
                    [397.80135516, 397.80135516],
                ],
            ),
            does_not_raise(),
            id="standard_array_should_get",
        ),
    ],
)
def test_calc_longwave_radiation(temp_canopy, temp_soil, exp_lw, exp_err):
    """Simple check for correct numbers, better test to be decided."""

    with exp_err:
        result = radiation.calculate_longwave_radiation(temp_canopy, temp_soil)

        assert np.allclose(result, exp_lw)


@pytest.mark.parametrize(
    argnames="toc_radiation, lw_canopy, lw_soil, rad_absorbed, exp_netrad, exp_err",
    argvalues=[
        pytest.param(
            np.array([10000, 10000]),
            np.array([100, 100]),
            np.array([100, 100]),
            np.array([200, 200]),
            np.array([9600, 9600]),
            does_not_raise(),
            id="standard_array_should_get",
        ),
    ],
)
def test_calc_netradiation_surface(
    toc_radiation, lw_canopy, lw_soil, rad_absorbed, exp_netrad, exp_err
):
    """Simple check for correct numbers, better test to be decided."""

    with exp_err as err:
        result = radiation.calculate_netradiation_surface(
            toc_radiation, lw_canopy, lw_soil, rad_absorbed
        )

    if not err:
        assert np.allclose(result, exp_netrad)
