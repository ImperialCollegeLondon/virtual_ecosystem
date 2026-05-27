"""An integration test for the VR command-line interface."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def config_file_list():
    """List of files (from config folder) to be used for simulation runs."""
    return [
        "abiotic_config.toml",
        "animal_config.toml",
        "data_config.toml",
        "hydrology_config.toml",
        "litter_config.toml",
        "plant_config.toml",
        "soil_config.toml",
    ]


def test_ve_run_install_example(capsys):
    """Test that the CLI can successfully run with example data."""
    from virtual_ecosystem.entry_points import ve_run_cli

    with TemporaryDirectory() as tempdir:
        ve_run_cli(args_list=["--install-example", tempdir])

        captured = capsys.readouterr()
        expected = "Example directory created at:"
        assert captured.out.startswith(expected)


@pytest.mark.slow
def test_ve_run(capsys, config_file_list):
    """Test that the CLI can successfully run with example data.

    Note that this does not currently test the various CLI options independently. We
    could do with a fast running minimal test or a mocker to do that.
    """

    from virtual_ecosystem.core.logger import remove_file_logger
    from virtual_ecosystem.entry_points import ve_run_cli

    with TemporaryDirectory() as tempdir:
        try:
            # Install the example directory to run it - tested above - and consume
            # the resulting stdout
            ve_run_cli(args_list=["--install-example", tempdir])
            _ = capsys.readouterr()

            example_dir = Path(tempdir) / "ve_example"
            configs = [
                example_dir / "config" / filename for filename in config_file_list
            ]
            outdir = example_dir / "out"
            outdir.mkdir(exist_ok=True)
            logfile = outdir / "ve_example.log"
            ve_run_cli(
                args_list=[
                    *(str(config) for config in configs),
                    "--outpath",
                    str(outdir),
                    "--logfile",
                    str(logfile),
                    "--config",
                    "core.debug.truncate_run_at_update=1",
                ]
            )

            # Test the requested --progress output ends as expected
            captured = capsys.readouterr()
            expected = "Virtual Ecosystem run complete.\n"
            assert captured.out.endswith(expected)

            # Check the logfile has been populated as expected
            assert logfile.exists()
            with open(logfile) as logfile_io:
                contents = logfile_io.readlines()
                assert "Virtual Ecosystem model run completed!" in contents[-1]

        except Exception as excep:
            # If the code above fails then tidy up the logger to restore normal
            # stream logging rather than leaving all other tests logging to the file
            # and then fail the test.
            remove_file_logger()

            # If this test fails on the CI runners, save the log to a known temporary
            # directory so that it can be saved as an artefact.
            if os.environ.get("CI") == "true" and logfile.exists():
                temp_log = Path(os.environ.get("RUNNER_TEMP")) / "log_file.log"
                temp_log.write_text(logfile.read_text())

            pytest.fail(reason=str(excep))


@pytest.mark.integration
@pytest.mark.parametrize(
    argnames="abiotic_simple",
    argvalues=(
        pytest.param(False, id="abiotic"),
        pytest.param(True, id="abiotic_simple"),
    ),
)
def test_ve_run_full(capsys, config_file_list, abiotic_simple):
    """Integration test that CLI can run for prolonged simulation without errors."""

    from virtual_ecosystem.core.logger import remove_file_logger
    from virtual_ecosystem.entry_points import ve_run_cli

    # Replace path to abiotic config with path to abiotic_simple config, to run that
    # model instead
    if abiotic_simple:
        config_files = [
            "abiotic_simple_config.toml" if f == "abiotic_config.toml" else f
            for f in config_file_list
        ]
    else:
        config_files = config_file_list

    with TemporaryDirectory() as tempdir:
        try:
            # Install the example directory to run it - tested above - and consume
            # the resulting stdout
            ve_run_cli(args_list=["--install-example", tempdir])
            _ = capsys.readouterr()

            example_dir = Path(tempdir) / "ve_example"
            configs = [example_dir / "config" / filename for filename in config_files]
            outdir = example_dir / "out"
            outdir.mkdir(exist_ok=True)
            logfile = outdir / "ve_example.log"
            ve_run_cli(
                args_list=[
                    *(str(config) for config in configs),
                    "--outpath",
                    str(outdir),
                    "--logfile",
                    str(logfile),
                ]
            )

            # Test the requested --progress output ends as expected
            captured = capsys.readouterr()
            expected = "Virtual Ecosystem run complete.\n"
            assert captured.out.endswith(expected)

            # Check the logfile has been populated as expected
            assert logfile.exists()
            with open(logfile) as logfile_io:
                contents = logfile_io.readlines()
                assert "Virtual Ecosystem model run completed!" in contents[-1]

        except Exception as excep:
            # If the code above fails then tidy up the logger to restore normal
            # stream logging rather than leaving all other tests logging to the file
            # and then fail the test.
            remove_file_logger()

            # If this test fails on the CI runners, save the log to a known temporary
            # directory so that it can be saved as an artefact.
            if os.environ.get("CI") == "true" and logfile.exists():
                temp_log = Path(os.environ.get("RUNNER_TEMP")) / "log_file.log"
                temp_log.write_text(logfile.read_text())

            pytest.fail(reason=str(excep))


@pytest.mark.parametrize(
    argnames="verbosity_flags, output_length",
    argvalues=(
        pytest.param("-qqq", 0, id="silent"),
        pytest.param("-qq", 3, id="minimal"),
        pytest.param("-q", 10, id="staged"),
        pytest.param(None, 12, id="full"),
    ),
)
def test_ve_run_verbosity(capsys, tmp_path, verbosity_flags, output_length):
    """Test that the CLI verbosity is set correctly."""

    from virtual_ecosystem.core.logger import remove_file_logger
    from virtual_ecosystem.core.registry import MODULE_REGISTRY
    from virtual_ecosystem.entry_points import ve_run_cli

    # Need to remove any existing file log attached to LOGGER and clear the variables
    # and modules registries.

    # This is not a pleasant feature of the current UI - the persistence of variable and
    # module states between tests is extremely confusing and makes tests really hard to
    # debug.

    remove_file_logger()
    MODULE_REGISTRY.clear()

    config_file = tmp_path / "config.toml"
    with open(config_file, "w") as cfg:
        cfg.write(
            """
