"""Test module for entry_points.py.

This module check that the model entry points exist and function as expected
"""

import os
import subprocess

import virtual_rainforest as vr


def test_entry_point_existence():
    """Check that the entry points exist."""

    exit_status = os.system("vr_run --help")
    assert exit_status == 0


def test_version():
    """Check --version information is displayed correctly."""
    expected_version = vr.__version__
    result = subprocess.run(["vr_run", "--version"], capture_output=True, text=True)

    assert result.stdout == f"vr_run {expected_version}{os.linesep}"
