"""Test module for soil.env_factors.py.

This module tests the functions which calculate environmental impacts on soil processes.
"""

import numpy as np
import pytest


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


def test_calculate_environmental_effect_factors(
    dummy_carbon_data, top_soil_layer_index
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
            top_soil_layer_index
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
        (30000.0, [2.57153601, 2.82565326, 3.10021393, 1.73629781]),
        (45000.0, [4.12371761, 4.74983258, 5.45867825, 2.28789625]),
        (57000.0, [6.01680536, 7.19657491, 8.58309980, 2.85289648]),
    ],
)
def calculate_temperature_effect_on_microbes(
    dummy_carbon_data, top_soil_layer_index, activation_energy, expected_factors
):
    """Test function to calculate microbial temperature response."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_temperature_effect_on_microbes,
    )

    actual_factors = calculate_temperature_effect_on_microbes(
        soil_temperature=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        activation_energy=activation_energy,
        reference_temperature=SoilConsts.arrhenius_reference_temp,
        gas_constant=SoilConsts.universal_gas_constant,
    )

    assert np.allclose(expected_factors, actual_factors)


def test_calculate_water_potential_impact_on_microbes(
    dummy_carbon_data, top_soil_layer_index
):
    """Test the calculation of the impact of soil water on microbial rates."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_water_potential_impact_on_microbes,
    )

    expected_factor = [1.0, 0.94414168, 0.62176357, 0.07747536]

    actual_factor = calculate_water_potential_impact_on_microbes(
        water_potential=dummy_carbon_data["matric_potential"][top_soil_layer_index],
        water_potential_halt=SoilConsts.soil_microbe_water_potential_halt,
        water_potential_opt=SoilConsts.soil_microbe_water_potential_optimum,
        response_curvature=SoilConsts.microbial_water_response_curvature,
    )

    assert np.allclose(actual_factor, expected_factor)


def test_soil_water_potential_too_high(dummy_carbon_data, top_soil_layer_index):
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


def test_calculate_leaching_rate(dummy_carbon_data, top_soil_layer_index):
    """Test calculation of solute leaching rates."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import calculate_leaching_rate

    expected_rate = [1.07473723e-6, 2.53952130e-6, 9.91551977e-5, 5.25567712e-5]
    vertical_flow_per_day = np.array([0.1, 0.5, 2.5, 15.9])

    actual_rate = calculate_leaching_rate(
        solute_density=dummy_carbon_data["soil_c_pool_lmwc"],
        vertical_flow_rate=vertical_flow_per_day,
        soil_moisture=dummy_carbon_data["soil_moisture"][top_soil_layer_index],
        solubility_coefficient=SoilConsts.solubility_coefficient_lmwc,
    )

    assert np.allclose(expected_rate, actual_rate)
