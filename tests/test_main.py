"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `vr_run` and the other functions
defined in main.py that it calls.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO, WARNING

import pytest
from numpy import datetime64, timedelta64

from virtual_rainforest.core.model import BaseModel, InitialisationError
from virtual_rainforest.main import (
    check_for_fast_models,
    configure_models,
    extract_timing_details,
    get_models_to_update,
    select_models,
    setup_timing_loop,
    vr_run,
)
from virtual_rainforest.soil.model import SoilModel

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
                    "Attempting to configure the following models: ['soil']",
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
                    "Attempting to configure the following models: ['soil']",
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
                    "Attempting to configure the following models: ['freshwater', "
                    "'soil']",
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
                "core": {"timing": {"main_time_step": "7 days"}},
            },
            "SoilModel(update_interval = 10080 minutes, no_layers = 1)",
            does_not_raise(),
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
            {  # invalid soil config tag
                "soil": {"no_layers": -1},
                "core": {"timing": {"main_time_step": "7 days"}},
            },
            None,
            pytest.raises(InitialisationError),
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
                "core": {"timing": {"main_time_step": "7"}},
            },
            None,
            pytest.raises(InitialisationError),
            (
                (INFO, "Attempting to configure the following models: ['soil']"),
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
        (INFO, "Attempting to configure the following models: ['topsoil']"),
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
    mock_conf.return_value = {
        "core": {
            "modules": ["soil"],
            "timing": {
                "start_date": "2020-01-01",
                "end_date": "2120-01-01",
                "main_time_step": "0.5 martian days",
            },
        },
        "soil": {},
    }

    with pytest.raises(InitialisationError):
        vr_run("tests/fixtures/all_config.toml", ".", "delete_me")

    expected_log_entries = (
        (INFO, "Attempting to configure the following models: ['soil']"),
        (
            INFO,
            "All models found in the registry, now attempting to configure them.",
        ),
        (
            ERROR,
            "Configuration types appear not to have been properly validated. This "
            "problem prevents initialisation of the soil model. The first instance of "
            "this problem is as follows: 'martian' is not defined in the unit registry",
        ),
        (
            CRITICAL,
            "Could not configure all the desired models, ending the simulation. The "
            "following models failed: ['soil'].",
        ),
    )

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,output,raises,expected_log_entries",
    [
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "end_date": "2120-01-01",
                        "main_time_step": "0.5 days",
                    }
                }
            },
            {
                "start_time": datetime64("2020-01-01"),
                "end_time": datetime64("2120-01-01"),
                "update_interval": timedelta64(12, "h"),
            },
            does_not_raise(),
            (),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "end_date": "1995-01-01",
                        "main_time_step": "0.5 days",
                    }
                }
            },
            {},  # Fails so no output to check
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Simulation ends (2020-01-01) before it starts (1995-01-01)!",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "end_date": "2020-01-03",
                        "main_time_step": "7 days",
                    }
                }
            },
            {},  # Fails so no output to check
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Model will never update as update interval (10080 minutes) is "
                    "larger than the difference between the start and end times "
                    "(2 days)",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "end_date": "2120-01-01",
                        "main_time_step": "7 short days",
                    }
                }
            },
            {},  # Fails so no output to check
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Units for core.timing.main_time_step are not valid time units: 7 "
                    "short days",
                ),
            ),
        ),
    ],
)
def test_extract_timing_details(caplog, config, output, raises, expected_log_entries):
    """Test that function to extract main loop timing works as intended."""

    with raises:
        start_time, end_time, update_interval = extract_timing_details(config)
        assert start_time == output["start_time"]
        assert end_time == output["end_time"]
        assert update_interval == output["update_interval"]

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "update_interval,expected_log_entries",
    [
        (timedelta64(2, "W"), ()),
        (
            timedelta64(5, "W"),
            (
                (
                    WARNING,
                    "The following models have shorter time steps than the main model: "
                    "['soil']",
                ),
            ),
        ),
    ],
)
def test_check_for_fast_models(caplog, mocker, update_interval, expected_log_entries):
    """Test that function to warn user about short module time steps works."""

    # Create SoilModel instance and then populate the update_interval
    model = SoilModel.__new__(SoilModel)
    model.update_interval = timedelta64(3, "W")
    models_cfd = [model]

    check_for_fast_models(models_cfd, update_interval)

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "update_interval,expected_log_entries",
    [
        (timedelta64(2 * 7 * 24 * 60, "m"), ()),
        (
            timedelta64(int(27 * 365.25 * 24 * 60), "m"),
            (
                (
                    WARNING,
                    "Due to a (relatively) large model time step, 9.99% of the desired "
                    "time span is not covered!",
                ),
            ),
        ),
        (
            timedelta64(int(13 * 365.25 * 24 * 60), "m"),
            (
                (
                    WARNING,
                    "Due to a (relatively) large model time step, 13.3% of the desired "
                    "time span is not covered!",
                ),
            ),
        ),
    ],
)
def test_setup_timing_loop(caplog, update_interval, expected_log_entries):
    """Test to check that timing loop setup works properly."""

    start_time = datetime64("2020-03-01")
    end_time = datetime64("2050-03-01")
    current_time = setup_timing_loop(start_time, end_time, update_interval)

    assert start_time == current_time

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "current_time,refreshed",
    [(datetime64("2020-03-12"), False), (datetime64("2020-04-01"), True)],
)
def test_get_models_to_update(current_time, refreshed):
    """Test to check that splitting models based on update status works."""

    # Create SoilModel for testing
    model = SoilModel.__new__(SoilModel)
    model.update_interval = timedelta64(3, "W")
    models = [model]

    for model in models:
        model.start_model_timing(datetime64("2020-03-01"))

    to_refresh, fixed = get_models_to_update(current_time, models)

    if refreshed is True:
        assert len(to_refresh) == 1
        assert len(fixed) == 0
        assert models[0].last_update == datetime64("2020-04-01")
    else:
        assert len(to_refresh) == 0
        assert len(fixed) == 1
        assert models[0].last_update == datetime64("2020-03-01")
