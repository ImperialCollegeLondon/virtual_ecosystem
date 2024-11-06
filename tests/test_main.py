"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `ve_run` and the other functions
defined in main.py that it calls.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import pytest

from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError
from virtual_ecosystem.main import ve_run

from .conftest import log_check

INITIALISATION_LOG = [
    (INFO, "Initialising models: soil"),
    (INFO, "Initialised soil.SoilConsts from config"),
    (
        INFO,
        "Information required to initialise the soil model successfully extracted.",
    ),
    (DEBUG, "soil model: required var 'soil_c_pool_maom' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_lmwc' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_microbe' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_pom' checked"),
    (DEBUG, "soil model: required var 'soil_c_pool_necromass' checked"),
    (DEBUG, "soil model: required var 'soil_enzyme_pom' checked"),
    (DEBUG, "soil model: required var 'soil_enzyme_maom' checked"),
    (DEBUG, "soil model: required var 'soil_n_pool_don' checked"),
    (DEBUG, "soil model: required var 'soil_n_pool_particulate' checked"),
    (DEBUG, "soil model: required var 'pH' checked"),
    (DEBUG, "soil model: required var 'bulk_density' checked"),
    (DEBUG, "soil model: required var 'clay_fraction' checked"),
]


@pytest.mark.parametrize(
    "cfg_strings,output,raises,expected_log_entries",
    [
        pytest.param(
            '[core.timing]\nupdate_interval = "7 days"\n[soil]\n',
            "SoilModel(update_interval=604800 seconds)",
            does_not_raise(),
            tuple(INITIALISATION_LOG),
            id="valid config",
        ),
        pytest.param(
            '[core.timing]\nupdate_interval = "1 minute"\n[soil]\n',
            None,
            pytest.raises(InitialisationError),
            tuple(
                [
                    *INITIALISATION_LOG,
                    (
                        ERROR,
                        "The update interval is faster than the soil "
                        "lower bound of 30 minute.",
                    ),
                    (CRITICAL, "Configuration failed for models: soil"),
                ],
            ),
            id="update interval too short",
        ),
        pytest.param(
            '[core.timing]\nupdate_interval = "1 year"\n[soil]\n',
            None,
            pytest.raises(InitialisationError),
            tuple(
                [
                    *INITIALISATION_LOG,
                    (
                        ERROR,
                        "The update interval is slower than the soil "
                        "upper bound of 3 month.",
                    ),
                    (CRITICAL, "Configuration failed for models: soil"),
                ],
            ),
            id="update interval too long",
        ),
    ],
)
def test_initialise_models(
    caplog,
    dummy_carbon_data,
    cfg_strings,
    output,
    raises,
    expected_log_entries,
):
    """Test the function that initialises the models."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.main import initialise_models

    # Generate a configuration to use, using simple inputs to populate most from
    # defaults. Then clear the caplog to isolate the logging for the function,
    config = Config(cfg_strings=cfg_strings)
    core_components = CoreComponents(config)
    caplog.clear()

    with raises:
        models = initialise_models(
            config=config,
            data=dummy_carbon_data,
            core_components=core_components,
            models=config.model_classes,
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
                    ERROR,
                    "Invalid units for core.timing.update_interval: 0.5 martian days",
                ),
            ),
            id="bad_config_data_one",
        ),
    ],
)
def test_ve_run_model_issues(caplog, config_content, expected_log_entries, mocker):
    """Test the main `ve_run` function handles bad model configurations correctly.

    Note that some of this is also safeguarded by the config validation. Unknown model
    names should not pass schema validation, but incorrect config data can still pass
    schema validation.
    """
    # TODO: Once models are adapted, this can be removed
    mocker.patch("virtual_ecosystem.core.variables.register_all_variables")

    with pytest.raises(ConfigurationError):
        ve_run(cfg_strings=config_content)

    log_check(caplog, expected_log_entries, subset=slice(-1, None, None))
