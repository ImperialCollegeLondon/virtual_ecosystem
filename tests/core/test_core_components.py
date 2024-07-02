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
        "topsoil",
        "subsoil",
    ]
)

ALTERNATE_CANOPY = np.array(
    [
        "above",
        "canopy",
        "canopy",
        "canopy",
        "surface",
        "topsoil",
        "subsoil",
        "subsoil",
    ]
)


@pytest.mark.parametrize(
    argnames="config, expected_layers, expected_timing, expected_constants",
    argvalues=[
        pytest.param(
            "[core]",
            {
                "n_canopy_layers": 10,
                "soil_layer_depths": np.array([-0.25, -1.0]),
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
            {"max_depth_of_microbial_activity": 0.25},
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
            max_depth_of_microbial_activity = 0.8
            """,
            {
                "n_canopy_layers": 3,
                "soil_layer_depths": np.array([-0.1, -0.5, -0.9]),
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
            {"max_depth_of_microbial_activity": 0.8},
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
        # Handle different expected classes
        result = getattr(core_components.layer_structure, ky)
        if isinstance(result, np.ndarray):
            assert np.all(np.equal(result, val))
        else:
            assert result == val

    for ky, val in expected_timing.items():
        assert getattr(core_components.model_timing, ky) == val

    for ky, val in expected_constants.items():
        assert getattr(core_components.core_constants, ky) == val


@pytest.mark.parametrize(
    argnames="config_string, max_active_depth, raises, expected_values, expected_log",
    argvalues=[
        pytest.param(
            "[core]",
            0.25,
            does_not_raise(),
            dict(
                n_canopy_layers=10,
                soil_layer_depths=np.array([-0.25, -1.0]),
                offset_height=2.0,
                surface_height=0.1,
                layer_roles=DEFAULT_CANOPY,
                layer_indices={
                    "above": np.array([0]),
                    "canopy": np.arange(1, 11),
                    "surface": np.array([11]),
                    "topsoil": np.array([12]),
                    "subsoil": np.array([13]),
                    "all_soil": np.array([12, 13]),
                    "active_soil": np.array([12]),
                    "atmosphere": np.arange(0, 12),
                    "filled_canopy": np.array([], dtype=np.int_),
                    "filled_atmosphere": np.array([0, 11]),
                    "flux_layers": np.array([12]),
                },
                soil_thickness=np.array([0.25, 0.75]),
                soil_active=np.array([0.25, 0]),
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
            0.25,
            does_not_raise(),
            dict(
                n_canopy_layers=3,
                soil_layer_depths=np.array([-0.1, -0.5, -0.9]),
                offset_height=1.5,
                surface_height=0.2,
                layer_roles=ALTERNATE_CANOPY,
                layer_indices={
                    "above": np.array([0]),
                    "canopy": np.arange(1, 4),
                    "surface": np.array([4]),
                    "topsoil": np.array([5]),
                    "subsoil": np.array([6, 7]),
                    "all_soil": np.array([5, 6, 7]),
                    "active_soil": np.array([5, 6]),
                    "atmosphere": np.arange(0, 5),
                    "filled_canopy": np.array([], dtype=np.int_),
                    "filled_atmosphere": np.array([0, 4]),
                    "flux_layers": np.array([5]),
                },
                soil_thickness=np.array([0.1, 0.4, 0.4]),
                soil_active=np.array([0.1, 0.15, 0]),
            ),
            ((INFO, "Layer structure built from model configuration"),),
            id="alternative",
        ),
        pytest.param(
            """[core.layers]
            soil_layers=[-0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9]
            canopy_layers=3
            above_canopy_height_offset=1.5
            surface_layer_height=0.2
            """,
            0.45,
            does_not_raise(),
            dict(
                n_canopy_layers=3,
                soil_layer_depths=np.array(
                    [-0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9]
                ),
                offset_height=1.5,
                surface_height=0.2,
                layer_roles=np.concatenate([ALTERNATE_CANOPY, ["subsoil"] * 6]),
                layer_indices={
                    "above": np.array([0]),
                    "canopy": np.arange(1, 4),
                    "surface": np.array([4]),
                    "topsoil": np.array([5]),
                    "subsoil": np.arange(6, 14),
                    "all_soil": np.arange(5, 14),
                    "active_soil": np.array([5, 6, 7, 8, 9]),
                    "atmosphere": np.arange(0, 5),
                    "filled_canopy": np.array([], dtype=np.int_),
                    "filled_atmosphere": np.array([0, 4]),
                    "flux_layers": np.array([5]),
                },
                soil_thickness=np.repeat(0.1, 9),
                soil_active=np.array([0.1, 0.1, 0.1, 0.1, 0.05, 0, 0, 0, 0]),
            ),
            ((INFO, "Layer structure built from model configuration"),),
            id="alternative fine soil layers",
        ),
        pytest.param(
            """[core.layers]
            soil_layers=[0.1, -0.5, -0.9]
            canopy_layers=9
            above_canopy_height_offset=1.5
            surface_layer_height=0.2
            """,
            0.25,
            pytest.raises(ConfigurationError),
            None,
            ((ERROR, "Soil layer depths must be strictly decreasing and negative."),),
            id="bad_soil",
        ),
        pytest.param(
            """[core.layers]
            soil_layers=[-0.1, -0.5, -0.9]
            canopy_layers=9
            above_canopy_height_offset=1.5
            surface_layer_height=0.2
            """,
            1.0,
            pytest.raises(ConfigurationError),
            None,
            (
                (
                    ERROR,
                    "Maximum depth of soil layers is less than the maximum depth "
                    "of microbial activity",
                ),
            ),
            id="soil not deep enough for microbes",
        ),
    ],
)
def test_LayerStructure_init(
    caplog, config_string, max_active_depth, raises, expected_values, expected_log
):
    """Test the creation and error handling of LayerStructure."""
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import LayerStructure

    cfg = Config(cfg_strings=config_string)

    with raises:
        layer_structure = LayerStructure(
            cfg, n_cells=9, max_depth_of_microbial_activity=max_active_depth
        )

    log_check(caplog=caplog, expected_log=expected_log, subset=slice(-1, None, None))

    if isinstance(raises, does_not_raise):
        # Check the simple properties
        assert layer_structure.n_canopy_layers == expected_values["n_canopy_layers"]
        assert np.all(
            np.equal(
                layer_structure.soil_layer_depths, expected_values["soil_layer_depths"]
            )
        )
        assert (
            layer_structure.above_canopy_height_offset
            == expected_values["offset_height"]
        )
        assert layer_structure.surface_layer_height == expected_values["surface_height"]
        assert np.all(
            np.equal(layer_structure.layer_roles, expected_values["layer_roles"])
        )
        assert np.allclose(
            layer_structure.soil_layer_thickness, expected_values["soil_thickness"]
        )
        assert np.allclose(
            layer_structure.soil_layer_active_thickness, expected_values["soil_active"]
        )
        assert np.all(
            np.equal(np.isnan(layer_structure.lowest_canopy_filled), np.repeat(True, 9))
        )

        # Check the index dictionaries
        assert (
            layer_structure._role_indices_int.keys()
            == expected_values["layer_indices"].keys()
        )
        for ky in layer_structure._role_indices_int.keys():
            exp_int_index = expected_values["layer_indices"][ky]
            # Do the integer indices match
            assert np.all(
                np.equal(layer_structure._role_indices_int[ky], exp_int_index)
            )
            # Do the boolean indices match

            bool_indices = np.repeat(False, layer_structure.n_layers)
            bool_indices[exp_int_index] = True
            assert np.all(
                np.equal(layer_structure._role_indices_bool[ky], bool_indices)
            )

            # Does the attribute/property API return the same as the boolean index
            assert np.all(
                np.equal(getattr(layer_structure, f"index_{ky}"), bool_indices)
            )

        # Check the from_template data array
        template = layer_structure.from_template("a_variable")
        assert isinstance(template, DataArray)
        assert template.shape == (layer_structure.n_layers, layer_structure._n_cells)
        assert template.dims == ("layers", "cell_id")
        assert template.name == "a_variable"
        assert np.all(
            np.equal(template["layers"].to_numpy(), layer_structure.layer_indices)
        )
        assert np.all(
            np.equal(template["layer_roles"].to_numpy(), layer_structure.layer_roles)
        )
        assert np.all(
            np.equal(
                template["cell_id"].to_numpy(), np.arange(layer_structure._n_cells)
            )
        )


def test_LayerStructure_set_filled_canopy():
    """Test the set_filled_canopy_method.

    This test:

    * Calls the `set_filled_canopy` method with a simple canopy structure with a simple
      triangle of filled canopy layers across the 9 grid cells, so that the lowest
      canopy layer is never filled and the ninth cell has no filled.canopy.
    * Checks that the filled canopy layers and lowest filled canopy attributes are then
      as expected
    * Checks that the aggregate role index has been updated with the new canopy state.
    """

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import LayerStructure

    cfg = Config(cfg_strings="[core]")
    layer_structure = LayerStructure(
        cfg, n_cells=9, max_depth_of_microbial_activity=0.25
    )

    # Run the set_filled_canopy method to populate the filled layers and update cached
    # indices.
    canopy_heights = np.full(
        (layer_structure.n_canopy_layers, layer_structure._n_cells), np.nan
    )
    canopy_heights[0:8, 0:8] = np.where(np.flipud(np.tri(8)), 1, np.nan)

    layer_structure.set_filled_canopy(canopy_heights=canopy_heights)

    # Check the attributes have been set correctly.
    assert np.allclose(
        layer_structure.lowest_canopy_filled,
        np.concatenate([np.arange(8, 0, -1), [np.nan]]),
        equal_nan=True,
    )

    # Index attributes that are defined using filled_canopy
    exp_filled_canopy = np.repeat(False, layer_structure.n_layers)
    exp_filled_canopy[np.arange(1, 9)] = True
    assert np.allclose(layer_structure.index_filled_canopy, exp_filled_canopy)

    exp_filled_atmosphere = np.repeat(False, layer_structure.n_layers)
    exp_filled_atmosphere[np.concatenate([[0], np.arange(1, 9), [11]])] = True
    assert np.allclose(layer_structure.index_filled_atmosphere, exp_filled_atmosphere)

    exp_flux_layers = np.repeat(False, layer_structure.n_layers)
    exp_flux_layers[np.concatenate([np.arange(1, 9), [12]])] = True
    assert np.allclose(layer_structure.index_flux_layers, exp_flux_layers)


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
        (np.inf, pytest.raises(ConfigurationError)),
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
        (np.inf, pytest.raises(ConfigurationError)),
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
