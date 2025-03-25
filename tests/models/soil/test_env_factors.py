"""Test module for soil.env_factors.py.

This module tests the functions which calculate environmental impacts on soil processes.
"""

import numpy as np
import pytest


def test_top_soil_data_extraction(dummy_carbon_data, fixture_core_components):
    """Test that top soil data can be extracted from the data object correctly."""

    top_soil_temps = [35.0, 37.5, 40.0, 25.0]
    top_soil_water_potentials = [-3.0, -10.0, -250.0, -10000.0]

    assert np.allclose(
        dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        top_soil_temps,
    )
    assert np.allclose(
        dummy_carbon_data["matric_potential"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        top_soil_water_potentials,
    )


def test_calculate_environmental_effect_factors(
    dummy_carbon_data, fixture_core_components
):
    """Test that function to calculate all set of environmental factors works."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_environmental_effect_factors,
    )

    expected_water = [1.0, 0.94414168, 0.62176357, 0.07747536]
    expected_pH = [0.25, 1.0, 0.428571428, 1.0]
    expected_clay_sat = [1.782, 1.102, 0.83, 1.918]

    env_factors = calculate_environmental_effect_factors(
        soil_water_potential=dummy_carbon_data["matric_potential"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        pH=dummy_carbon_data["pH"],
        clay_fraction=dummy_carbon_data["clay_fraction"],
        constants=SoilConsts,
    )

    assert np.allclose(env_factors.water, expected_water)
    assert np.allclose(env_factors.pH, expected_pH)
    assert np.allclose(env_factors.clay_saturation, expected_clay_sat)


@pytest.mark.parametrize(
    "activation_energy,expected_factors",
    [
        (30000.0, [2.57140165, 2.82549088, 3.10001987, 1.73624481]),
        (45000.0, [4.1233944, 4.7494232, 5.4581657, 2.2877915]),
        (57000.0, [6.01620802, 7.19578916, 8.58207901, 2.85273102]),
    ],
)
def test_calculate_temperature_effect_on_microbes(
    dummy_carbon_data,
    fixture_core_components,
    activation_energy,
    expected_factors,
    functional_groups,
):
    """Test function to calculate microbial temperature response."""
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_temperature_effect_on_microbes,
    )

    actual_factors = calculate_temperature_effect_on_microbes(
        soil_temperature=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        activation_energy=activation_energy,
        reference_temperature=functional_groups["bacteria"].reference_temperature,
    )

    assert np.allclose(expected_factors, actual_factors)


def test_calculate_water_potential_impact_on_microbes(
    dummy_carbon_data, fixture_core_components
):
    """Test the calculation of the impact of soil water on microbial rates."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_water_potential_impact_on_microbes,
    )

    expected_factor = [1.0, 0.94414168, 0.62176357, 0.07747536]

    actual_factor = calculate_water_potential_impact_on_microbes(
        water_potential=dummy_carbon_data["matric_potential"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        water_potential_halt=SoilConsts.soil_microbe_water_potential_halt,
        water_potential_opt=SoilConsts.soil_microbe_water_potential_optimum,
        response_curvature=SoilConsts.microbial_water_response_curvature,
    )

    assert np.allclose(actual_factor, expected_factor)


def test_soil_water_potential_too_high(dummy_carbon_data):
    """Test that too high soil water potential results in an error."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_water_potential_impact_on_microbes,
    )

    water_potentials = np.array([-2.0, -10.0, -250.0, -10000.0])

    with pytest.raises(ValueError):
        calculate_water_potential_impact_on_microbes(
            water_potential=water_potentials,
            water_potential_halt=SoilConsts.soil_microbe_water_potential_halt,
            water_potential_opt=SoilConsts.soil_microbe_water_potential_optimum,
            response_curvature=SoilConsts.microbial_water_response_curvature,
        )


def test_calculate_pH_suitability():
    """Test that calculation of pH suitability is correct."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import calculate_pH_suitability

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
    from virtual_ecosystem.models.soil.env_factors import calculate_pH_suitability

    pH_values = np.array([3.0, 7.5, 9.0, 5.7, 2.0, 11.5])

    with pytest.raises(ValueError):
        calculate_pH_suitability(soil_pH=pH_values, **params)


def test_calculate_clay_impact_on_enzyme_saturation(dummy_carbon_data):
    """Test calculation of the effect of soil clay fraction on saturation constants."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_clay_impact_on_enzyme_saturation,
    )

    expected_factor = [1.782, 1.102, 0.83, 1.918]

    actual_factor = calculate_clay_impact_on_enzyme_saturation(
        clay_fraction=dummy_carbon_data["clay_fraction"],
        base_protection=SoilConsts.base_soil_protection,
        protection_with_clay=SoilConsts.soil_protection_with_clay,
    )

    assert np.allclose(expected_factor, actual_factor)


def test_calculate_nitrification_temperature_factor(
    dummy_carbon_data, fixture_core_components
):
    """Test calculation of nitrification temperature factor."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_nitrification_temperature_factor,
    )

    expected_factor = [0.95155852, 0.99855129, 0.97583452, 0.45663041]

    actual_factor = calculate_nitrification_temperature_factor(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        optimum_temp=SoilConsts.nitrification_optimum_temperature,
        max_temp=SoilConsts.nitrification_maximum_temperature,
        thermal_sensitivity=SoilConsts.nitrification_thermal_sensitivity,
    )

    assert np.allclose(expected_factor, actual_factor)


