"""Tests for the virtual_ecosystem.core.variables module."""

import sys
from dataclasses import asdict

import pytest

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@pytest.fixture
def known_variables():
    """Fixture to reset the known variables after each test."""
    from virtual_ecosystem.core import variables

    vars_bkp = variables.KNOWN_VARIABLES.copy()
    variables.KNOWN_VARIABLES.clear()
    yield variables.KNOWN_VARIABLES
    variables.KNOWN_VARIABLES.clear()
    variables.KNOWN_VARIABLES.update(vars_bkp)


def test_register_variable(known_variables):
    """Test the register_variable function."""
    from virtual_ecosystem.core import variables

    var = variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )
    assert "test_var" in variables.KNOWN_VARIABLES
    assert variables.KNOWN_VARIABLES["test_var"] == var


def test_register_variable_duplicate(known_variables):
    """Test the register_variable function with a duplicate variable."""
    from virtual_ecosystem.core import variables

    variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )
    with pytest.raises(ValueError):
        variables.Variable(
            name="test_var",
            description="Test variable",
            unit="m",
            variable_type="float",
            axis=("x", "y", "z"),
        )


def test_register_all_variables(known_variables):
    """Test the register_all_variables function."""
    from virtual_ecosystem.core import variables

    assert len(variables.KNOWN_VARIABLES) == 0
    variables.register_all_variables()
    assert len(variables.KNOWN_VARIABLES) > 0


def test_discover_all_variables_usage(known_variables, mocker):
    """Test the discover_all_variables_usage function."""
    from virtual_ecosystem.core import base_model, variables

    mocker.patch("virtual_ecosystem.core.variables.setup_variables")
    variables._discover_all_variables_usage()
    variables.setup_variables.assert_called_once()
    args = variables.setup_variables.call_args[0]
    assert len(args[0]) > 0
    assert all(issubclass(x, base_model.BaseModel) for x in args[0])
    assert args[1] == []


def test_output_known_variables(known_variables, mocker, tmpdir):
    """Test the output_known_variables function."""
    from virtual_ecosystem.core import variables

    mocker.patch("virtual_ecosystem.core.variables.register_all_variables")
    mocker.patch("virtual_ecosystem.core.variables._discover_all_variables_usage")

    var = variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )
    path = tmpdir / "variables.json"

    variables.output_known_variables(path)

    variables.register_all_variables.assert_called_once()
    variables._discover_all_variables_usage.assert_called_once()
    assert path.exists()
    with open(path, "rb") as f:
        data = tomllib.load(f)

    assert len(data) == 1
    var.axis = list(var.axis)
    assert data["test_var"] == asdict(var)
