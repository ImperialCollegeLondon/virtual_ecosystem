"""Test module for abiotic.radiation.py."""

import pytest
import numpy as np

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
    raise NotImplementedError("Implementation of this feature is missing")


def test_calc_topofcanopy_radiation(shortwave_in, sunshine_hours, albedo_shortwave):
    """Test to be decided."""
    raise NotImplementedError("Implementation of this feature is missing")


def test_calc_longwave_radiation(canopy_temperature, surface_temperature):
    """Test to be decided."""
    raise NotImplementedError("Implementation of this feature is missing")


def test_calc_netradiation_surface(canopy_absorption):
    """Test to be decided."""
    raise NotImplementedError("Implementation of this feature is missing")


def test_radiation_balance(
    elevation,
    shortwave_in,
    sunshine_hours,
    albedo_vis,
    albedo_shortwave,
    canopy_temperature,
    surface_temperature,
    canopy_absorption,
):
    """Test to be decided."""
    raise NotImplementedError("Implementation of this feature is missing")
