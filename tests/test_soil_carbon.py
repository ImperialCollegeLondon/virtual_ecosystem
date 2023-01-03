"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL

import numpy as np
import pytest

from virtual_rainforest.core.model import InitialisationError
from virtual_rainforest.models.soil.carbon import SoilCarbonPools

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
        soil_carbon = SoilCarbonPools(maom, lmwc)

        assert (soil_carbon.maom == maom).all()
        assert (soil_carbon.lmwc == lmwc).all()

    log_check(caplog, expected_log_entries)


def test_update_pools():
    """Test that update_pools runs and generates the correct values."""

    # Initialise soil carbon class
    maom = np.array([23.0, 23.0], dtype=np.float32)
    lmwc = np.array([98.0, 55.0], dtype=np.float32)
    soil_carbon = SoilCarbonPools(maom, lmwc)

    # Define all the required variables to run function
    pH = np.array([7.0, 7.0], dtype=np.float32)
    bulk_density = np.array([1350, 1350], dtype=np.float32)
    percent_clay = np.array([50.0, 50.0], dtype=np.float32)
    soil_moisture = np.array([0.5, 0.5], dtype=np.float32)
    soil_temp = np.array([35.0, 35.0], dtype=np.float32)
    dt = 2.0 / 24.0

    soil_carbon.update_pools(
        pH, bulk_density, soil_moisture, soil_temp, percent_clay, dt
    )

    # Check that pools are correctly incremented
    assert np.allclose(soil_carbon.maom, np.array([28.8263, 25.7322]))
    assert np.allclose(soil_carbon.lmwc, np.array([92.1736, 52.2677]))


def test_mineral_association():
    """Test that mineral_association runs and generates the correct values."""

    # Initialise soil carbon class
    maom = np.array([23.0, 23.0], dtype=np.float32)
    lmwc = np.array([98.0, 55.0], dtype=np.float32)
    soil_carbon = SoilCarbonPools(maom, lmwc)

    # Define all the required variables to run function
    pH = np.array([7.0, 7.0], dtype=np.float32)
    bulk_density = np.array([1350, 1350], dtype=np.float32)
    percent_clay = np.array([50.0, 50.0], dtype=np.float32)
    soil_moisture = np.array([0.5, 0.5], dtype=np.float32)
    soil_temp = np.array([35.0, 35.0], dtype=np.float32)

    lmwc_to_maom = soil_carbon.mineral_association(
        pH, bulk_density, soil_moisture, soil_temp, percent_clay
    )

    # Check that expected values are generated
    assert np.allclose(lmwc_to_maom, np.array([69.9158, 32.7868]))


def test_convert_temperature_to_scalar():
    """Test that scalar_temperature runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_temperature_to_scalar

    soil_temperature = np.array([35.0, 37.5], dtype=np.float32)
    temp_scalar = convert_temperature_to_scalar(soil_temperature)

    assert np.allclose(temp_scalar, np.array([1.27113, 1.27196]))


def test_convert_moisture_to_scalar():
    """Test that scalar_moisture runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_moisture_to_scalar

    soil_moisture = np.array([0.5, 0.7], dtype=np.float32)
    moist_scalar = convert_moisture_to_scalar(soil_moisture)

    assert np.allclose(moist_scalar, np.array([0.750035, 0.947787]))
