"""Test module for abiotic.radiation.py."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest

# from core.constants import CONSTANTS as C  # this doesn't exist yet
from virtual_rainforest.models.abiotic.radiation import ALBEDO_SHORTWAVE, ALBEDO_VIS


@pytest.mark.parametrize(
    argnames=["cname"],
    argvalues=[
        ("ALBEDO_SHORTWAVE",),
        ("ALBEDO_VIS",),
        ("BEER_REGRESSION",),
        ("BOLZMAN_CONSTANT",),
        ("CANOPY_EMISSIVITY",),
        ("CELSIUS_TO_KELVIN",),
        ("CLOUDY_TRANSMISSIVITY",),
        ("FLUX_TO_ENERGY",),
        ("SECOND_TO_DAY",),
        ("SOIL_EMISSIVITY",),
        ("TRANSMISSIVITY_COEFFICIENT",),
    ],
)
def test_import_constants2(cname):
    """Test constants can be imported."""

    # Get the module that should contain the constants
    import virtual_rainforest.models.abiotic.radiation as rad

    # Check that the constant can be retrieved from the module without
    # raising an AttributeError.
    with does_not_raise():
        assert getattr(rad, cname)


@pytest.fixture
def radiation_fixture():
    """Create a reusable radiation fixture."""
    from virtual_rainforest.models.abiotic.radiation import Radiation

    return Radiation(100)


@pytest.mark.parametrize(
    argnames="input, exp_tau, exp_ppfd",
    argvalues=[
        (29376000, 0.752, 43.713),
        (
            np.array([29376000, 29376000]),
            np.array([0.752, 0.752]),
            np.array([43.713, 43.713]),
        ),
    ],
)
def test_calc_ppfd(radiation_fixture, input, exp_tau, exp_ppfd):
    """Simple check for correct numbers, better test to be decided."""

    tau = radiation_fixture.calc_ppfd(input, 1.0)
    assert tau == pytest.approx(exp_tau, 0.1)
    assert radiation_fixture.ppfd == pytest.approx(exp_ppfd, 0.1)


@pytest.mark.parametrize(
    argnames="input, exp_tau, exp_toc_radiation",
    argvalues=[
        (29376000, 0.752, 18335385.16),
        (
            np.array([29376000, 29376000]),
            np.array([0.752, 0.752]),
            np.array([18335385.16, 18335385.16]),
        ),
    ],
)
def test_calc_topofcanopy_radiation(
    radiation_fixture, input, exp_tau, exp_toc_radiation
):
    """Simple check for correct numbers, better test to be decided."""

    tau = radiation_fixture.calc_ppfd(input, 1.0)
    assert tau == pytest.approx(exp_tau, 0.1)
    radiation_fixture.calc_topofcanopy_radiation(tau, input, 1.0)
    assert radiation_fixture.topofcanopy_radiation == pytest.approx(
        exp_toc_radiation, 0.1
    )


@pytest.mark.parametrize(
    argnames="temp_canopy, temp_soil, exp_lw_canopy, exp_lw_soil",
    argvalues=[
        (25, 25, 425.6434, 425.6434),
        (
            np.array([25, 25]),
            np.array([25, 25]),
            np.array([425.6434, 425.6434]),
            np.array([425.6434, 425.6434]),
        ),
    ],
)
def test_calc_longwave_radiation(
    radiation_fixture, temp_canopy, temp_soil, exp_lw_canopy, exp_lw_soil
):
    """Simple check for correct numbers, better test to be decided."""

    radiation_fixture.calc_longwave_radiation(temp_canopy, temp_soil)
    assert radiation_fixture.longwave_canopy == pytest.approx(exp_lw_canopy)
    assert radiation_fixture.longwave_soil == pytest.approx(exp_lw_soil)


@pytest.mark.parametrize(
    argnames="toc_radiation, lw_canopy, lw_soil, rad_absorbed, exp_netrad",
    argvalues=[
        (10000, 100, 100, 200, 9600),
        (
            np.array([10000, 10000]),
            np.array([100, 100]),
            np.array([100, 100]),
            np.array([200, 200]),
            np.array([9600, 9600]),
        ),
    ],
)
def test_calc_netradiation_surface(
    radiation_fixture, toc_radiation, lw_canopy, lw_soil, rad_absorbed, exp_netrad
):
    """Simple check for correct numbers, better test to be decided."""

    radiation_fixture.topofcanopy_radiation = toc_radiation
    radiation_fixture.longwave_canopy = lw_canopy
    radiation_fixture.longwave_soil = lw_soil
    radiation_fixture.calc_netradiation_surface(rad_absorbed)
    assert radiation_fixture.netradiation_surface == pytest.approx(exp_netrad)


@pytest.mark.parametrize(
    argnames=(
        "elev",
        "sw_in",
        "sun_hours",
        "temp_canopy",
        "temp_soil",
        "rad_absorbed",
        "exp_ppfd",
        "exp_toc_rad",
        "exp_lw_canopy",
        "exp_lw_soil",
        "exp_netrad",
    ),
    argvalues=[
        (
            100.0,
            29376000.0,
            1.0,
            25.0,
            25.0,
            200.0,
            43.713,
            18335385.16,
            425.6434,
            425.6434,
            18334333.83,
        ),
        (
            np.array([100.0, 100.0]),
            np.array([29376000.0, 29376000.0]),
            np.array([1.0, 1.0]),
            np.array([25.0, 25.0]),
            np.array([25.0, 25.0]),
            np.array([200.0, 200.0]),
            np.array([43.713, 43.713]),
            np.array([18335385.16, 18335385.16]),
            np.array([425.6434, 425.6434]),
            np.array([425.6434, 425.6434]),
            np.array([18334333.83, 18334333.83]),
        ),
    ],
)
def test_radiation_balance(
    radiation_fixture,
    elev,
    sw_in,
    sun_hours,
    temp_canopy,
    temp_soil,
    rad_absorbed,
    exp_ppfd,
    exp_toc_rad,
    exp_lw_canopy,
    exp_lw_soil,
    exp_netrad,
):
    """Simple check for correct numbers, better test to be decided."""

    radiation_fixture.radiation_balance(
        elevation=elev,
        shortwave_in=sw_in,
        sunshine_hours=sun_hours,
        albedo_vis=ALBEDO_VIS,
        albedo_shortwave=ALBEDO_SHORTWAVE,
        canopy_temperature=temp_canopy,
        surface_temperature=temp_soil,
        canopy_absorption=rad_absorbed,
    )

    assert radiation_fixture.ppfd == pytest.approx(exp_ppfd, 0.1)
    assert radiation_fixture.topofcanopy_radiation == pytest.approx(exp_toc_rad, 0.1)
    assert radiation_fixture.longwave_canopy == pytest.approx(exp_lw_canopy)
    assert radiation_fixture.longwave_soil == pytest.approx(exp_lw_soil)
    assert radiation_fixture.netradiation_surface == pytest.approx(exp_netrad, 0.1)
