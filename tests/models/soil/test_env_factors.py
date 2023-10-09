"""Test module for soil.env_factors.py.

This module tests the functions which calculate environmental impacts on soil processes.
"""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_rainforest.models.soil.constants import SoilConsts


def test_top_soil_data_extraction(dummy_carbon_data, top_soil_layer_index):
    """Test that top soil data can be extracted from the data object correctly."""

    top_soil_temps = [35.0, 37.5, 40.0, 25.0]
    top_soil_water_potentials = [-3.0, -10.0, -250.0, -10000.0]

    assert np.allclose(
        dummy_carbon_data["soil_temperature"][top_soil_layer_index], top_soil_temps
    )
    assert np.allclose(
        dummy_carbon_data["matric_potential"][top_soil_layer_index],
        top_soil_water_potentials,
    )


@pytest.mark.parametrize(
    "activation_energy,expected_factors",
    [
        (30000.0, [2.57153601, 2.82565326, 3.10021393, 1.73629781]),
        (45000.0, [4.12371761, 4.74983258, 5.45867825, 2.28789625]),
        (57000.0, [6.01680536, 7.19657491, 8.58309980, 2.85289648]),
    ],
)
def calculate_temperature_effect_on_microbes(
    dummy_carbon_data, top_soil_layer_index, activation_energy, expected_factors
):
    """Test function to calculate microbial temperature response."""
    from virtual_rainforest.models.soil.env_factors import (
        calculate_temperature_effect_on_microbes,
    )

    actual_factors = calculate_temperature_effect_on_microbes(
        soil_temperature=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        activation_energy=activation_energy,
        reference_temperature=SoilConsts.arrhenius_reference_temp,
        gas_constant=SoilConsts.universal_gas_constant,
    )

    assert np.allclose(expected_factors, actual_factors)


@pytest.mark.parametrize(
    "alternative,output_scalars,raises,expected_log_entries",
    [
        (None, [0.750035, 0.947787, 0.880671, 0.167814], does_not_raise(), ()),
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
    caplog,
    dummy_carbon_data,
    alternative,
    output_scalars,
    raises,
    expected_log_entries,
    top_soil_layer_index,
):
    """Test that scalar_moisture runs and generates the correct value."""
    from virtual_rainforest.models.soil.env_factors import convert_moisture_to_scalar

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        if alternative:
            moist_scalar = convert_moisture_to_scalar(
                np.array(alternative, dtype=np.float32),
                SoilConsts.moisture_scalar_coefficient,
                SoilConsts.moisture_scalar_exponent,
            )
        else:
            moist_scalar = convert_moisture_to_scalar(
                np.array([0.5, 0.7, 0.6, 0.2]),
                SoilConsts.moisture_scalar_coefficient,
                SoilConsts.moisture_scalar_exponent,
            )

        assert np.allclose(moist_scalar, output_scalars)

    log_check(caplog, expected_log_entries)


def test_calculate_water_potential_impact_on_microbes():
    """Test the calculation of the impact of soil water on microbial rates."""
    from virtual_rainforest.models.soil.env_factors import (
        calculate_water_potential_impact_on_microbes,
    )

    water_potentials = np.array([-3.0, -10.0, -250.0, -10000.0])

    expected_factor = [1.0, 0.94414168, 0.62176357, 0.07747536]

    actual_factor = calculate_water_potential_impact_on_microbes(
        water_potential=water_potentials,
        water_potential_halt=SoilConsts.soil_microbe_water_potential_halt,
        water_potential_opt=SoilConsts.soil_microbe_water_potential_optimum,
        moisture_response_curvature=SoilConsts.moisture_response_curvature,
    )

    assert np.allclose(actual_factor, expected_factor)
