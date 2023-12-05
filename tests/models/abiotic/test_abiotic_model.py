"""Test module for abiotic.abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pint
import pytest
from xarray import DataArray

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


def test_abiotic_model_initialization(
    caplog,
    dummy_climate_data,
    layer_roles_fixture,
):
    """Test `AbioticModel` initialization."""
    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.core.constants import CoreConsts
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel
    from virtual_rainforest.models.abiotic.constants import AbioticConsts

    # Initialize model
    model = AbioticModel(
        dummy_climate_data,
        pint.Quantity("1 day"),
        soil_layers=[-0.5, -1.0],
        canopy_layers=10,
        constants=AbioticConsts(),
        core_constants=CoreConsts(),
    )

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "abiotic"
    assert str(model) == "A abiotic model instance"
    assert repr(model) == "AbioticModel(update_interval = 1 day)"
    assert model.layer_roles == layer_roles_fixture

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (DEBUG, "abiotic model: required var 'air_temperature' checked"),
            (DEBUG, "abiotic model: required var 'canopy_height' checked"),
            (DEBUG, "abiotic model: required var 'layer_heights' checked"),
            (DEBUG, "abiotic model: required var 'leaf_area_index' checked"),
            (DEBUG, "abiotic model: required var 'atmospheric_pressure' checked"),
            (
                DEBUG,
                (
                    "abiotic model: required var 'sensible_heat_flux_topofcanopy'"
                    " checked"
                ),
            ),
            (DEBUG, "abiotic model: required var 'wind_speed_ref' checked"),
        ),
    )


def test_abiotic_model_initialization_no_data(caplog, dummy_climate_data):
    """Test `AbioticModel` initialization with no data."""

    from virtual_rainforest.core.constants import CoreConsts
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel
    from virtual_rainforest.models.abiotic.constants import AbioticConsts

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        empty_data = Data(grid)

        # Try and initialise model with empty data object
        _ = AbioticModel(
            empty_data,
            pint.Quantity("1 day"),
            soil_layers=[-0.5, -1.0],
            canopy_layers=10,
            constants=AbioticConsts,
            core_constants=CoreConsts,
        )

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=(
            (ERROR, "abiotic model: init data missing required var 'air_temperature'"),
            (ERROR, "abiotic model: init data missing required var 'canopy_height'"),
            (ERROR, "abiotic model: init data missing required var 'layer_heights'"),
            (ERROR, "abiotic model: init data missing required var 'leaf_area_index'"),
            (
                ERROR,
                (
                    "abiotic model: init data missing required var"
                    " 'atmospheric_pressure'"
                ),
            ),
            (
                ERROR,
                (
                    "abiotic model: init data missing required var"
                    " 'sensible_heat_flux_topofcanopy'"
                ),
            ),
            (ERROR, "abiotic model: init data missing required var 'wind_speed_ref'"),
            (ERROR, "abiotic model: error checking required_init_vars, see log."),
        ),
    )


@pytest.mark.parametrize(
    "cfg_string, time_interval, drag_coeff, raises, expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n[abiotic]\n",
            pint.Quantity("12 hours"),
            0.2,
            does_not_raise(),
            (
                (INFO, "Initialised abiotic.AbioticConsts from config"),
                (INFO, "Initialised core.CoreConsts from config"),
                (
                    INFO,
                    "Information required to initialise the abiotic model successfully "
                    "extracted.",
                ),
                (DEBUG, "abiotic model: required var 'air_temperature' checked"),
                (DEBUG, "abiotic model: required var 'canopy_height' checked"),
                (DEBUG, "abiotic model: required var 'layer_heights' checked"),
                (DEBUG, "abiotic model: required var 'leaf_area_index' checked"),
                (
                    DEBUG,
                    "abiotic model: required var 'atmospheric_pressure' checked",
                ),
                (
                    DEBUG,
                    (
                        "abiotic model: required var 'sensible_heat_flux_topofcanopy'"
                        " checked"
                    ),
                ),
                (DEBUG, "abiotic model: required var 'wind_speed_ref' checked"),
            ),
            id="default_config",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[abiotic.constants.AbioticConsts]\ndrag_coefficient = 0.05\n",
            pint.Quantity("12 hours"),
            0.05,
            does_not_raise(),
            (
                (INFO, "Initialised abiotic.AbioticConsts from config"),
                (INFO, "Initialised core.CoreConsts from config"),
                (
                    INFO,
                    "Information required to initialise the abiotic model successfully "
                    "extracted.",
                ),
                (DEBUG, "abiotic model: required var 'air_temperature' checked"),
                (DEBUG, "abiotic model: required var 'canopy_height' checked"),
                (DEBUG, "abiotic model: required var 'layer_heights' checked"),
                (DEBUG, "abiotic model: required var 'leaf_area_index' checked"),
                (
                    DEBUG,
                    "abiotic model: required var 'atmospheric_pressure' checked",
                ),
                (
                    DEBUG,
                    (
                        "abiotic model: required var 'sensible_heat_flux_topofcanopy'"
                        " checked"
                    ),
                ),
                (DEBUG, "abiotic model: required var 'wind_speed_ref' checked"),
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '12 hours'\n"
            "[abiotic.constants.AbioticConsts]\ndrag_coefficients = 0.05\n",
            None,
            None,
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Unknown names supplied for AbioticConsts: drag_coefficients"),
                (INFO, "Valid names are: "),
                (CRITICAL, "Could not initialise abiotic.AbioticConsts from config"),
            ),
            id="modified_config_incorrect",
        ),
    ],
)
def test_generate_abiotic_model(
    caplog,
    dummy_climate_data,
    cfg_string,
    time_interval,
    drag_coeff,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the abiotic model behaves as expected."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel

    # Register the module components to access constants classes
    register_module("virtual_rainforest.models.abiotic")

    # Build the config object
    config = Config(cfg_strings=cfg_string)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.update_interval == time_interval
        assert model.constants.drag_coefficient == drag_coeff

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string, time_interval, raises, expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '1 month'\n[abiotic]\n",
            pint.Quantity("1 month"),
            pytest.raises(ConfigurationError),
            (
                (INFO, "Initialised abiotic.AbioticConsts from config"),
                (INFO, "Initialised core.CoreConsts from config"),
                (
                    INFO,
                    "Information required to initialise the abiotic model "
                    "successfully extracted.",
                ),
                (ERROR, "The update interval is longer than the model's upper bound"),
            ),
            id="time interval out of bounds",
        ),
    ],
)
def test_generate_abiotic_model_bounds_error(
    caplog,
    dummy_climate_data,
    cfg_string,
    time_interval,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test that the initialisation of the abiotic model from config."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel

    # Register the module components to access constants classes
    register_module("virtual_rainforest.models.abiotic")

    # Build the config object
    config = Config(cfg_strings=cfg_string)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.layer_roles == layer_roles_fixture
        assert model.update_interval == time_interval

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,time_interval",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '1 day'\n[abiotic]\n",
            pint.Quantity("1 day"),
            id="updates correctly",
        ),
    ],
)
def test_update_abiotic_model(
    dummy_climate_data, layer_roles_fixture, cfg_string, time_interval
):
    """Test that update() returns expected output in data object."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel

    # Register the module components to access constants classes
    register_module("virtual_rainforest.models.abiotic")

    # Build the config object
    config = Config(cfg_strings=cfg_string)

    # initialise model
    model = AbioticModel.from_config(
        dummy_climate_data,
        config,
        pint.Quantity(config["core"]["timing"]["update_interval"]),
    )

    model.setup()
    model.update(time_index=0)

    friction_velocity_exp = np.array(
        [
            [0.0, 0.818637, 1.638679],
            [0.0, 0.81887, 1.638726],
            [0.0, 0.820036, 1.638959],
            [0.0, 0.821194, 1.639192],
            [0.0, 0.822174, 1.63939],
            [0.0, 0.822336, 1.639422],
        ]
    )
    wind_speed_exp = np.array(
        [
            [0.55, 5.536364, 11.07365],
            [0.54557, 5.491774, 10.984462],
            [0.523951, 5.274152, 10.549181],
            [0.503188, 5.065153, 10.13115],
            [0.486188, 4.89403, 9.788873],
            [0.483444, 4.866404, 9.733618],
        ]
    )

    wind_above_exp = np.array([0.55, 5.536364, 11.07365])

    np.testing.assert_allclose(
        model.data["wind_speed_above_canopy"], wind_above_exp, rtol=1e-3, atol=1e-3
    )
    np.testing.assert_allclose(
        model.data["friction_velocity"],
        DataArray(np.concatenate((friction_velocity_exp, np.full((9, 3), np.nan)))),
        rtol=1e-3,
        atol=1e-3,
    )
    np.testing.assert_allclose(
        model.data["wind_speed_canopy"],
        DataArray(np.concatenate((wind_speed_exp, np.full((9, 3), np.nan)))),
        rtol=1e-3,
        atol=1e-3,
    )
