"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

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
                    ERROR,
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
                    ERROR,
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


@pytest.mark.parametrize(
    argnames=[
        "maom",
        "lmwc",
        "pH",
        "bulk_density",
        "moistures",
        "temperatures",
        "percent_clay",
        "dt",
        "end_maom",
        "end_lmwc",
    ],
    argvalues=[
        (
            [2.5, 1.7],
            [0.05, 0.02],
            [3.0, 7.5],
            [1350.0, 1800.0],
            [0.5, 0.7],
            [35.0, 37.5],
            [80.0, 30.0],
            [2.0 / 24.0, 1.0 / 24.0],
            [2.500033, 1.70000049],
            [0.0499668, 0.0199995],
        ),
        (
            [4.5],
            [0.1],
            [9.0],
            [1000.0],
            [0.6],
            [40.0],
            [10.0],
            [0.5],
            [4.500071],
            [0.0999282],
        ),
        (
            [0.5],
            [0.005],
            [5.7],
            [1500.0],
            [0.2],
            [25.0],
            [90.0],
            [1.0 / 30.0],
            [0.500000],
            [0.00499999],
        ),
    ],
)
def test_update_pools(
    maom,
    lmwc,
    pH,
    bulk_density,
    moistures,
    temperatures,
    percent_clay,
    dt,
    end_maom,
    end_lmwc,
):
    """Test that update_pools runs and generates the correct values."""

    # Initialise soil carbon class
    soil_carbon = SoilCarbonPools(
        maom=np.array(maom, dtype=np.float32), lmwc=np.array(lmwc, dtype=np.float32)
    )

    soil_pH = np.array(pH, dtype=np.float32)
    soil_BD = np.array(bulk_density, dtype=np.float32)
    soil_moisture = np.array(moistures, dtype=np.float32)
    soil_temp = np.array(temperatures, dtype=np.float32)
    soil_clay = np.array(percent_clay, dtype=np.float32)

    soil_carbon.update_pools(soil_pH, soil_BD, soil_moisture, soil_temp, soil_clay, dt)

    # Check that pools are correctly incremented
    assert np.allclose(soil_carbon.maom, np.array(end_maom))
    assert np.allclose(soil_carbon.lmwc, np.array(end_lmwc))


@pytest.mark.parametrize(
    "maom,lmwc,pH,bulk_density,moistures,temperatures,percent_clay,output_l_to_m",
    [
        (
            [2.5, 1.7],
            [0.05, 0.02],
            [3.0, 7.5],
            [1350.0, 1800.0],
            [0.5, 0.7],
            [35.0, 37.5],
            [80.0, 30.0],
            [0.000397665, 1.178336e-5],
        ),
        ([4.5], [0.1], [9.0], [1000.0], [0.6], [40.0], [10.0], [0.0001434178]),
        ([0.5], [0.005], [5.7], [1500.0], [0.2], [25.0], [90.0], [2.80359e-7]),
    ],
)
def test_mineral_association(
    maom, lmwc, pH, bulk_density, moistures, temperatures, percent_clay, output_l_to_m
):
    """Test that mineral_association runs and generates the correct values."""

    # Initialise soil carbon class
    soil_carbon = SoilCarbonPools(
        maom=np.array(maom, dtype=np.float32), lmwc=np.array(lmwc, dtype=np.float32)
    )

    soil_pH = np.array(pH, dtype=np.float32)
    soil_BD = np.array(bulk_density, dtype=np.float32)
    soil_moisture = np.array(moistures, dtype=np.float32)
    soil_temp = np.array(temperatures, dtype=np.float32)
    soil_clay = np.array(percent_clay, dtype=np.float32)

    # Then calculate mineral association rate
    lmwc_to_maom = soil_carbon.mineral_association(
        soil_pH, soil_BD, soil_moisture, soil_temp, soil_clay
    )

    # Check that expected values are generated
    assert np.allclose(lmwc_to_maom, output_l_to_m)


@pytest.mark.parametrize(
    "pH,Q_max,lmwc,output_eqb_maoms",
    [
        (
            [3.0, 7.5],
            [2.385207e6, 1.980259e6],
            [0.05, 0.02],
            [19900.19, 969.4813],
        ),
        ([9.0], [647142.61], [0.1], [832.6088]),
        ([5.7], [2.805371e6], [0.005], [742.4128]),
    ],
)
def test_calculate_equilibrium_maom(pH, Q_max, lmwc, output_eqb_maoms):
    """Test that equilibrium maom calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_equilibrium_maom

    soil_pH = np.array(pH, dtype=np.float32)
    soil_Q_max = np.array(Q_max, dtype=np.float32)
    soil_lmwc = np.array(lmwc, dtype=np.float32)

    equib_maoms = calculate_equilibrium_maom(soil_pH, soil_Q_max, soil_lmwc)
    assert np.allclose(equib_maoms, np.array(output_eqb_maoms))


@pytest.mark.parametrize(
    "bulk_density,percent_clay,output_capacities,raises,expected_log_entries",
    [
        (
            [1350.0, 1800.0],
            [80.0, 30.0],
            [2.385207e6, 1.980259e6],
            does_not_raise(),
            (),
        ),
        ([1000.0], [10.0], [647142.61], does_not_raise(), ()),
        ([1500.0], [90.0], [2.805371e6], does_not_raise(), ()),
        (
            [1500.0],
            [156.0],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative clay content must be expressed as a percentage!"),),
        ),
        (
            [1500.0],
            [-9.0],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative clay content must be expressed as a percentage!"),),
        ),
    ],
)
def test_calculate_max_sorption_capacity(
    caplog, bulk_density, percent_clay, output_capacities, raises, expected_log_entries
):
    """Test that max sorption capacity calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_max_sorption_capacity

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        soil_BD = np.array(bulk_density, dtype=np.float32)
        soil_clay = np.array(percent_clay, dtype=np.float32)
        max_capacities = calculate_max_sorption_capacity(soil_BD, soil_clay)

        assert np.allclose(max_capacities, np.array(output_capacities))

    log_check(caplog, expected_log_entries)


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
    "moistures,output_scalars,raises,expected_log_entries",
    [
        ([0.5, 0.7], [0.750035, 0.947787], does_not_raise(), ()),
        ([0.6], [0.880671], does_not_raise(), ()),
        ([0.2], [0.167814], does_not_raise(), ()),
        (
            [-0.2],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative water content cannot go below zero or above one!"),),
        ),
        (
            [2.7],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative water content cannot go below zero or above one!"),),
        ),
    ],
)
def test_convert_moisture_to_scalar(
    caplog, moistures, output_scalars, raises, expected_log_entries
):
    """Test that scalar_moisture runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_moisture_to_scalar

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        soil_moisture = np.array(moistures, dtype=np.float32)
        moist_scalar = convert_moisture_to_scalar(soil_moisture)

        assert np.allclose(moist_scalar, np.array(output_scalars))

    log_check(caplog, expected_log_entries)
