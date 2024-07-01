"""Collection of fixtures to assist the testing of the soil model."""

import pytest

from virtual_ecosystem.models.soil.env_factors import EnvironmentalEffectFactors


@pytest.fixture
def fixture_soil_config():
    """Create a soil config with faster update interval."""
    from virtual_ecosystem.core.config import Config

    return Config(
        cfg_strings="[core]\n[core.timing]\nupdate_interval = '12 hours'\n[soil]\n"
    )


@pytest.fixture
def fixture_soil_core_components(fixture_soil_config):
    """Create a core components from the fixture_soil_config."""
    from virtual_ecosystem.core.core_components import CoreComponents

    return CoreComponents(fixture_soil_config)


@pytest.fixture
def fixture_soil_model(
    dummy_carbon_data, fixture_soil_config, fixture_soil_core_components
):
    """Create a soil model fixture based on the dummy carbon data."""
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    return SoilModel.from_config(
        data=dummy_carbon_data,
        core_components=fixture_soil_core_components,
        config=fixture_soil_config,
    )


@pytest.fixture
def environmental_factors(dummy_carbon_data, top_soil_layer_index):
    """Environmental factors based on dummy carbon data."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_clay_impact_on_enzyme_saturation,
        calculate_pH_suitability,
        calculate_water_potential_impact_on_microbes,
    )

    soil_constants = SoilConsts()

    water_factors = calculate_water_potential_impact_on_microbes(
        water_potential=dummy_carbon_data["matric_potential"][
            top_soil_layer_index
        ].to_numpy(),
        water_potential_halt=soil_constants.soil_microbe_water_potential_halt,
        water_potential_opt=soil_constants.soil_microbe_water_potential_optimum,
        response_curvature=soil_constants.microbial_water_response_curvature,
    )

    pH_factors = calculate_pH_suitability(
        soil_pH=dummy_carbon_data["pH"].to_numpy(),
        maximum_pH=soil_constants.max_pH_microbes,
        minimum_pH=soil_constants.min_pH_microbes,
        lower_optimum_pH=soil_constants.lowest_optimal_pH_microbes,
        upper_optimum_pH=soil_constants.highest_optimal_pH_microbes,
    )

    clay_saturation_factors = calculate_clay_impact_on_enzyme_saturation(
        clay_fraction=dummy_carbon_data["clay_fraction"].to_numpy(),
        base_protection=soil_constants.base_soil_protection,
        protection_with_clay=soil_constants.soil_protection_with_clay,
    )

    return EnvironmentalEffectFactors(
        water=water_factors, pH=pH_factors, clay_saturation=clay_saturation_factors
    )
