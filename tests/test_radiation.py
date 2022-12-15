"""Test module for abiotic.radiation.py."""

# import pytest

# from virtual_rainforest.models.abiotic import radiation
# from core.constants import CONSTANTS as C  # this doesn't exist yet


def test_calc_ppfd(shortwave_in, sunshine_hours, albedo_vis):
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
