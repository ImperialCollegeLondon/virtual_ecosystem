"""Collection of fixtures to assist the testing of the soil model."""

import pytest

from virtual_rainforest.models.soil.constants import SoilConsts


@pytest.fixture
def environmental_factors(dummy_carbon_data, top_soil_layer_index):
    """Environmental factors based on dummy carbon data."""
    from virtual_rainforest.models.soil.env_factors import (
        calculate_clay_impact_on_enzyme_saturation,
        calculate_clay_impact_on_necromass_decay,
        calculate_pH_suitability,
        calculate_water_potential_impact_on_microbes,
    )

    water_factors = calculate_water_potential_impact_on_microbes(
        water_potential=dummy_carbon_data["matric_potential"][
            top_soil_layer_index
        ].to_numpy(),
        water_potential_halt=SoilConsts.soil_microbe_water_potential_halt,
        water_potential_opt=SoilConsts.soil_microbe_water_potential_optimum,
        moisture_response_curvature=SoilConsts.moisture_response_curvature,
    )

    pH_factors = calculate_pH_suitability(
        soil_pH=dummy_carbon_data["pH"].to_numpy(),
        maximum_pH=SoilConsts.max_pH_microbes,
        minimum_pH=SoilConsts.min_pH_microbes,
        lower_optimum_pH=SoilConsts.lowest_optimal_pH_microbes,
        upper_optimum_pH=SoilConsts.highest_optimal_pH_microbes,
    )

    clay_saturation_factors = calculate_clay_impact_on_enzyme_saturation(
        clay_fraction=dummy_carbon_data["clay_fraction"].to_numpy(),
        base_protection=SoilConsts.base_soil_protection,
        protection_with_clay=SoilConsts.soil_protection_with_clay,
    )

    clay_decay_factors = calculate_clay_impact_on_necromass_decay(
        clay_fraction=dummy_carbon_data["clay_fraction"].to_numpy(),
        decay_exponent=SoilConsts.clay_necromass_decay_exponent,
    )

    return {
        "water": water_factors,
        "pH": pH_factors,
        "clay_saturation": clay_saturation_factors,
        "clay_decay": clay_decay_factors,
    }