[core.data_output_options]
save_initial_state = false
save_continuous_data = false
save_final_state = false
save_merged_config = false
[core.data]
variable = []
[testing]
"""
        )

    args_list = [
        str(config_file),
        "--outpath",
        str(tmp_path),
        "--logfile",
        str(tmp_path / "log.log"),
    ]
    if verbosity_flags:
        args_list.append(verbosity_flags)

    ve_run_cli(args_list=args_list)

    # Test the requested --progress output ends as expected
    out, err = capsys.readouterr()

    assert len(err.splitlines()) == 0
    output = [v for v in out.splitlines() if v]  # drop blank lines
    assert len(output) == output_length


@pytest.mark.parametrize(
    argnames="cli_config, expected_called_value",
    argvalues=(
        pytest.param([], {}, id="no cli config"),
        pytest.param(
            ["--config", "core.grid.cell_nx=6"],
            {"core": {"grid": {"cell_nx": 6}}},
            id="single cli config",
        ),
        pytest.param(
            [
                "--config",
                "core.grid.cell_nx=6",
                "--config",
                "plants.constants.value=0.1",
            ],
            {"core": {"grid": {"cell_nx": 6}}, "plants": {"constants": {"value": 0.1}}},
            id="multiple cli config",
        ),
    ),
)
def test_ve_run_cli_config(tmp_path, mocker, cli_config, expected_called_value):
    """Test that the CLI can successfully override configuration.

    This test just checks that a command line config option is successfully passed
    through from the ve_run_cli entry point into the actual call to ve_run. There is no
    testing of the handling of the input by ve_run, which is mocked out to keep the test
    fast and focussed.

    Actual testing of the integration of CLI config data into the configuration is here:
    tests/core/test_configuration_builder.py::test_ConfigurationLoader_load_configuration_data
    """

    from virtual_ecosystem.entry_points import ve_run_cli

    # Don't actually _run_ the ve_run function
    run_function = mocker.patch("virtual_ecosystem.entry_points.ve_run")

    # Call the CLI interface with a temporary empty file and the parameterised CLI
    # config  details
    ve_run_cli(args_list=[str(tmp_path), *cli_config])

    # Retrieve what would have been passed to ve_run and check it matches expectations.
    called_value = run_function.call_args.kwargs["cli_config"]
    assert called_value == expected_called_value


def test_ve_run_cli_cli_paths(tmp_path):
    """Test that cli_paths are passed down to validation.

    This test checks that a data path substitution option is successfully passed
    through from the ve_run_cli entry point into the actual call to ve_run.
    """

    from virtual_ecosystem.core.exceptions import ConfigurationError
    from virtual_ecosystem.entry_points import ve_run_cli

    config = tmp_path / "config.toml"
    p1 = tmp_path / "data_one.nc"
    p1.touch()

    config.write_text(
        f"""[[core.data.variable]]
  file_path = "{p1}"
  var_name = "temp"
[[core.data.variable]]
  file_path = "$MARKER_ONE"
  var_name = "prec"
"""
    )

    # Fails with undefined MARKER
    with pytest.raises(ConfigurationError):
        ve_run_cli(args_list=[str(config), "--validate-config-only"])

    # Works with MARKER defined via env.
    os.environ["MARKER_ONE"] = str(p1)
    ve_run_cli(args_list=[str(config), "--validate-config-only"])

    # Fails with duplicate definition via env and CLI
    with pytest.raises(ConfigurationError):
        ve_run_cli(
            args_list=[str(config), "--validate-config-only", f"-pMARKER_ONE={p1}"]
        )

    # Works with marker defined only via CLI
    del os.environ["MARKER_ONE"]
    ve_run_cli(
        args_list=[str(config), "--validate-config-only", "-p", f"MARKER_ONE={p1}"]
    )

    # Add another variable
    config.write_text(
        """[[core.data.variable]]
  file_path = "$MARKER_TWO"
  var_name = "snow"
"""
    )

    # Check multiple paths
    ve_run_cli(
        args_list=[
            str(config),
            "--validate-config-only",
            "-p",
            f"MARKER_ONE={p1}",
            "-p",
            f"MARKER_TWO={p1}",
        ]
    )
