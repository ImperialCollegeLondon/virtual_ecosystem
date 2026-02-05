"""Tests the hydrology.model_config module."""

import pytest
from pydantic import ValidationError


@pytest.mark.parametrize(
    argnames="args",
    argvalues=[
        pytest.param(
            dict(initial_soil_moisture=-0.5, initial_groundwater_saturation=0.9),
            id="soil moisture out of bounds",
        ),
        pytest.param(
            dict(
                initial_soil_moisture=[50, 30, 20, 20],
                initial_groundwater_saturation=0.9,
            ),
            id="soil moisture not numeric",
        ),
        pytest.param(
            dict(initial_soil_moisture=0.5, initial_groundwater_saturation=1.9),
            id="grnd sat out of bounds",
        ),
        pytest.param(
            dict(
                initial_soil_moisture=0.5,
                initial_groundwater_saturation=0.9,
                constants=dict(soilm_cap=0.7),
            ),
            id="unknown constant",
        ),
    ],
)
def test_HydrologyConfiguration(args):
    """Testing validation.

    This is basically checking pydantic works, but these test cases were used with the
    old configuration system, so retained for completeness.
    """
    from virtual_ecosystem.models.hydrology.model_config import HydrologyConfiguration

    with pytest.raises(ValidationError):
        HydrologyConfiguration(**args)
