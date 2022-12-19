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
    """Test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    test = radiation.Radiation(100)
    tau = test.calc_ppfd(29376000, 1.0)
    assert tau == pytest.approx(0.752, 0.1)
    assert test.ppfd == pytest.approx(43.713, 0.1)


def test_calc_topofcanopy_radiation():
    """Test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    test = radiation.Radiation(100)
    tau = test.calc_ppfd(29376000, 1.0)
    assert tau == pytest.approx(0.752, 0.1)
    test.calc_topofcanopy_radiation(tau, 29376000, 1.0)
    assert test.topofcanopy_radiation == pytest.approx(18335385.16, 0.1)


def test_calc_longwave_radiation():
    """Test to be decided."""
    pass


def test_calc_netradiation_surface():
    """Test to be decided."""
    pass


def test_radiation_balance():
    """Test to be decided."""
    pass
