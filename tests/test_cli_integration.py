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


def test_ve_run(capsys):
    """Test that the CLI can successfully run with example data.

    Note that this does not currently test the various CLI options independently. We
    could do with a fast running minimal test or a mocker to do that.
    """

    # import virtual_ecosystem.core  #F401
    from virtual_ecosystem.core.logger import remove_file_logger
    from virtual_ecosystem.entry_points import ve_run_cli

    with TemporaryDirectory() as tempdir:
        try:
            # Install the example directory to run it - tested above - and consume the
            # resulting stdout
            ve_run_cli(args_list=["--install-example", tempdir])
            _ = capsys.readouterr()

            example_dir = Path(tempdir) / "ve_example"
            configs = example_dir / "config"
            outdir = example_dir / "out"
            logfile = outdir / "ve_example.log"
            ve_run_cli(
                args_list=[
                    str(configs),
                    "--outpath",
                    str(outdir),
                    "--logfile",
                    str(logfile),
                    "--progress",
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
            # If the code above fails then tidy up the logger to restore normal stream
            # logging rather than leaving all other tests logging to the file and then
            # fail the test.
            remove_file_logger()
            pytest.fail(msg=str(excep))
