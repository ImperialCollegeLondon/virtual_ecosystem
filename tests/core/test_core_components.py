"""Check that the core components system works as expected."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


def test_core_components():
    """Simple test of core component generation."""
    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.core_components import CoreComponents

    cfg = Config(cfg_strings="[core]")

    core_components = CoreComponents(cfg)

    assert core_components.update_interval == 1
    core_components.layer_structure


@pytest.mark.parametrize(
    argnames="config_string, raises, expected_values, expected_log",
    argvalues=[
        pytest.param(
            "[core]",
            does_not_raise(),
            (
                10,
                [-0.25, -1.0],
                2.0,
                0.1,
                1.5,
                (
                    "above",
                    "canopy",
                    "canopy",
                    "canopy",
                    "canopy",
                    "canopy",
                    "canopy",
                    "canopy",
                    "canopy",
                    "canopy",
                    "canopy",
                    "subcanopy",
                    "surface",
                    "soil",
                    "soil",
                ),
            ),
            ((INFO, "Layer structure built from model configuration"),),
            id="defaults",
        ),
        pytest.param(
            """[core.layers]
            soil_layers=[-0.1, -0.5, -0.9]
            canopy_layers=3
            above_canopy_height_offset=1.5
            surface_layer_height=0.2
            subcanopy_layer_height=1.2
            """,
            does_not_raise(),
            (
                3,
                [-0.1, -0.5, -0.9],
                1.5,
                0.2,
                1.2,
                (
                    "above",
                    "canopy",
                    "canopy",
                    "canopy",
                    "subcanopy",
                    "surface",
                    "soil",
                    "soil",
                    "soil",
                ),
            ),
            ((INFO, "Layer structure built from model configuration"),),
            id="alternative",
        ),
        pytest.param(
            """[core.layers]
            soil_layers=[0.1, -0.5, -0.9]
            canopy_layers=9
            above_canopy_height_offset=1.5
            surface_layer_height=0.2
            subcanopy_layer_height=1.2
            """,
            pytest.raises(ConfigurationError),
            None,
            ((ERROR, "Soil layer depths must be strictly decreasing and negative."),),
            id="bad_soil",
        ),
    ],
)
def test_layer_structure(caplog, config_string, raises, expected_values, expected_log):
    """Test the creation and error handling of LayerStructure."""
    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.core_components import LayerStructure

    cfg = Config(cfg_strings=config_string)

    with raises:
        layer_structure = LayerStructure(cfg)

    log_check(caplog=caplog, expected_log=expected_log, subset=slice(-1, None, None))

    if isinstance(raises, does_not_raise):
        assert layer_structure.canopy_layers == expected_values[0]
        assert layer_structure.soil_layers == expected_values[1]
        assert layer_structure.above_canopy_height_offset == expected_values[2]
        assert layer_structure.surface_layer_height == expected_values[3]
        assert layer_structure.subcanopy_layer_height == expected_values[4]
        assert layer_structure.layer_roles == expected_values[5]
