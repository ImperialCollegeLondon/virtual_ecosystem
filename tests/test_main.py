"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `vr_run` and the other functions
defined in main.py that it calls.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO

import pytest

from virtual_rainforest.core.model import BaseModel, InitialisationError
from virtual_rainforest.main import configure_models, select_models, vr_run

from .conftest import log_check


@pytest.mark.parametrize(
    "model_list,no_models,raises,expected_log_entries",
    [
        (
            ["soil"],  # valid input
            1,
            does_not_raise(),
            (
                (
                    INFO,
                    "Attempting to configure the following models: {'soil'}",
                ),
            ),
        ),
        (
            ["soil", "core"],
            1,
            does_not_raise(),
            (
                (
                    INFO,
                    "Attempting to configure the following models: {'soil'}",
                ),
            ),
        ),
        (
            ["soil", "freshwater"],  # Model that hasn't been defined
            0,
            pytest.raises(InitialisationError),
            (
                (
                    INFO,
                    "Attempting to configure the following models: {'freshwater', "
                    "'soil'}",
                ),
                (
                    CRITICAL,
                    "The following models cannot be configured as they are not found in"
                    " the registry: ['freshwater']",
                ),
            ),
        ),
    ],
)
def test_select_models(caplog, model_list, no_models, raises, expected_log_entries):
    """Test the model selecting function."""

    with raises:
        models = select_models(model_list)
        assert len(models) == no_models
        assert all([type(model) == type(BaseModel) for model in models])

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,output,raises,expected_log_entries",
    [
        (
            {  # valid config
                "soil": {"no_layers": 1},
                "core": {"timing": {"min_time_step": "7 days"}},
            },
            "SoilModel(update_interval = 10080 minutes, no_layers = 1)",
            does_not_raise(),
            (
                (INFO, "Attempting to configure the following models: {'soil'}"),
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
            pytest.raises(InitialisationError),
            (
                (INFO, "Attempting to configure the following models: {'soil'}"),
                (
                    ERROR,
                    "Configuration is missing information required to initialise the "
                    "soil model. The first missing key is 'no_layers'.",
                ),
                (
                    CRITICAL,
                    "Could not configure all the desired models, ending the "
                    "simulation.",
                ),
            ),
        ),
        (
            {  # invalid soil config tag
                "soil": {"no_layers": -1},
                "core": {"timing": {"min_time_step": "7 days"}},
            },
            None,
            pytest.raises(InitialisationError),
            (
                (INFO, "Attempting to configure the following models: {'soil'}"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (
                    CRITICAL,
                    "There has to be at least one soil layer in the soil model!",
                ),
                (
                    CRITICAL,
                    "Could not configure all the desired models, ending the "
                    "simulation.",
                ),
            ),
        ),
        (
            {  # min_time_step missing units
                "soil": {"no_layers": 1},
                "core": {"timing": {"min_time_step": "7"}},
            },
            None,
            pytest.raises(InitialisationError),
            (
                (INFO, "Attempting to configure the following models: {'soil'}"),
                (
                    ERROR,
                    "Configuration types appear not to have been properly validated. "
                    "This problem prevents initialisation of the soil model. The first "
                    "instance of this problem is as follows: Cannot convert from "
                    "'dimensionless' (dimensionless) to 'minute' ([time])",
                ),
                (
                    CRITICAL,
                    "Could not configure all the desired models, ending the "
                    "simulation.",
                ),
            ),
        ),
    ],
)
def test_configure_models(caplog, config, output, raises, expected_log_entries):
    """Test the function that configures the models."""

    with raises:
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
        (INFO, "Attempting to configure the following models: {'topsoil'}"),
        (
            CRITICAL,
            "The following models cannot be configured as they are not found in the "
            "registry: ['topsoil']",
        ),
    )

    log_check(caplog, expected_log_entries)


def test_vr_run_bad_model(mocker, caplog):
    """Test the main `vr_run` function handles bad model configuration correctly."""

    mock_conf = mocker.patch("virtual_rainforest.main.validate_config")
    mock_conf.return_value = {"core": {"modules": ["soil"]}, "soil": {}}

    with pytest.raises(InitialisationError):
        vr_run("tests/fixtures/all_config.toml", ".", "delete_me")

    expected_log_entries = (
        (INFO, "Attempting to configure the following models: {'soil'}"),
        (
            INFO,
            "All models found in the registry, now attempting to configure them.",
        ),
        (
            ERROR,
            "Configuration is missing information required to initialise the soil "
            "model. The first missing key is 'timing'.",
        ),
        (
            CRITICAL,
            "Could not configure all the desired models, ending the simulation.",
        ),
    )

    log_check(caplog, expected_log_entries)
