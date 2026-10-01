"""Test module for litter.env_factors.py."""

import numpy as np
import pytest


def test_calculate_temperature_effect_on_litter_decomp(
    dummy_litter_data, fixture_core_components, fixture_litter_constants
):
    """Test that temperature effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_temperature_effect_on_litter_decomp,
    )

    expected_factor = [0.2732009, 0.2732009, 0.2732009, 0.2732009]

    actual_factor = calculate_temperature_effect_on_litter_decomp(
        dummy_litter_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        reference_temp=fixture_litter_constants.litter_decomp_reference_temp,
        offset_temp=fixture_litter_constants.litter_decomp_offset_temp,
        temp_response=fixture_litter_constants.litter_decomp_temp_response,
    )

    assert np.allclose(actual_factor, expected_factor)


@pytest.mark.parametrize(
    "increased_depth,variable,expected_average",
    [
        pytest.param(
            True,
            "soil_temperature",
            [19.833333, 19.566667, 19.566667, 19.2],
            id="increased depth, temperature",
        ),
        pytest.param(
            False,
            "soil_temperature",
            [20.0, 20.0, 20.0, 20.0],
            id="normal depth, temperature",
        ),
        pytest.param(
            True,
            "matric_potential",
            [-10.333333, -26.5, -107.666667, -118.033333],
            id="increased depth, matric potential",
        ),
        pytest.param(
            False,
            "matric_potential",
            [-10.0, -25.0, -100.0, -100.0],
            id="normal depth, matric potential",
        ),
    ],
)
def test_average_abiotic_environment_over_microbially_active_layers(
    dummy_litter_data,
    fixture_core_components,
    increased_depth,
    variable,
    expected_average,
):
    """Check averaging of temperatures over soil layers works correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        average_abiotic_environment_over_microbially_active_layers,
    )

    if increased_depth:
        fixture_core_components.layer_structure.soil_layer_active_thickness = np.array(
            [0.5, 0.25]
        )
        fixture_core_components.layer_structure.microbial_simulation_depth = 0.75

    actual_average = average_abiotic_environment_over_microbially_active_layers(
        environmental_variable=dummy_litter_data[variable],
        layer_structure=fixture_core_components.layer_structure,
    )

    assert np.allclose(actual_average, expected_average)


@pytest.mark.parametrize(
    "increased_depth,expected_factors",
    [
        pytest.param(
            True,
            {
                "temp_above": [0.1878681, 0.1878681, 0.1878681, 0.1878681],
                "temp_below": [0.2691235, 0.2626726, 0.2626726, 0.2539490],
                "water": [0.9958835, 0.8776531, 0.7016582, 0.6901177],
            },
            id="increased depth",
        ),
        pytest.param(
            False,
            {
                "temp_above": [0.1878681, 0.1878681, 0.1878681, 0.1878681],
                "temp_below": [0.2732009, 0.2732009, 0.2732009, 0.2732009],
                "water": [1.0, 0.884968239, 0.710931904, 0.710931904],
            },
            id="normal depth",
        ),
    ],
)
def test_calculate_environmental_factors(
    dummy_litter_data,
    fixture_core_components,
    fixture_litter_constants,
    increased_depth,
    expected_factors,
):
    """Check that the calculation of the relevant environmental factors is correct."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_environmental_factors,
    )

    if increased_depth:
        fixture_core_components.layer_structure.soil_layer_active_thickness = np.array(
            [0.5, 0.25]
        )
        fixture_core_components.layer_structure.microbial_simulation_depth = 0.75

    actual_factors = calculate_environmental_factors(
        air_temperatures=dummy_litter_data["air_temperature"],
        soil_temperatures=dummy_litter_data["soil_temperature"],
        water_potentials=dummy_litter_data["matric_potential"],
        layer_structure=fixture_core_components.layer_structure,
        constants=fixture_litter_constants,
    )

    assert set(expected_factors.keys()) == set(actual_factors.keys())

    for key in actual_factors.keys():
        assert np.allclose(actual_factors[key], expected_factors[key])
