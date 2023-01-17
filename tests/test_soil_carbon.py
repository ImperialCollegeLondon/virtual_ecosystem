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


@pytest.mark.parametrize(
    "maom,lmwc,temp_scalar,moist_scalar,equib_maom,Q_max,output_l_to_m",
    [
        (
            [2.5, 1.7],
            [0.05, 0.02],
            [1.27113, 1.27196],
            [0.750035, 0.947787],
            [19900.19, 969.4813],
            [2.385207e6, 1.980259e6],
            [0.000397665, 1.178336e-5],
        ),
        ([4.5], [0.1], [1.27263], [0.880671], [832.6088], [647142.61], [0.0001434178]),
        ([0.5], [0.005], [1.26344], [0.167814], [742.4128], [2.805371e6], [2.80359e-7]),
    ],
)
def test_mineral_association(
    mocker, maom, lmwc, temp_scalar, moist_scalar, equib_maom, Q_max, output_l_to_m
):
    """Test that mineral_association runs and generates the correct values."""

    # Initialise soil carbon class
    soil_carbon = SoilCarbonPools(
        maom=np.array(maom, dtype=np.float32), lmwc=np.array(lmwc, dtype=np.float32)
    )

    # Mock required values
    mock_t_scalar = mocker.patch(
        "virtual_rainforest.models.soil.carbon.convert_temperature_to_scalar"
    )
    mock_t_scalar.return_value = np.array(temp_scalar, dtype=np.float32)
    mock_m_scalar = mocker.patch(
        "virtual_rainforest.models.soil.carbon.convert_moisture_to_scalar"
    )
    mock_m_scalar.return_value = np.array(moist_scalar, dtype=np.float32)
    mock_equib_maom = mocker.patch(
        "virtual_rainforest.models.soil.carbon.calculate_equilibrium_maom"
    )
    mock_equib_maom.return_value = np.array(equib_maom, dtype=np.float32)
    mock_Q_max = mocker.patch(
        "virtual_rainforest.models.soil.carbon.calculate_max_sorption_capacity"
    )
    mock_Q_max.return_value = np.array(Q_max, dtype=np.float32)

    # Then calculate mineral association rate
    lmwc_to_maom = soil_carbon.mineral_association([], [], [], [], [])

    # Check that expected values are generated
    assert np.allclose(lmwc_to_maom, output_l_to_m)


@pytest.mark.parametrize(
    "binding_coefficients,Q_max,lmwc,output_eqb_maoms",
    [
        (
            [0.16826738, 0.02449064],
            [2.385207e6, 1.980259e6],
            [0.05, 0.02],
            [19900.19, 969.4813],
        ),
        ([0.0128825], [647142.61], [0.1], [832.6088]),
        ([0.05294197], [2.805371e6], [0.005], [742.4128]),
    ],
)
def test_calculate_equilibrium_maom(
    mocker, binding_coefficients, Q_max, lmwc, output_eqb_maoms
):
    """Test that equilibrium maom calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_equilibrium_maom

    # Configure the mock to return specific binding coefficients
    mock_binding = mocker.patch(
        "virtual_rainforest.models.soil.carbon.calculate_binding_coefficient"
    )
    mock_binding.return_value = np.array(binding_coefficients, dtype=np.float32)

    soil_Q_max = np.array(Q_max, dtype=np.float32)
    soil_lmwc = np.array(lmwc, dtype=np.float32)

    equib_maoms = calculate_equilibrium_maom([], soil_Q_max, soil_lmwc)
    assert np.allclose(equib_maoms, np.array(output_eqb_maoms))


@pytest.mark.parametrize(
    "bulk_density,percent_clay,output_capacities",
    [
        ([1350.0, 1800.0], [80.0, 30.0], [2.385207e6, 1.980259e6]),
        ([1000.0], [10.0], [647142.61]),
        ([1500.0], [90.0], [2.805371e6]),
    ],
)
def test_calculate_max_sorption_capacity(bulk_density, percent_clay, output_capacities):
    """Test that max sorption capacity calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_max_sorption_capacity

    soil_BD = np.array(bulk_density, dtype=np.float32)
    soil_clay = np.array(percent_clay, dtype=np.float32)
    max_capacities = calculate_max_sorption_capacity(soil_BD, soil_clay)

    assert np.allclose(max_capacities, np.array(output_capacities))


@pytest.mark.parametrize(
    "pH,output_coefs",
    [
        ([3.0, 7.5], [0.16826738, 0.02449064]),
        ([9.0], [0.0128825]),
        ([5.7], [0.05294197]),
    ],
)
def test_calculate_binding_coefficient(pH, output_coefs):
    """Test that Langmuir binding coefficient calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_binding_coefficient

    soil_pH = np.array(pH, dtype=np.float32)
    binding_coefs = calculate_binding_coefficient(soil_pH)

    assert np.allclose(binding_coefs, np.array(output_coefs))


@pytest.mark.parametrize(
    "temperatures,output_scalars",
    [([35.0, 37.5], [1.27113, 1.27196]), ([40.0], [1.27263]), ([25.0], [1.26344])],
)
def test_convert_temperature_to_scalar(temperatures, output_scalars):
    """Test that scalar_temperature runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_temperature_to_scalar

    soil_temperature = np.array(temperatures, dtype=np.float32)
    temp_scalar = convert_temperature_to_scalar(soil_temperature)

    assert np.allclose(temp_scalar, np.array(output_scalars))


@pytest.mark.parametrize(
    "moistures,output_scalars",
    [([0.5, 0.7], [0.750035, 0.947787]), ([0.6], [0.880671]), ([0.2], [0.167814])],
)
def test_convert_moisture_to_scalar(moistures, output_scalars):
    """Test that scalar_moisture runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_moisture_to_scalar

    soil_moisture = np.array(moistures, dtype=np.float32)
    moist_scalar = convert_moisture_to_scalar(soil_moisture)

    assert np.allclose(moist_scalar, np.array(output_scalars))