def test_calculate_nitrification_moisture_factor(
    dummy_carbon_data, fixture_core_components
):
    """Test calculation of nitrification moisture factor."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_nitrification_moisture_factor,
    )

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * CoreConsts.soil_moisture_capacity
    )

    expected_factor = [0.9988544, 0.9843887, 0.8066573, 0.5592926]

    actual_factor = calculate_nitrification_moisture_factor(
        effective_saturation=effective_saturation
    )

    assert np.allclose(expected_factor, actual_factor)


def test_calculate_denitrification_temperature_factor(
    dummy_carbon_data, fixture_core_components
):
    """Test calculation of nitrification temperature factor."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_denitrification_temperature_factor,
    )

    expected_factor = [2.0706664, 2.3206989, 2.5837455, 1.2112116]

    actual_factor = calculate_denitrification_temperature_factor(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        factor_at_infinity=SoilConsts.denitrification_infinite_temperature_factor,
        minimum_temp=SoilConsts.denitrification_minimum_temperature,
        thermal_sensitivity=SoilConsts.denitrification_thermal_sensitivity,
    )

    assert np.allclose(expected_factor, actual_factor)


def test_denitrification_temperature_factor_bad_temp(
    dummy_carbon_data, fixture_core_components
):
    """Check denitrification temperature factor handles bad temperature values."""
    from scipy.constants import convert_temperature

    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_denitrification_temperature_factor,
    )

    soil_temp = dummy_carbon_data["soil_temperature"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ]

    # Modify some of the soil temps to be below the minimum
    soil_temp[1] = convert_temperature(
        SoilConsts.denitrification_minimum_temperature,
        old_scale="Kelvin",
        new_scale="Celsius",
    )
    soil_temp[3] = convert_temperature(
        SoilConsts.denitrification_minimum_temperature,
        old_scale="Kelvin",
        new_scale="Celsius",
    )

    expected_factor = [2.0706664, 0.0, 2.5837455, 0.0]

    actual_factor = calculate_denitrification_temperature_factor(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        factor_at_infinity=SoilConsts.denitrification_infinite_temperature_factor,
        minimum_temp=SoilConsts.denitrification_minimum_temperature,
        thermal_sensitivity=SoilConsts.denitrification_thermal_sensitivity,
    )

    assert np.allclose(expected_factor, actual_factor)


