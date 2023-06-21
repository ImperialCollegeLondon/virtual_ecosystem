"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `vr_run` and the other functions
defined in main.py that it calls.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO
from pathlib import Path

import pint
import pytest
from numpy import datetime64, timedelta64

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.main import vr_run

from .conftest import log_check


@pytest.mark.parametrize(
    "model_list,no_models,raises,expected_log_entries",
    [
        pytest.param(
            ["soil"],  # valid input
            1,
            does_not_raise(),
            (
                (
                    INFO,
                    "Attempting to configure the following models: ['soil']",
                ),
            ),
            id="valid input",
        ),
        pytest.param(
            ["soil", "core"],
            1,
            does_not_raise(),
            (
                (
                    INFO,
                    "Attempting to configure the following models: ['soil']",
                ),
            ),
            id="ignores core",
        ),
        pytest.param(
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
            id="undefined model",
        ),
    ],
)
def test_select_models(caplog, model_list, no_models, raises, expected_log_entries):
    """Test the model selecting function."""
    from virtual_rainforest.main import select_models

    with raises:
        models = select_models(model_list)
        assert len(models) == no_models
        assert all([type(model) == type(BaseModel) for model in models])

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,update_interval,output,raises,expected_log_entries",
    [
        pytest.param(
            {"core": {"layers": {"soil_layers": 2, "canopy_layers": 10}}},
            pint.Quantity("7 days"),
            "SoilModel(update_interval = 7 day)",
            does_not_raise(),
            (
                (INFO, "Attempting to configure the following models: ['soil']"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_maom' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_lmwc' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'soil_c_pool_microbe' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'pH' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'bulk_density' checked",
                ),
                (
                    DEBUG,
                    "soil model: required var 'percent_clay' checked",
                ),
            ),
            id="valid config",
        ),
        pytest.param(
            {"core": {"layers": {"soil_layers": 2, "canopy_layers": 10}}},
            pint.Quantity("1 minute"),
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
                    ERROR,
                    "The update interval is shorter than the model's lower bound",
                ),
                (
                    CRITICAL,
                    "Could not configure all the desired models, ending the "
                    "simulation.",
                ),
            ),
            id="update interval too short",
        ),
        pytest.param(
            {"core": {"layers": {"soil_layers": 2, "canopy_layers": 10}}},
            pint.Quantity("1 year"),
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
                    ERROR,
                    "The update interval is longer than the model's upper bound",
                ),
                (
                    CRITICAL,
                    "Could not configure all the desired models, ending the "
                    "simulation.",
                ),
            ),
            id="update interval too long",
        ),
    ],
)
def test_configure_models(
    caplog,
    dummy_carbon_data,
    config,
    update_interval,
    output,
    raises,
    expected_log_entries,
):
    """Test the function that configures the models."""
    from virtual_rainforest.main import configure_models, select_models

    with raises:
        model_list = select_models(["soil"])

        models = configure_models(
            config, dummy_carbon_data, model_list, update_interval
        )

        if output is None:
            assert models == [None]
        else:
            assert repr(models["soil"]) == output

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config_content, expected_log_entries",
    [
        pytest.param(
            {
                "core": {
                    "modules": ["soil"],
                    "timing": {
                        "start_date": "2020-01-01",
                        "run_length": "50 years",
                        "update_interval": "0.5 martian days",
                    },
                    "data": [],
                    "grid": {
                        "grid_type": "square",
                        "cell_area": 10000,
                        "cell_nx": 3,
                        "cell_ny": 3,
                    },
                },
            },
            (
                (INFO, "Grid created from configuration."),
                (INFO, "Loading data from configuration"),
                (INFO, "Attempting to configure the following models: ['soil']"),
                (
                    INFO,
                    "All models found in the registry, now attempting "
                    "to configure them.",
                ),
                (
                    CRITICAL,
                    "Units for core.timing.update_interval are not valid time units: "
                    "0.5 martian days",
                ),
            ),
            id="bad_config_data",
        ),
        pytest.param(
            {
                "core": {
                    "modules": ["topsoil"],
                    "data": [],
                    "grid": {
                        "grid_type": "square",
                        "cell_area": 10000,
                        "cell_nx": 3,
                        "cell_ny": 3,
                    },
                },
            },
            (
                (INFO, "Grid created from configuration."),
                (INFO, "Loading data from configuration"),
                (INFO, "Attempting to configure the following models: ['topsoil']"),
                (
                    CRITICAL,
                    "The following models cannot be configured as they are not "
                    "found in the registry: ['topsoil']",
                ),
            ),
            id="missing_model",
        ),
    ],
)
def test_vr_run_model_issues(mocker, caplog, config_content, expected_log_entries):
    """Test the main `vr_run` function handles bad model configurations correctly.

    Note that some of this is also safeguarded by the config validation. Unknown model
    names should not pass schema validation, but incorrect config data can still pass
    schema validation.
    """

    # Simple drop in replacement for the Config class that sidesteps TOML loading and
    # validation and simply asserts the resulting config dictionary contents.
    class MockConfig(dict):
        def __init__(self, cfg_paths):
            self.update(config_content)

        def export_config(self, outfile: Path):
            pass

    mocker.patch("virtual_rainforest.main.Config", MockConfig)

    with pytest.raises(InitialisationError):
        vr_run([], Path("./delete_me.toml"))
        # If vr_run is successful (which it shouldn't be) clean up the file
        Path("./delete_me.toml").unlink()

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,output,raises,expected_log_entries",
    [
        pytest.param(
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "10 minutes",
                        "run_length": "30 years",
                    }
                }
            },
            {
                "start_time": datetime64("2020-01-01"),
                "update_interval": timedelta64(10, "m"),
                "update_interval_as_quantity": pint.Quantity("10 minutes"),
                "end_time": datetime64("2049-12-31T12:00"),
            },
            does_not_raise(),
            (
                (
                    INFO,
                    "Virtual Rainforest simulation will run from 2020-01-01 until "
                    "2049-12-31T12:00:00. This is a run length of 946728000 seconds, "
                    "the user requested 946728000 seconds",
                ),
            ),
            id="timing correct",
        ),
        pytest.param(
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "10 minutes",
                        "run_length": "1 minute",
                    }
                }
            },
            {},  # Fails so no output to check
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Models will never update as the update interval (600 seconds) is "
                    "larger than the run length (60 seconds)",
                ),
            ),
            id="run length < update interval",
        ),
        pytest.param(
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "10 minutes",
                        "run_length": "7 short days",
                    }
                }
            },
            {},  # Fails so no output to check
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Units for core.timing.run_length are not valid time units: 7 short"
                    " days",
                ),
            ),
            id="invalid run length units",
        ),
        pytest.param(
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "10 long minutes",
                        "run_length": "30 years",
                    }
                }
            },
            {},  # Fails so no output to check
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Units for core.timing.update_interval are not valid time units: 10"
                    " long minutes",
                ),
            ),
            id="invalid update_interval units",
        ),
        pytest.param(
            {  # update_interval missing units
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "7",
                        "run_length": "30 years",
                    }
                },
            },
            {},  # Fails so no output to check
            pytest.raises(InitialisationError),
            (
                (
                    CRITICAL,
                    "Units for core.timing.update_interval are not valid time units: 7",
                ),
            ),
            id="model_time_step missing units",
        ),
    ],
)
def test_extract_timing_details(caplog, config, output, raises, expected_log_entries):
    """Test that function to extract main loop timing works as intended."""
    from virtual_rainforest.main import extract_timing_details

    with raises:
        (
            current_time,
            update_interval,
            update_interval_as_quantity,
            end_time,
        ) = extract_timing_details(config)
        assert end_time == output["end_time"]
        assert update_interval == output["update_interval"]
        assert current_time == output["start_time"]
        assert update_interval_as_quantity == output["update_interval_as_quantity"]

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize("time_index", [0, 1])
def test_output_current_state(mocker, dummy_carbon_data, time_index):
    """Test that function to output the current data state works as intended."""

    from virtual_rainforest.core.base_model import MODEL_REGISTRY
    from virtual_rainforest.main import output_current_state

    data_options = {"out_folder_continuous": "."}

    # Patch the relevant lower level function
    mock_save = mocker.patch("virtual_rainforest.main.Data.save_timeslice_to_netcdf")

    # Extract model from registry and put into expected dictionary format
    configured_models = {"soil": MODEL_REGISTRY["soil"]}

    # Then call the top level function
    output_current_state(dummy_carbon_data, configured_models, data_options, time_index)

    # Check that the mocked function was called once with correct input (which is
    # calculated in the higher level function)
    assert mock_save.call_count == 1
    assert mock_save.call_args == mocker.call(
        Path(f"./continuous_state{time_index}.nc"),
        ["soil_c_pool_maom", "soil_c_pool_lmwc", "soil_c_pool_microbe"],
    )
