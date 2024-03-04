"""Test module for entry_points.py.

This module check that the model entry points exist and function as expected
"""

import os
import shutil
import subprocess

import virtual_ecosystem as ve


def test_entry_point_existence():
    """Check that the entry points exist."""

    exit_status = os.system("ve_run --help")
    assert exit_status == 0


def test_version():
    """Check --version information is displayed correctly."""
    expected_version = ve.__version__
    result = subprocess.run(
        [shutil.which("ve_run"), "--version"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert result.stdout == f"ve_run {expected_version}\n"
