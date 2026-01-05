"""An integration test for the VR command-line interface."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def test_ve_run_install_example(capsys):
    """Test that the CLI can successfully run with example data."""
    from virtual_ecosystem.entry_points import ve_run_cli

    with TemporaryDirectory() as tempdir:
        ve_run_cli(args_list=["--install-example", tempdir])

        captured = capsys.readouterr()
        expected = "Example directory created at:"
        assert captured.out.startswith(expected)


@pytest.mark.slow
def test_ve_run(capsys):
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
            configs = example_dir / "config"
            outdir = example_dir / "out"
            outdir.mkdir(exist_ok=True)
            logfile = outdir / "ve_example.log"
            ve_run_cli(
                args_list=[
                    str(configs),
                    "--outpath",
                    str(outdir),
                    "--logfile",
                    str(logfile),
                    "--config",
                    'core.timing.run_length="2 months"',
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
            pytest.fail(reason=str(excep))


@pytest.mark.parametrize(
    argnames="verbosity_flags, output_length",
    argvalues=(
        pytest.param("-qqq", 0, id="silent"),
        pytest.param("-qq", 3, id="minimal"),
        pytest.param("-q", 9, id="staged"),
        pytest.param(None, 11, id="full"),
    ),
)
def test_ve_run_verbosity(capsys, tmp_path, verbosity_flags, output_length):
    """Test that the CLI verbosity is set correctly."""

    from virtual_ecosystem.core.logger import remove_file_logger
    from virtual_ecosystem.core.registry import MODULE_REGISTRY
    from virtual_ecosystem.core.variables import KNOWN_VARIABLES, RUN_VARIABLES_REGISTRY
    from virtual_ecosystem.entry_points import ve_run_cli

    # Need to remove any existing file log attached to LOGGER and clear the variables
    # and modules registries.

    # This is not a pleasant feature of the current UI - the persistence of variable and
    # module states between tests is extremely confusing and makes tests really hard to
    # debug.

    remove_file_logger()
    KNOWN_VARIABLES.clear()
    RUN_VARIABLES_REGISTRY.clear()
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
            id="cli config",
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
