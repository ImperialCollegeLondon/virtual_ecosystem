"""An integration test for the VR command-line interface."""
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from tempfile import TemporaryDirectory


def test_vr_run_install_example(capsys):
    """Test that the CLI can successfully run with example data."""
    from virtual_rainforest.entry_points import vr_run_cli

    with TemporaryDirectory() as tempdir:
        with does_not_raise():
            vr_run_cli(args_list=["--install_example", tempdir])

            captured = capsys.readouterr()
            expected = "Example directory created at:"
            assert captured.out.startswith(expected)


def test_vr_run(capsys):
    """Test that the CLI can successfully run with example data."""
    from virtual_rainforest.entry_points import vr_run_cli

    with TemporaryDirectory() as tempdir:
        # Install the example directory to run it - tested above
        vr_run_cli(args_list=["--install_example", tempdir])

        with does_not_raise():
            example_dir = str(Path(tempdir) / "vr_example")
            vr_run_cli(args_list=[example_dir, "--outpath", example_dir])

            captured = capsys.readouterr()
            expected = "Example directory created at:"
            assert captured.out.startswith(expected)
