"""An integration test for the VR command-line interface."""
from pathlib import Path
from tempfile import TemporaryDirectory


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
    from virtual_rainforest.entry_points import vr_run_cli

    with TemporaryDirectory() as tempdir:
        # Install the example directory to run it - tested above - and consume the
        # resulting stdout
        vr_run_cli(args_list=["--install-example", tempdir])
        _ = capsys.readouterr()

        example_dir = Path(tempdir) / "vr_example"
        vr_run_cli(
            args_list=[
                str(example_dir),
                "--outpath",
                str(example_dir),
                # "--logfile",
                # str(example_dir / "vr_example.log"),
            ]
        )

        captured = capsys.readouterr()
        expected = "VR run complete."
        assert captured.out.startswith(expected)
