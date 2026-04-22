"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `ve_run` and the other functions
defined in main.py that it calls.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO
from typing import cast

import pytest

from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError

from .conftest import log_check, record_found_in_log

INITIALISATION_LOG = [
    (INFO, "Initialising models: litter"),
    (INFO, "Initialising litter model"),
    (
        INFO,
        "Information required to initialise the litter model successfully extracted.",
    ),
    (DEBUG, "litter model: required var 'litter_pool_above_metabolic_cnp' checked"),
    (DEBUG, "litter model: required var 'litter_pool_above_structural_cnp' checked"),
    (DEBUG, "litter model: required var 'litter_pool_woody_cnp' checked"),
    (DEBUG, "litter model: required var 'litter_pool_below_metabolic_cnp' checked"),
    (DEBUG, "litter model: required var 'litter_pool_below_structural_cnp' checked"),
    (DEBUG, "litter model: required var 'lignin_above_structural' checked"),
    (DEBUG, "litter model: required var 'lignin_woody' checked"),
    (DEBUG, "litter model: required var 'lignin_below_structural' checked"),
]


@pytest.mark.parametrize(
    "cfg_strings,output,raises,expected_log_entries",
    [
        pytest.param(
            '[core.timing]\nupdate_interval = "7 days"\n[litter]\n',
            "LitterModel(update_interval=604800 seconds)",
            does_not_raise(),
            tuple(
                [
                    *INITIALISATION_LOG,
                ],
            ),
            id="valid config",
        ),
        pytest.param(
            '[core.timing]\nupdate_interval = "1 minute"\n[litter]\n',
            None,
            pytest.raises(InitialisationError),
            tuple(
                [
                    *INITIALISATION_LOG,
                    (
                        ERROR,
                        "The update interval is faster than the litter "
                        "lower bound of 30 minute.",
                    ),
                    (CRITICAL, "Configuration failed for models: litter"),
                ],
            ),
            id="update interval too short",
        ),
        pytest.param(
            '[core.timing]\nupdate_interval = "1 year"\n[litter]\n',
            None,
            pytest.raises(InitialisationError),
            tuple(
                [
                    *INITIALISATION_LOG,
                    (
                        ERROR,
                        "The update interval is slower than the litter "
                        "upper bound of 3 month.",
                    ),
                    (CRITICAL, "Configuration failed for models: litter"),
                ],
            ),
            id="update interval too long",
        ),
    ],
)
def test_initialise_models(
    caplog,
    dummy_litter_data,
    cfg_strings,
    output,
    raises,
    expected_log_entries,
):
    """Test the function that initialises the models."""

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.main import initialise_models

    # Generate a configuration to use, using simple inputs to populate most from
    # defaults. Then clear the caplog to isolate the logging for the function,
    config_data = ConfigurationLoader(cfg_strings=cfg_strings)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)
    caplog.clear()

    with raises:
        models = initialise_models(
            configuration=configuration,
            data=dummy_litter_data,
            core_components=core_components,
            models=configuration._model_classes,
        )

        if output is None:
            assert models == [None]
        else:
            assert repr(models["litter"]) == output

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
                    "core.timing.update_interval = 0.5 martian days: Value error, "
                    "Cannot parse value as time quantity: 0.5 martian days",
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
    from virtual_ecosystem.main import ve_run

    with pytest.raises(ConfigurationError):
        ve_run(cfg_strings=config_content)

    record_found_in_log(caplog, expected_log_entries)


@pytest.mark.parametrize(
    argnames="progress_value, output_length",
    argvalues=(
        pytest.param(0, 0, id="silent"),
        pytest.param(1, 3, id="minimal"),
        pytest.param(2, 9, id="staged"),
        pytest.param(3, 11, id="full"),
    ),
)
def test_ve_run_progress_reporting(capsys, tmp_path, progress_value, output_length):
    """Test the function that initialises the models.

    The progress report is muted when the log is not written to file, so this writes the
    log out to a temporary file.
    """

    from virtual_ecosystem.core.logger import remove_file_logger
    from virtual_ecosystem.main import ve_run

    # Need to remove any existing file log attached to LOGGER
    remove_file_logger()

    # Make the output directory - need to make a decision about whether ve_run creates
    # this.
    out_dir = tmp_path / "out_dir"
    out_dir.mkdir()

    # Run ve_run with just a minimal TestingModel used and don't save any outputs
    ve_run(
        cfg_strings=f"""
[core.data_output_options]
save_initial_state = false
save_continuous_data = false
save_final_state = false
save_merged_config = false
out_path='{out_dir!s}'
[core.data]
variable = []
[testing]
""",
        progress=progress_value,
        logfile=tmp_path / "log.log",
    )

    out, err = capsys.readouterr()

    assert len(err.splitlines()) == 0
    output = [v for v in out.splitlines() if v]  # drop blank lines
    assert len(output) == output_length


def test_sort_disturbances(mocker):
    """Test the sort_disturbances function."""
    from virtual_ecosystem.core.configuration import (
        CompiledConfiguration,
        DisturbanceConfigurationRoot,
    )
    from virtual_ecosystem.main import sort_disturbances

    models = {
        "normal": DisturbanceConfigurationRoot(run_at=0, priority=0),
        "more_important": DisturbanceConfigurationRoot(run_at=0, priority=2),
        "important": DisturbanceConfigurationRoot(run_at=0, priority=1),
    }
    expected_order = ["more_important", "important", "normal"]

    class MockConfig(CompiledConfiguration):
        _model_classes = models

        def get_subconfiguration(self, model_name, _):
            return self._model_classes[model_name]

        @property
        def disturbance(self):
            return self

    actual_order = sort_disturbances(cast(CompiledConfiguration, MockConfig()))
    assert expected_order == actual_order


DISTURBANCE_INITIALISATION_LOG = [
    (INFO, "Initialising disturbances: disturbance_testing"),
    (INFO, "Initialising disturbance_testing disturbance"),
    (
        INFO,
        "Disturbance testing model instance generated from configuration.",
    ),
]


@pytest.mark.parametrize(
    "cfg_strings,output,raises,expected_log_entries",
    [
        pytest.param(
            "[core.timing]\nupdate_interval = '7 days'\n"
            "[testing]\n"
            "[disturbance.disturbance_testing]\n",
            "DisturbanceTestingModel(_run_at=[0])",
            does_not_raise(),
            tuple(
                [
                    *DISTURBANCE_INITIALISATION_LOG,
                ],
            ),
            id="valid config",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '7 days'\n"
            "[disturbance.disturbance_testing]\n",
            None,
            pytest.raises(InitialisationError),
            tuple(
                [
                    *DISTURBANCE_INITIALISATION_LOG[:-1],
                    (
                        CRITICAL,
                        "Configuration failed for disturbances: disturbance_testing",
                    ),
                ],
            ),
            id="model required for disturbance missing",
        ),
    ],
)
def test_initialise_disturbances(
    caplog,
    dummy_litter_data,
    cfg_strings,
    output,
    raises,
    expected_log_entries,
):
    """Test the function that initialises the models."""

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.main import initialise_disturbances

    # Generate a configuration to use, using simple inputs to populate most from
    # defaults. Then clear the caplog to isolate the logging for the function,
    config_data = ConfigurationLoader(cfg_strings=cfg_strings)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)
    caplog.clear()

    with raises:
        models = initialise_disturbances(
            configuration=configuration,
            data=dummy_litter_data,
            core_components=core_components,
            models=configuration._model_classes,
        )

        if output is None:
            assert models == [None]
        else:
            assert repr(models["disturbance_testing"]) == output

    log_check(caplog, expected_log_entries)
