"""Test module for entry_points.py.

This module check that the model entry points exist and function as expected
"""

import shutil
import subprocess
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest

import virtual_ecosystem as ve


def test_entry_point_existence():
    """Check that the entry points exist."""

    result = subprocess.run(
        [shutil.which("ve_run"), "--help"], capture_output=True, text=True
    )

    assert result.returncode == 0


def test_version():
    """Check --version information is displayed correctly."""
    expected_version = ve.__version__
    result = subprocess.run(
        [shutil.which("ve_run"), "--version"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert result.stdout == f"ve_run {expected_version}\n"


@pytest.mark.parametrize(
    argnames="inputs, outcome, excep_message",
    argvalues=(
        pytest.param(
            ["NO_EQUALS"],
            pytest.raises(ValueError),
            "Incorrect syntax",
            id="bad_syntax",
        ),
        pytest.param(
            ["ONE_EQUALS=TMPDIR/file_one.nc"],
            does_not_raise(),
            None,
            id="single_path_ok",
        ),
        pytest.param(
            ["TWO_EQUALS=TMPDIR/file_=_two.nc"],
            does_not_raise(),
            None,
            id="single_path_with_equals_ok",
        ),
        pytest.param(
            ["ONE_EQUALS=TMPDIR/file_ohno.nc"],
            pytest.raises(ValueError),
            "does not point to existing",
            id="single_path_bad_file",
        ),
        pytest.param(
            [
                "ONE_EQUALS=TMPDIR/file_one.nc",
                "ONE_EQUALS=TMPDIR/file_one.nc",
            ],
            does_not_raise(),
            None,
            id="two_paths_ok",
        ),
    ),
)
def test__parse_cli_paths(tmpdir, inputs, outcome, excep_message):
    """Test the path parsing function for the command line."""

    from virtual_ecosystem.entry_points import _parse_cli_paths

    # Create some temporary files for checking file
    (Path(tmpdir) / "file_one.nc").touch()
    (Path(tmpdir) / "file_=_two.nc").touch()

    # Sub in the tmpdir
    inputs = [i.replace("TMPDIR", str(tmpdir)) for i in inputs]

    with outcome as excep:
        _parse_cli_paths(inputs)

    if excep:
        assert excep_message in str(excep.value)
