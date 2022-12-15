"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL
from math import isclose

import numpy as np
import pytest

from virtual_rainforest.core.model import InitialisationError
from virtual_rainforest.soil.carbon import (
    SoilCarbon,
    scalar_moisture,
    scalar_temperature,
)

from .conftest import log_check


@pytest.mark.parametrize(
    "maom,lmwc,raises,expected_log_entries",
    [
        (
            np.array([23.0, 12.0], dtype=np.float32),
            np.array([98.0, 7.0], dtype=np.float32),
            does_not_raise(),
            (),
        ),
        (
            np.array([23.0, 12.0], dtype=np.float32),
            np.array([98.0], dtype=np.float32),
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Dimension mismatch for initial carbon pools!",
                ),
            ),
        ),
        (
            np.array([23.0, 12.0], dtype=np.float32),
            np.array([98.0, -24.0], dtype=np.float32),
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Initial carbon pools contain at least one negative value!",
                ),
            ),
        ),
    ],
)
def test_soil_carbon_class(caplog, maom, lmwc, raises, expected_log_entries):
    """Test SoilCarbon class initialisation."""

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        soil_carbon = SoilCarbon(maom, lmwc)

        assert (soil_carbon.maom == maom).all()
        assert (soil_carbon.lmwc == lmwc).all()

    log_check(caplog, expected_log_entries)


# TEST update_pools()
# SO test that it runs without failing
# And test that the pools update as expected
# And by the correct amount
# To get the amounts right it probably makes sense to test lower level functions first

# TEST mineral_association()
# Again test that it runs without errors
# Check that correct pair of fluxes is returned


def test_scalar_temperature():
    """Test that scalar_temperature runs and generates the correct value."""

    soil_temperature = np.array([35.0, 37.5], dtype=np.float32)
    temp_scalar = scalar_temperature(soil_temperature)
    print(temp_scalar)

    assert isclose(temp_scalar[0].item(), 1.271131634)
    assert isclose(temp_scalar[1].item(), 1.271966338)


def test_scalar_moisture():
    """Test that scalar_moisture runs and generates the correct value."""

    soil_moisture = np.array([0.5, 0.7], dtype=np.float32)
    moist_scalar = scalar_moisture(soil_moisture)

    assert isclose(moist_scalar[0].item(), 0.750035643)
    assert isclose(moist_scalar[1].item(), 0.947787225)
