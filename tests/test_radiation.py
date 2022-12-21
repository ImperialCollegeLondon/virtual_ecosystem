"""Test module for abiotic.radiation.py."""

import pytest

# from core.constants import CONSTANTS as C  # this doesn't exist yet
from virtual_rainforest.models.abiotic.radiation import (
    ALBEDO_SHORTWAVE,
    ALBEDO_VIS,
    BEER_REGRESSION,
    BOLZMAN_CONSTANT,
    CANOPY_EMISSIVITY,
    CELCIUS_TO_KELVIN,
    CLOUDY_TRANSMISSIVITY,
    FLUX_TO_ENERGY,
    SECOND_TO_DAY,
    SOIL_EMISSIVITY,
    TRANSMISSIVITY_COEFFICIENT,
)


def test_import_constants():
    """Test that constants were imported correctly."""
    assert CLOUDY_TRANSMISSIVITY == 0.25
    assert TRANSMISSIVITY_COEFFICIENT == 0.50
    assert FLUX_TO_ENERGY == 2.04
    assert BOLZMAN_CONSTANT == 5.67e-8
    assert SOIL_EMISSIVITY == 0.95
    assert CANOPY_EMISSIVITY == 0.95
    assert BEER_REGRESSION == 2.67e-5
    assert ALBEDO_VIS == 0.03
    assert ALBEDO_SHORTWAVE == 0.17
    assert CELCIUS_TO_KELVIN == 273.15
    assert SECOND_TO_DAY == 86400


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
    """Simple check for correct numbers, better test to be decided."""
    from virtual_rainforest.models.abiotic import radiation

    dummy = radiation.Radiation(100)
    dummy.topofcanopy_radiation = 10000
    dummy.longwave_canopy = 100
    dummy.longwave_soil = 100
    dummy.calc_netradiation_surface(200)
    assert dummy.netradiation_surface == pytest.approx(9600)


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
