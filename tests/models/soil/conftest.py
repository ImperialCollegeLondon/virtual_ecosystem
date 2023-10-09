"""Collection of fixtures to assist the testing of the soil model."""

import numpy as np
import pytest

from virtual_rainforest.models.soil.constants import SoilConsts


@pytest.fixture
def moist_scalars(dummy_carbon_data, top_soil_layer_index):
    """Moisture scalars based on dummy carbon data."""
    from virtual_rainforest.models.soil.env_factors import convert_moisture_to_scalar

    moist_scalars = convert_moisture_to_scalar(
        np.array([0.5, 0.7, 0.6, 0.2]),
        SoilConsts.moisture_scalar_coefficient,
        SoilConsts.moisture_scalar_exponent,
    )

    return moist_scalars


@pytest.fixture
def water_factors(dummy_carbon_data, top_soil_layer_index):
    """Water potential factors based on dummy carbon data."""
    from virtual_rainforest.models.soil.env_factors import (
        calculate_water_potential_impact_on_microbes,
    )

    moist_scalars = calculate_water_potential_impact_on_microbes(
        water_potential=dummy_carbon_data["matric_potential"][top_soil_layer_index],
        water_potential_halt=SoilConsts.soil_microbe_water_potential_halt,
        water_potential_opt=SoilConsts.soil_microbe_water_potential_optimum,
        moisture_response_curvature=SoilConsts.moisture_response_curvature,
    )

    return moist_scalars
