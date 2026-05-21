"""Unit tests for ve_run_cli() with profiling included."""

import cProfile
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.mark.profiling
def test_ve_run_with_profiling(capsys):
    """Runs ve_run_cli() with profiling.

    This test is included to make it easy for developers to run ve_run_cli() with
    profiling enabled. The test is skipped by default as it is not meant to be a unit
    test but rather a convenient way to run the code with profiling enabled.

    The `tool.pytest.ini_options` settings `pyproject.toml` configure pytest to ignore
    tests marked with `profiling`. Run this test to generate profiling outputs from the
    command line using `pytest -m profiling` and then use `snakeviz ve_run_profile.prof`
    to explore the results.
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
            config_dir = example_dir / "config"
            outdir = example_dir / "out"
            outdir.mkdir(exist_ok=True)
            logfile = outdir / "logfile.log"

            pr = cProfile.Profile()
            pr.enable()

            ve_run_cli(
                args_list=[
                    str(config_dir / "data_config.toml"),
                    str(config_dir / "abiotic_config.toml"),
                    str(config_dir / "animal_config.toml"),
                    str(config_dir / "hydrology_config.toml"),
                    str(config_dir / "litter_config.toml"),
                    str(config_dir / "plant_config.toml"),
                    str(config_dir / "soil_config.toml"),
                    "--outpath",
                    str(outdir),
                    "--logfile",
                    str(logfile),
                    "--config",
                    "core.debug.truncate_run_at_update=1",
                ]
            )

            pr.disable()
            pr.dump_stats("ve_run_profile.prof")
        finally:
            # Always tidy up the logger to restore normal stream logging rather
            # than leaving other tests logging to the file. Any original
            # exception will still be re-raised by the test framework.
            remove_file_logger()
