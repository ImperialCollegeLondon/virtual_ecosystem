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


def test_calculate_pH_suitability():
    """Test that calculation of pH suitability is correct."""
    from virtual_rainforest.models.soil.env_factors import calculate_pH_suitability

    pH_values = np.array([3.0, 7.5, 9.0, 5.7, 2.0, 11.5])
    expected_inhib = [0.25, 1.0, 0.428571428, 1.0, 0.0, 0.0]

    actual_inhib = calculate_pH_suitability(
        soil_pH=pH_values,
        maximum_pH=SoilConsts.max_pH_microbes,
        minimum_pH=SoilConsts.min_pH_microbes,
        lower_optimum_pH=SoilConsts.lowest_optimal_pH_microbes,
        upper_optimum_pH=SoilConsts.highest_optimal_pH_microbes,
    )

    assert np.allclose(expected_inhib, actual_inhib)


@pytest.mark.parametrize(
    argnames=["params"],
    argvalues=[
        pytest.param(
            {
                "maximum_pH": 7.0,
                "minimum_pH": 2.5,
                "lower_optimum_pH": 4.5,
                "upper_optimum_pH": 7.5,
            },
            id="maximum_pH too low",
        ),
        pytest.param(
            {
                "maximum_pH": 11.0,
                "minimum_pH": 2.5,
                "lower_optimum_pH": 1.5,
                "upper_optimum_pH": 7.5,
            },
            id="lower_optimum_pH too low",
        ),
        pytest.param(
            {
                "maximum_pH": 11.0,
                "minimum_pH": 2.5,
                "lower_optimum_pH": 4.5,
                "upper_optimum_pH": 3.5,
            },
            id="upper_optimum_pH too low",
        ),
    ],
)
def test_calculate_pH_suitability_errors(params):
    """Test that calculation of pH suitability generates errors if constants are bad."""
    from virtual_rainforest.models.soil.env_factors import calculate_pH_suitability

    pH_values = np.array([3.0, 7.5, 9.0, 5.7, 2.0, 11.5])

    with pytest.raises(ValueError):
        calculate_pH_suitability(soil_pH=pH_values, **params)


def test_calculate_clay_impact_on_enzyme_saturation(dummy_carbon_data):
    """Test calculation of the effect of soil clay fraction on saturation constants."""
    from virtual_rainforest.models.soil.env_factors import (
        calculate_clay_impact_on_enzyme_saturation,
    )

    expected_factor = [1.782, 1.102, 0.83, 1.918]

    actual_factor = calculate_clay_impact_on_enzyme_saturation(
        clay_fraction=dummy_carbon_data["clay_fraction"],
        base_protection=SoilConsts.base_soil_protection,
        protection_with_clay=SoilConsts.soil_protection_with_clay,
    )

    assert np.allclose(expected_factor, actual_factor)


def test_calculate_clay_impact_on_necromass_decay(dummy_carbon_data):
    """Test calculation of the effect of soil clay fraction on necromass decay."""
    from virtual_rainforest.models.soil.env_factors import (
        calculate_clay_impact_on_necromass_decay,
    )

    expected_factor = [0.52729242, 0.78662786, 0.92311634, 0.48675225]

    actual_factor = calculate_clay_impact_on_necromass_decay(
        clay_fraction=dummy_carbon_data["clay_fraction"],
        decay_exponent=SoilConsts.clay_necromass_decay_exponent,
    )

    assert np.allclose(expected_factor, actual_factor)
