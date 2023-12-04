"""Test module for abiotic.abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import pint
import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


def test_abiotic_model_initialization(
    caplog,
    dummy_climate_data,
    layer_roles_fixture,
):
    """Test `AbioticModel` initialization."""
    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel
    from virtual_rainforest.models.abiotic.constants import AbioticConsts

    # Initialize model
    model = AbioticModel(
        dummy_climate_data,
        pint.Quantity("1 day"),
        soil_layers=[-0.5, -1.0],
        canopy_layers=10,
        constants=AbioticConsts(),
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
            (DEBUG, "abiotic model: required var 'atmospheric_pressure_ref' checked"),
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
                    " 'atmospheric_pressure_ref'"
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
                    "abiotic model: required var 'atmospheric_pressure_ref' checked",
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
                    "abiotic model: required var 'atmospheric_pressure_ref' checked",
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
