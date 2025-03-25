"""Test module for litter.env_factors.py."""

import numpy as np
import pytest

from virtual_ecosystem.models.litter.constants import LitterConsts


def test_calculate_temperature_effect_on_litter_decomp(
    dummy_litter_data, fixture_core_components
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
        reference_temp=LitterConsts.litter_decomp_reference_temp,
        offset_temp=LitterConsts.litter_decomp_offset_temp,
        temp_response=LitterConsts.litter_decomp_temp_response,
    )

    assert np.allclose(actual_factor, expected_factor)


def test_calculate_soil_water_effect_on_litter_decomp(
    dummy_litter_data, fixture_core_components
):
    """Test that soil moisture effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_soil_water_effect_on_litter_decomp,
    )

    expected_factor = [1.0, 0.88496823, 0.71093190, 0.71093190]

    actual_factor = calculate_soil_water_effect_on_litter_decomp(
        water_potential=dummy_litter_data["matric_potential"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        water_potential_halt=LitterConsts.litter_decay_water_potential_halt,
        water_potential_opt=LitterConsts.litter_decay_water_potential_optimum,
        moisture_response_curvature=LitterConsts.moisture_response_curvature,
    )

    assert np.allclose(actual_factor, expected_factor)


@pytest.mark.parametrize(
    "increased_depth,expected_av_temps",
    [
        pytest.param(
            True,
            [18.6319817, 18.498648, 18.498648, 18.315315],
            id="increased depth",
        ),
        pytest.param(
            False,
            [18.0729725, 18.0729725, 18.0729725, 18.0729725],
            id="normal depth",
        ),
    ],
)
def test_average_temperature_over_microbially_active_layers(
    dummy_litter_data, fixture_core_components, increased_depth, expected_av_temps
):
    """Check averaging of temperatures over soil layers works correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        average_temperature_over_microbially_active_layers,
    )

    if increased_depth:
        fixture_core_components.layer_structure.soil_layer_active_thickness = np.array(
            [0.5, 0.25]
        )
        fixture_core_components.layer_structure.max_depth_of_microbial_activity = 0.75

    actual_av_temps = average_temperature_over_microbially_active_layers(
        soil_temperatures=dummy_litter_data["soil_temperature"],
        surface_temperature=dummy_litter_data["air_temperature"][
            fixture_core_components.layer_structure.index_surface
        ].to_numpy(),
        layer_structure=fixture_core_components.layer_structure,
    )

    assert np.allclose(actual_av_temps, expected_av_temps)


@pytest.mark.parametrize(
    "increased_depth,expected_water_pots",
    [
        pytest.param(
            True,
            [-10.1667, -25.750, -103.8333, -109.0167],
            id="increased depth",
        ),
        pytest.param(
            False,
            [-10.0, -25.0, -100.0, -100.0],
            id="normal depth",
        ),
    ],
)
def test_average_water_potential_over_microbially_active_layers(
    dummy_litter_data, fixture_core_components, increased_depth, expected_water_pots
):
    """Check averaging of water potentials over soil layers works correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        average_water_potential_over_microbially_active_layers,
    )

    if increased_depth:
        fixture_core_components.layer_structure.soil_layer_active_thickness = np.array(
            [0.5, 0.25]
        )
        fixture_core_components.layer_structure.max_depth_of_microbial_activity = 0.75

    actual_water_pots = average_water_potential_over_microbially_active_layers(
        water_potentials=dummy_litter_data["matric_potential"],
        layer_structure=fixture_core_components.layer_structure,
    )

    assert np.allclose(actual_water_pots, expected_water_pots)


@pytest.mark.parametrize(
    "increased_depth,expected_factors",
    [
        pytest.param(
            True,
            {
                "temp_above": [0.1878681, 0.1878681, 0.1878681, 0.1878681],
                "temp_below": [0.2407699, 0.2377353, 0.2377353, 0.2335993],
                "water": [0.9979245, 0.8812574, 0.7062095, 0.7000939],
            },
            id="increased depth",
        ),
        pytest.param(
            False,
            {
                "temp_above": [0.1878681, 0.1878681, 0.1878681, 0.1878681],
                "temp_below": [0.2281971, 0.2281971, 0.2281971, 0.2281971],
                "water": [1.0, 0.88496823, 0.71093190, 0.71093190],
            },
            id="normal depth",
        ),
    ],
)
def test_calculate_environmental_factors(
    dummy_litter_data, fixture_core_components, increased_depth, expected_factors
):
    """Check that the calculation of the relevant environmental factors is correct."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_environmental_factors,
    )

    if increased_depth:
        fixture_core_components.layer_structure.soil_layer_active_thickness = np.array(
            [0.5, 0.25]
        )
        fixture_core_components.layer_structure.max_depth_of_microbial_activity = 0.75

    actual_factors = calculate_environmental_factors(
        air_temperatures=dummy_litter_data["air_temperature"],
        soil_temperatures=dummy_litter_data["soil_temperature"],
        water_potentials=dummy_litter_data["matric_potential"],
        layer_structure=fixture_core_components.layer_structure,
        constants=LitterConsts,
    )

    assert set(expected_factors.keys()) == set(actual_factors.keys())

    for key in actual_factors.keys():
        assert np.allclose(actual_factors[key], expected_factors[key])
