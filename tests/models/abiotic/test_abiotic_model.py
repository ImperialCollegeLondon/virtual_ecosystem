"""Test module for abiotic.abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO

import pint
import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    "raises,expected_log_entries",
    [
        (
            does_not_raise(),
            (
                (
                    DEBUG,
                    "abiotic model: required var 'air_temperature_ref' checked",
                ),
            ),
        ),
    ],
)
def test_abiotic_model_initialization(
    caplog,
    dummy_climate_data,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test `AbioticModel` initialization."""
    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel
    from virtual_rainforest.models.abiotic.constants import AbioticConsts

    with raises:
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
        assert repr(model) == "AbioticModel(update_interval = 1 day)"
        assert model.layer_roles == layer_roles_fixture

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,time_interval,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n[core.timing]\nupdate_interval = '1 day'\n[abiotic]\n",
            pint.Quantity("1 day"),
            does_not_raise(),
            (
                (INFO, "Initialised abiotic.AbioticConsts from config"),
                (
                    INFO,
                    "Information required to initialise the abiotic model "
                    "successfully extracted.",
                ),
                (
                    DEBUG,
                    "abiotic model: required var 'air_temperature_ref' checked",
                ),
            ),
            id="initialises correctly",
        ),
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
def test_generate_abiotic_model(
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
