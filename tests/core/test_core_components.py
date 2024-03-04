"""Check that the core components system works as expected."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import numpy as np
import pytest
from pint import Quantity

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError

DEFAULT_CANOPY = [
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
]

ALTERNATE_CANOPY = [
    "above",
    "canopy",
    "canopy",
    "canopy",
    "subcanopy",
    "surface",
    "soil",
    "soil",
    "soil",
]


@pytest.mark.parametrize(
    argnames="config, expected_layers, expected_timing, expected_constants",
    argvalues=[
        pytest.param(
            "[core]",
            {
                "canopy_layers": 10,
                "soil_layers": [-0.25, -1.0],
                "above_canopy_height_offset": 2.0,
                "surface_layer_height": 0.1,
                "subcanopy_layer_height": 1.5,
                "layer_roles": DEFAULT_CANOPY,
                "n_layers": 15,
            },
            {
                "start_time": np.datetime64("2013-01-01"),
                "run_length": np.timedelta64(63115200, "s"),
                "run_length_quantity": Quantity(63115200.0, "second"),
                "update_interval": np.timedelta64(2629800, "s"),
                "update_interval_quantity": Quantity(2629800.0, "second"),
                "end_time": np.datetime64("2015-01-01T12:00:00"),
                "reconciled_run_length": np.timedelta64(63115200, "s"),
            },
            {"depth_of_active_soil_layer": 0.25},
            id="defaults",
        ),
        pytest.param(
            """[core.layers]
            soil_layers=[-0.1, -0.5, -0.9]
            canopy_layers=3
            above_canopy_height_offset=1.5
            surface_layer_height=0.2
            subcanopy_layer_height=1.2
            [core.timing]
            start_date = "2020-01-01"
            update_interval = "10 minutes"
            run_length = "30 years"
            [core.constants.CoreConsts]
            depth_of_active_soil_layer = 2
            """,
            {
                "canopy_layers": 3,
                "soil_layers": [-0.1, -0.5, -0.9],
                "above_canopy_height_offset": 1.5,
                "surface_layer_height": 0.2,
                "subcanopy_layer_height": 1.2,
                "layer_roles": ALTERNATE_CANOPY,
                "n_layers": 9,
            },
            {
                "start_time": np.datetime64("2020-01-01"),
                "run_length": np.timedelta64(946728000, "s"),
                "run_length_quantity": Quantity(946728000.0, "second"),
                "update_interval": np.timedelta64(10 * 60, "s"),
                "update_interval_quantity": Quantity(10 * 60, "second"),
                "end_time": np.datetime64("2049-12-31T12:00:00"),
                "reconciled_run_length": np.timedelta64(946728000, "s"),
            },
            {"depth_of_active_soil_layer": 2},
            id="alternative config",
        ),
    ],
)
def test_CoreComponents(config, expected_layers, expected_timing, expected_constants):
    """Simple test of core component generation."""
    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.core_components import CoreComponents

    cfg = Config(cfg_strings=config)
    core_components = CoreComponents(cfg)

    core_constants = {
        "placeholder": 123.4,
        "standard_pressure": 101.325,
        "standard_mole": 44.642,
        "molar_heat_capacity_air": 29.19,
        "gravity": 6.6743e-11,
        "stefan_boltzmann_constant": 5.670374419e-08,
        "von_karmans_constant": 0.4,
        "depth_of_active_soil_layer": 0.25,
        "meters_to_mm": 1000.0,
        "molecular_weight_air": 28.96,
        "gas_constant_water_vapour": 461.51,
        "seconds_to_day": 86400.0,
        "characteristic_dimension_leaf": 0.01,
    }
    core_constants.update(expected_constants)

    assert core_components.layer_structure.__dict__ == expected_layers
    assert core_components.model_timing.__dict__ == expected_timing
    assert core_components.core_constants.__dict__ == core_constants


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
                DEFAULT_CANOPY,
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
                ALTERNATE_CANOPY,
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
def test_LayerStructure(caplog, config_string, raises, expected_values, expected_log):
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


@pytest.mark.parametrize(
    "config,output,raises,expected_log_entries",
    [
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "10 minutes"
            run_length = "30 years"
            """,
            {
                "start_time": np.datetime64("2020-01-01"),
                "update_interval": np.timedelta64(10, "m"),
                "update_interval_as_quantity": Quantity("10 minutes"),
                "end_time": np.datetime64("2049-12-31T12:00"),
            },
            does_not_raise(),
            (
                (
                    INFO,
                    "Timing details built from model configuration: "
                    "start - 2020-01-01, end - 2049-12-31T12:00:00, "
                    "run length - 946728000 seconds",
                ),
            ),
            id="timing correct",
        ),
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "10 metres"
            run_length = "30 years"
            """,
            None,
            pytest.raises(ConfigurationError),
            ((ERROR, "Invalid units for core.timing.update_interval: "),),
            id="bad update dimension",
        ),
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "10 epochs"
            run_length = "30 years"
            """,
            None,
            pytest.raises(ConfigurationError),
            ((ERROR, "Invalid units for core.timing.update_interval: "),),
            id="unknown update unit",
        ),
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "10 minutes"
            run_length = "1 minute"
            """,
            {},  # Fails so no output to check
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Model run length (1 minute) expires before first "
                    "update (10 minutes)",
                ),
            ),
            id="run length too short",
        ),
    ],
)
def test_ModelTiming(caplog, config, output, raises, expected_log_entries):
    """Test that function to extract main loop timing works as intended."""
    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.core_components import ModelTiming

    config_obj = Config(cfg_strings=config)
    caplog.clear()

    with raises:
        model_timing = ModelTiming(config=config_obj)

        assert model_timing.end_time == output["end_time"]
        assert model_timing.update_interval == output["update_interval"]
        assert model_timing.start_time == output["start_time"]
        assert (
            model_timing.update_interval_quantity
            == output["update_interval_as_quantity"]
        )

    log_check(caplog=caplog, expected_log=expected_log_entries)


@pytest.mark.parametrize(
    argnames="value, raises",
    argvalues=[
        (1, does_not_raise()),
        (1.23, does_not_raise()),
        (np.infty, pytest.raises(ConfigurationError)),
        (np.nan, pytest.raises(ConfigurationError)),
        (-9, pytest.raises(ConfigurationError)),
        (-9.5, pytest.raises(ConfigurationError)),
        ("h", pytest.raises(ConfigurationError)),
        ([1], pytest.raises(ConfigurationError)),
    ],
)
def test__validate_positive_finite_numeric(value, raises):
    """Testing private validation function."""
    from virtual_rainforest.core.core_components import (
        _validate_positive_finite_numeric,
    )

    with raises:
        _validate_positive_finite_numeric(value, "label")


@pytest.mark.parametrize(
    argnames="value, raises",
    argvalues=[
        (10, does_not_raise()),
        (1.23, pytest.raises(ConfigurationError)),
        (np.infty, pytest.raises(ConfigurationError)),
        (np.nan, pytest.raises(ConfigurationError)),
        (-9, pytest.raises(ConfigurationError)),
        (-9.5, pytest.raises(ConfigurationError)),
        ("h", pytest.raises(ConfigurationError)),
        ([1], pytest.raises(ConfigurationError)),
    ],
)
def test__validate_positive_integer(value, raises):
    """Testing private validation function."""
    from virtual_rainforest.core.core_components import _validate_positive_integer

    with raises:
        _validate_positive_integer(value)


@pytest.mark.parametrize(
    argnames="value, raises",
    argvalues=[
        (1, pytest.raises(ConfigurationError)),
        ("h", pytest.raises(ConfigurationError)),
        ([1], pytest.raises(ConfigurationError)),
        ([-1], does_not_raise()),
        ([-1, -0.5], pytest.raises(ConfigurationError)),
        ([-0.5, -1.5], does_not_raise()),
    ],
)
def test__validate_soil_layers(value, raises):
    """Testing private validation function."""
    from virtual_rainforest.core.core_components import _validate_soil_layers

    with raises:
        _validate_soil_layers(value)
