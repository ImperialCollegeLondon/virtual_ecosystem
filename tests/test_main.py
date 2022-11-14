"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `vr_run` and the other functions
defined in main.py that it calls.
"""

from logging import CRITICAL, ERROR, INFO

import pytest

from virtual_rainforest.core.model import BaseModel, InitialisationError
from virtual_rainforest.main import configure_models, select_models, vr_run

from .conftest import log_check


@pytest.mark.parametrize(
    "model_list,no_models,expected_log_entries",
    [
        (
            ["soil"],  # valid input
            1,
            (
                (
                    INFO,
                    "Attempting to configure the following models: ['soil']",
                ),
            ),
        ),
        (
            ["soil", "core"],
            1,
            (
                (
                    INFO,
                    "Attempting to configure the following models: ['soil']",
                ),
            ),
        ),
        (
            ["soil", "freshwater"],  # Model that hasn't been defined
            0,
            (
                (
                    INFO,
                    "Attempting to configure the following models: ['soil', "
                    "'freshwater']",
                ),
                (
                    ERROR,
                    "The following models cannot be configured as they are not found in"
                    " the registry: ['freshwater']",
                ),
            ),
        ),
    ],
)
def test_select_models(caplog, model_list, no_models, expected_log_entries):
    """Test the model selecting function."""

    models = select_models(model_list)

    log_check(caplog, expected_log_entries)

    # Finally check that output is as expected
    if no_models > 0:
        assert len(models) == no_models
        assert all([type(model) == type(BaseModel) for model in models])
    else:
        assert models is None


@pytest.mark.parametrize(
    "config,output,expected_log_entries",
    [
        (
            {  # valid config
                "soil": {"no_layers": 1},
                "core": {"timing": {"min_time_step": "7 days"}},
            },
            "SoilModel(update_interval = 10080 minutes, no_layers = 1)",
            (
                (INFO, "Attempting to configure the following models: ['soil']"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
            ),
        ),
        (
            {  # missing soil config tag
                "soil": {},
                "core": {"timing": {"min_time_step": "7 days"}},
            },
            None,
            (
                (INFO, "Attempting to configure the following models: ['soil']"),
                (
                    ERROR,
                    "Configuration is missing information required to initialise the "
                    "soil model. The first missing key is 'no_layers'.",
                ),
            ),
        ),
        (
            {  # invalid soil config tag
                "soil": {"no_layers": -1},
                "core": {"timing": {"min_time_step": "7 days"}},
            },
            None,
            (
                (INFO, "Attempting to configure the following models: ['soil']"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (
                    CRITICAL,
                    "There has to be at least one soil layer in the soil model!",
                ),
            ),
        ),
        (
            {  # min_time_step missing units
                "soil": {"no_layers": 1},
                "core": {"timing": {"min_time_step": "7"}},
            },
            None,
            (
                (INFO, "Attempting to configure the following models: ['soil']"),
                (
                    ERROR,
                    "Configuration types appear not to have been properly validated. "
                    "This problem prevents initialisation of the soil model. The first "
                    "instance of this problem is as follows: Cannot convert from "
                    "'dimensionless' (dimensionless) to 'minute' ([time])",
                ),
            ),
        ),
    ],
)
def test_configure_models(caplog, config, output, expected_log_entries):
    """Test the function that configures the models."""

    model_list = select_models(["soil"])

    models = configure_models(config, model_list)

    if output is None:
        assert models == [None]
    else:
        assert repr(models[0]) == output

    log_check(caplog, expected_log_entries)


def test_vr_run_miss_model(mocker, caplog):
    """Test the main `vr_run` function handles missing models correctly."""

    mock_conf = mocker.patch("virtual_rainforest.main.validate_config")
    mock_conf.return_value = {"core": {"modules": ["topsoil"]}}

    with pytest.raises(InitialisationError):
        vr_run("tests/fixtures/all_config.toml", ".", "delete_me")

    expected_log_entries = (
        (INFO, "Attempting to configure the following models: ['topsoil']"),
        (
            ERROR,
            "The following models cannot be configured as they are not found in the "
            "registry: ['topsoil']",
        ),
        (CRITICAL, "Could not find all the desired models, ending the simulation."),
    )

    log_check(caplog, expected_log_entries)


def test_vr_run_bad_model(mocker, caplog):
    """Test the main `vr_run` function handles bad model configuration correctly."""

    mock_conf = mocker.patch("virtual_rainforest.main.validate_config")
    mock_conf.return_value = {"core": {"modules": ["soil"]}}
    mock_cf_mod = mocker.patch("virtual_rainforest.main.configure_models")
    mock_cf_mod.return_value = [None]

    with pytest.raises(InitialisationError):
        vr_run("tests/fixtures/all_config.toml", ".", "delete_me")

    expected_log_entries = (
        (INFO, "Attempting to configure the following models: ['soil']"),
        (
            INFO,
            "All models found in the registry, now attempting to configure them.",
        ),
        (
            CRITICAL,
            "Could not configure all the desired models, ending the simulation.",
        ),
    )

    log_check(caplog, expected_log_entries)
