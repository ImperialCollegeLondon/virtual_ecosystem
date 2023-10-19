"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `vr_run` and the other functions
defined in main.py that it calls.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING

import numpy as np
import pint
import pytest

from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.main import vr_run

from .conftest import log_check


@pytest.mark.parametrize(
    "cfg_strings,update_interval,output,raises,expected_log_entries",
    [
        pytest.param(
            "[core]\n[soil]\n",
            pint.Quantity("7 days"),
            "SoilModel(update_interval = 7 day)",
            does_not_raise(),
            (
                (INFO, "Initialising models: soil"),
                (INFO, "Initialised soil.SoilConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (DEBUG, "soil model: required var 'soil_c_pool_maom' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_lmwc' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_microbe' checked"),
                (DEBUG, "soil model: required var 'soil_c_pool_pom' checked"),
                (DEBUG, "soil model: required var 'pH' checked"),
                (DEBUG, "soil model: required var 'bulk_density' checked"),
                (DEBUG, "soil model: required var 'percent_clay' checked"),
            ),
            id="valid config",
        ),
        pytest.param(
            "[core]\n[soil]\n",
            pint.Quantity("1 minute"),
            None,
            pytest.raises(InitialisationError),
            (
                (INFO, "Initialising models: soil"),
                (INFO, "Initialised soil.SoilConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (ERROR, "The update interval is shorter than the model's lower bound"),
                (CRITICAL, "Configuration failed for models: soil"),
            ),
            id="update interval too short",
        ),
        pytest.param(
            "[core]\n[soil]\n",
            pint.Quantity("1 year"),
            None,
            pytest.raises(InitialisationError),
            (
                (INFO, "Initialising models: soil"),
                (INFO, "Initialised soil.SoilConsts from config"),
                (
                    INFO,
                    "Information required to initialise the soil model successfully "
                    "extracted.",
                ),
                (ERROR, "The update interval is longer than the model's upper bound"),
                (CRITICAL, "Configuration failed for models: soil"),
            ),
            id="update interval too long",
        ),
    ],
)
def test_initialise_models(
    caplog,
    dummy_carbon_data,
    cfg_strings,
    update_interval,
    output,
    raises,
    expected_log_entries,
):
    """Test the function that initialises the models."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.main import initialise_models

    # Generate a configuration to use, using simple inputs to populate most from
    # defaults. Then clear the caplog to isolate the logging for the function,
    config = Config(cfg_strings=cfg_strings)
    caplog.clear()

    with raises:
        models = initialise_models(
            config=config,
            data=dummy_carbon_data,
            models=config.model_classes,
            update_interval=update_interval,
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
            """[core]
            data = {}
            [core.data_output_options]
            save_merged_config = false
            [core.timing]
            start_date = "2020-01-01"
            run_length = "50 years"
            update_interval = "0.5 martian days"
            [core.grid]
            grid_type = "square"
            cell_area = 10000
            cell_nx = 3
            cell_ny = 3
            [soil]
            """,
            (
                (
                    CRITICAL,
                    "Units for core.timing.update_interval are not valid time units: "
                    "0.5 martian days",
                ),
            ),
            id="bad_config_data_one",
        ),
    ],
)
def test_vr_run_model_issues(caplog, config_content, expected_log_entries):
    """Test the main `vr_run` function handles bad model configurations correctly.

    Note that some of this is also safeguarded by the config validation. Unknown model
    names should not pass schema validation, but incorrect config data can still pass
    schema validation.
    """

    with pytest.raises(InitialisationError):
        vr_run(cfg_strings=config_content)

    log_check(caplog, expected_log_entries, subset=slice(-1, None, None))


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
                "start_time": np.datetime64("2020-01-01"),
                "update_interval": np.timedelta64(10, "m"),
                "update_interval_as_quantity": pint.Quantity("10 minutes"),
                "end_time": np.datetime64("2049-12-31T12:00"),
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

    log_check(caplog=caplog, expected_log=expected_log_entries)


@pytest.mark.parametrize(
    "cfg_strings,method,raises,model_keys,expected_log_entries",
    [
        pytest.param(
            "[core]\n[soil.depends]\ninit=['abiotic_simple']\n[abiotic_simple]",
            "init",
            does_not_raise(),
            ["abiotic_simple", "soil"],
            ((INFO, "Model init execution order set: abiotic_simple, soil"),),
            id="valid init depends",
        ),
        pytest.param(
            "[core]\n[abiotic_simple.depends]\nupdate=['soil']\n[soil]\n",
            "update",
            does_not_raise(),
            ["soil", "abiotic_simple"],
            ((INFO, "Model update execution order set: soil, abiotic_simple"),),
            id="valid update depends",
        ),
        pytest.param(
            "[core]\n[abiotic_simple.depends]\nupdate=['soil']\n"
            "[soil.depends]\nupdate=['abiotic_simple']\n",
            "update",
            pytest.raises(ConfigurationError),
            None,
            ((CRITICAL, "Model update dependencies are cyclic"),),
            id="cyclic dependencies",
        ),
        pytest.param(
            "[core]\n[abiotic_simple.depends]\nupdate=['abiotic_simple']\n",
            "update",
            pytest.raises(ConfigurationError),
            None,
            (
                (
                    CRITICAL,
                    "Model update dependencies for abiotic_simple includes itself",
                ),
            ),
            id="depends over self",
        ),
        pytest.param(
            "[core]\n[abiotic_simple.depends]\nupdate=['plants', 'soil']\n[soil]",
            "update",
            does_not_raise(),
            ["soil", "abiotic_simple"],
            (
                (
                    WARNING,
                    "Configuration does not include all of the models listed in "
                    "update dependencies for abiotic_simple: plants",
                ),
                (INFO, "Model update execution order set: soil, abiotic_simple"),
            ),
            id="depends includes unconfigured models",
        ),
    ],
)
def test_get_model_sequence(
    caplog,
    cfg_strings,
    raises,
    method,
    model_keys,
    expected_log_entries,
):
    """Test the function that sets the model sequence."""

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.main import _get_model_sequence

    # Generate a configuration to use, using simple inputs to populate most from
    # defaults. Then clear the caplog to isolate the logging for the function,
    config = Config(cfg_strings=cfg_strings)
    caplog.clear()

    with raises:
        model_sequence = _get_model_sequence(
            config=config, models=config.model_classes, method=method
        )

        if isinstance(raises, does_not_raise):
            assert model_keys == list(model_sequence.keys())

    log_check(caplog, expected_log_entries)
