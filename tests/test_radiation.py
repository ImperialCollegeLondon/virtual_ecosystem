"""Test module for abiotic.radiation.py."""

import numpy as np
import pytest

# from core.constants import CONSTANTS as C  # this doesn't exist yet
# from core.constants import CONSTANTS as C
# this doesn't exist yet; optional scipy
CLOUDY_TRANSMISSIVITY = 0.25  # cloudy transmittivity (Linacre, 1968)
TRANSMISSIVITY_COEFFICIENT = (
    0.50  # angular coefficient of transmittivity (Linacre, 1968)
)
FLUX_TO_ENERGY = 2.04  # from flux to energy conversion, umol/J (Meek et al., 1984)
BOLZMAN_CONSTANT = 5.67 * 10 ** (-8)  # Stephan Bolzman constant W m-2 K-4
SOIL_EMISSIVITY = 0.95  # default for tropical rainforest
CANOPY_EMISSIVITY = 0.95  # default for tropical rainforest
BEER_REGRESSION = 2.67e-5  # parameter in equation for atmospheric transmissivity based
# on regression of Beer’s radiation extinction function (Allen 1996)
ALBEDO_VIS = np.array(0.03, dtype=float)
ALBEDO_SHORTWAVE = np.array(0.17, dtype=float)
CELCIUS_TO_KELVIN = 273.15  # calculate absolute temperature in Kelvin


def test_calc_ppfd():
    """Simple check for correct numbers, better test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    dummy = radiation.Radiation(100)
    tau = dummy.calc_ppfd(29376000, 1.0)
    assert tau == pytest.approx(0.752, 0.1)
    assert dummy.ppfd == pytest.approx(43.713, 0.1)


def test_calc_topofcanopy_radiation():
    """Simple check for correct numbers, better test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    dummy = radiation.Radiation(100)
    tau = dummy.calc_ppfd(29376000, 1.0)
    assert tau == pytest.approx(0.752, 0.1)
    dummy.calc_topofcanopy_radiation(tau, 29376000, 1.0)
    assert dummy.topofcanopy_radiation == pytest.approx(18335385.16, 0.1)


def test_calc_longwave_radiation():
    """Simple check for correct numbers, better test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    dummy = radiation.Radiation(100)
    dummy.calc_longwave_radiation(25, 25)
    assert dummy.longwave_canopy == pytest.approx(425.6434)
    assert dummy.longwave_soil == pytest.approx(425.6434)


def test_calc_netradiation_surface():
    """Test to be decided."""
    pass


def test_radiation_balance():
    """Simple check for correct numbers, better test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    dummy = radiation.Radiation(100)
    dummy.radiation_balance(
        elevation=100.0,
        shortwave_in=29376000,
        sunshine_hours=1.0,
        albedo_vis=ALBEDO_VIS,
        albedo_shortwave=ALBEDO_SHORTWAVE,
        canopy_temperature=25.0,
        surface_temperature=25.0,
        canopy_absorption=0.0,
    )

    assert dummy.ppfd == pytest.approx(43.713, 0.1)
    assert dummy.topofcanopy_radiation == pytest.approx(18335385.16, 0.1)
    assert dummy.longwave_canopy == pytest.approx(425.6434)
    assert dummy.longwave_soil == pytest.approx(425.6434)
