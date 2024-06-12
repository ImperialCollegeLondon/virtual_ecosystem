"""Check that the core components system works as expected."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import numpy as np
import pytest
from pint import Quantity
from xarray import DataArray

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError

DEFAULT_CANOPY = np.array(
    [
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
        "surface",
        "soil",
        "soil",
    ]
)

ALTERNATE_CANOPY = np.array(
    [
        "above",
        "canopy",
        "canopy",
        "canopy",
        "surface",
        "soil",
        "soil",
        "soil",
    ]
)


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
                "n_layers": 14,
            },
            {
                "start_time": np.datetime64("2013-01-01"),
                "run_length": np.timedelta64(63115200, "s"),
                "run_length_quantity": Quantity(63115200.0, "second"),
                "update_interval": np.timedelta64(2629800, "s"),
                "update_interval_quantity": Quantity(2629800.0, "second"),
                "end_time": np.datetime64("2015-01-01T12:00:00"),
                "reconciled_run_length": np.timedelta64(63115200, "s"),
                "n_updates": 24,
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
                "n_layers": 8,
            },
            {
                "start_time": np.datetime64("2020-01-01"),
                "run_length": np.timedelta64(946728000, "s"),
                "run_length_quantity": Quantity(946728000.0, "second"),
                "update_interval": np.timedelta64(10 * 60, "s"),
                "update_interval_quantity": Quantity(10 * 60, "second"),
                "end_time": np.datetime64("2049-12-31T12:00:00"),
                "reconciled_run_length": np.timedelta64(946728000, "s"),
                "n_updates": 1577880,
            },
            {"depth_of_active_soil_layer": 2},
            id="alternative config",
        ),
    ],
)
def test_CoreComponents(config, expected_layers, expected_timing, expected_constants):
    """Simple test of core component generation.

    The expected components contain some simple values to check - the component specific
    tests provide more rigourous testing.
    """
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents

    cfg = Config(cfg_strings=config)
    core_components = CoreComponents(cfg)

    for ky, val in expected_layers.items():
        assert getattr(core_components.layer_structure, ky) == expected_layers[ky]

    for ky, val in expected_timing.items():
        assert getattr(core_components.model_timing, ky) == expected_timing[ky]

    for ky, val in expected_constants.items():
        assert getattr(core_components.core_constants, ky) == expected_constants[ky]


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
                DEFAULT_CANOPY,
                {
                    "above": np.array([0]),
                    "canopy": np.arange(1, 11),
                    "surface": np.array([11]),
                    "soil": np.array([12, 13]),
                },
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
            """,
            does_not_raise(),
            (
                3,
                [-0.1, -0.5, -0.9],
                1.5,
                0.2,
                ALTERNATE_CANOPY,
                {
                    "above": np.array([0]),
                    "canopy": np.arange(1, 4),
                    "surface": np.array([4]),
                    "soil": np.array([5, 6, 7]),
                },
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
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import LayerStructure

    cfg = Config(cfg_strings=config_string)

    with raises:
        layer_structure = LayerStructure(cfg, n_cells=9)

    log_check(caplog=caplog, expected_log=expected_log, subset=slice(-1, None, None))

    if isinstance(raises, does_not_raise):
        # Check the main properties
        assert layer_structure.canopy_layers == expected_values[0]
        assert layer_structure.soil_layers == expected_values[1]
        assert layer_structure.above_canopy_height_offset == expected_values[2]
        assert layer_structure.surface_layer_height == expected_values[3]
        assert np.all(np.equal(layer_structure.layer_roles, expected_values[4]))
        assert layer_structure.role_indices.keys() == expected_values[5].keys()
        for ky in layer_structure.role_indices.keys():
            assert np.all(
                np.equal(layer_structure.role_indices[ky], expected_values[5][ky])
            )

        # Check the template data array
        template = layer_structure.get_template()
        assert isinstance(template, DataArray)
        assert template.shape == (layer_structure.n_layers, layer_structure.n_cells)
        assert template.dims == ("layer_roles", "cell_id")
        assert np.all(
            np.equal(template["layer_roles"].to_numpy(), layer_structure.layer_roles)
        )
        assert np.all(
            np.equal(template["cell_id"].to_numpy(), np.arange(layer_structure.n_cells))
        )


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
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import ModelTiming

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
    from virtual_ecosystem.core.core_components import _validate_positive_finite_numeric

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
    from virtual_ecosystem.core.core_components import _validate_positive_integer

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
    from virtual_ecosystem.core.core_components import _validate_soil_layers

    with raises:
        _validate_soil_layers(value)
