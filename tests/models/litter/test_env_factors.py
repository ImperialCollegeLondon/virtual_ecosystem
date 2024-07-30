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


def test_calculate_soil_water_effect_on_litter_decomp():
    """Test that soil moisture effects on decomposition are calculated correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        calculate_soil_water_effect_on_litter_decomp,
    )

    water_potentials = np.array([-10.0, -25.0, -100.0, -400.0])

    expected_factor = [1.0, 0.88496823, 0.71093190, 0.53689556]

    actual_factor = calculate_soil_water_effect_on_litter_decomp(
        water_potentials,
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
            [19.8333333, 19.5666667, 19.5666667, 19.2],
            id="increased depth",
        ),
        pytest.param(
            False,
            [20.0, 20.0, 20.0, 20.0],
            id="normal depth",
        ),
    ],
)
def test_average_over_microbially_active_layers(
    dummy_litter_data, fixture_core_components, increased_depth, expected_av_temps
):
    """Check averaging of environmental variables over soil layers works correctly."""
    from virtual_ecosystem.models.litter.env_factors import (
        average_over_microbially_active_layers,
    )

    if increased_depth:
        fixture_core_components.layer_structure.soil_layer_active_thickness = np.array(
            [0.5, 0.25]
        )
        fixture_core_components.layer_structure.max_depth_of_microbial_activity = 0.75

    actual_av_temps = average_over_microbially_active_layers(
        environmental_variable=dummy_litter_data["soil_temperature"],
        layer_structure=fixture_core_components.layer_structure,
    )

    assert np.allclose(actual_av_temps, expected_av_temps)