def test_calculate_symbiotic_nitrogen_fixation_carbon_cost(
    dummy_carbon_data, fixture_core_components
):
    """Test calculation of symbiotic nitrogen fixation cost."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_symbiotic_nitrogen_fixation_carbon_cost,
    )

    expected_cost = [45.8029373, 49.464657, 52.689498, 36.073368]

    actual_cost = calculate_symbiotic_nitrogen_fixation_carbon_cost(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        cost_at_zero_celsius=SoilConsts.nitrogen_fixation_cost_zero_celcius,
        infinite_temp_cost_offset=SoilConsts.nitrogen_fixation_cost_infinite_temp_offset,
        thermal_sensitivity=SoilConsts.nitrogen_fixation_cost_thermal_sensitivity,
        cost_equality_temp=SoilConsts.nitrogen_fixation_cost_equality_temperature,
    )

    assert np.allclose(expected_cost, actual_cost)


def test_calculate_symbiotic_nitrogen_fixation_carbon_cost_bad_temp(
    dummy_carbon_data, fixture_core_components
):
    """Check calculation of nitrogen fixation cost handles bad temperature values."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_symbiotic_nitrogen_fixation_carbon_cost,
    )

    soil_temp = dummy_carbon_data["soil_temperature"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ]

    # Modify some of the soil temps to be below the minimum
    soil_temp[1] = -23.3
    soil_temp[3] = -200.0

    expected_cost = [45.8029373, np.inf, 52.689498, np.inf]

    actual_cost = calculate_symbiotic_nitrogen_fixation_carbon_cost(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        cost_at_zero_celsius=SoilConsts.nitrogen_fixation_cost_zero_celcius,
        infinite_temp_cost_offset=SoilConsts.nitrogen_fixation_cost_infinite_temp_offset,
        thermal_sensitivity=SoilConsts.nitrogen_fixation_cost_thermal_sensitivity,
        cost_equality_temp=SoilConsts.nitrogen_fixation_cost_equality_temperature,
    )

    assert np.allclose(expected_cost, actual_cost)


def test_calculate_leaching_rate(dummy_carbon_data, fixture_core_components):
    """Test calculation of solute leaching rates."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import calculate_leaching_rate

    expected_rate = [1.07473723e-6, 2.53952130e-6, 9.91551977e-5, 5.25567712e-5]
    vertical_flow_per_day = np.array([0.1, 0.5, 2.5, 15.9])

    actual_rate = calculate_leaching_rate(
        solute_density=dummy_carbon_data["soil_c_pool_lmwc"],
        vertical_flow_rate=vertical_flow_per_day,
        soil_moisture=dummy_carbon_data["soil_moisture"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        solubility_coefficient=SoilConsts.solubility_coefficient_lmwc,
    )

    assert np.allclose(expected_rate, actual_rate)


@pytest.mark.parametrize(
    "increased_depth,expected_soil_moisture",
    [
        pytest.param(
            True,
            [265.73973825, 294.34301675, 186.715737, 101.65406175],
            id="increased depth",
        ),
        pytest.param(
            False,
            [116.307750625, 98.443665875, 63.0328985, 37.815975875],
            id="normal depth",
        ),
    ],
)
def test_find_total_soil_moisture_for_microbially_active_depth(
    dummy_carbon_data, fixture_core_components, increased_depth, expected_soil_moisture
):
    """Test that finding the total soil moisture works as expected."""
    from virtual_ecosystem.models.soil.env_factors import (
        find_total_soil_moisture_for_microbially_active_depth,
    )

    if increased_depth:
        fixture_core_components.layer_structure.soil_layer_active_thickness = np.array(
            [0.5, 0.25]
        )
        fixture_core_components.layer_structure.max_depth_of_microbial_activity = 0.75

    actual_soil_moisture = find_total_soil_moisture_for_microbially_active_depth(
        soil_moistures=dummy_carbon_data["soil_moisture"],
        layer_structure=fixture_core_components.layer_structure,
    )

    assert np.allclose(actual_soil_moisture, expected_soil_moisture)
