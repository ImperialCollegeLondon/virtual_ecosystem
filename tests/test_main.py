"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `ve_run` and the other functions
defined in main.py that it calls.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING

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
    (DEBUG, "soil model: required var 'soil_enzyme_pom' checked"),
    (DEBUG, "soil model: required var 'soil_enzyme_maom' checked"),
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


@pytest.mark.parametrize(
    "cfg_strings,method,raises,model_keys,expected_log_entries",
    [
        pytest.param(
            "[core]\n[soil.depends]\ninit=['abiotic_simple']\n"
            "[abiotic_simple.depends]\ninit=[]\n",
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

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.main import _get_model_sequence

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
