"""An integration test for the VR command-line interface."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def test_vr_run_install_example(capsys):
    """Test that the CLI can successfully run with example data."""
    from virtual_rainforest.entry_points import vr_run_cli

    with TemporaryDirectory() as tempdir:
        vr_run_cli(args_list=["--install-example", tempdir])

        captured = capsys.readouterr()
        expected = "Example directory created at:"
        assert captured.out.startswith(expected)


def test_vr_run(capsys):
    """Test that the CLI can successfully run with example data."""
    # import virtual_rainforest.core  # noqa #F401
    from virtual_rainforest.core.logger import remove_file_logger
    from virtual_rainforest.entry_points import vr_run_cli

    with TemporaryDirectory() as tempdir:
        try:
            # Install the example directory to run it - tested above - and consume the
            # resulting stdout
            vr_run_cli(args_list=["--install-example", tempdir])
            _ = capsys.readouterr()

            example_dir = Path(tempdir) / "vr_example"
            configs = example_dir / "config"
            outdir = example_dir / "out"
            logfile = outdir / "vr_example.log"
            vr_run_cli(
                args_list=[
                    str(configs),
                    "--outpath",
                    str(outdir),
                    "--logfile",
                    str(logfile),
                ]
            )

            # Test the command line output is as expected
            captured = capsys.readouterr()
            expected = "VR run complete."
            assert captured.out.startswith(expected)

            # Check the logfile has been populated as expected
            assert logfile.exists()
            with open(logfile) as logfile_io:
                contents = logfile_io.readlines()
                assert "Virtual rainforest model run completed!" in contents[-1]

        except Exception as excep:
            # If the code above fails then tidy up the logger to restore normal stream
            # logging rather than leaving all other tests logging to the file and then
            # fail the test.
            remove_file_logger()
            pytest.fail(msg=str(excep))
