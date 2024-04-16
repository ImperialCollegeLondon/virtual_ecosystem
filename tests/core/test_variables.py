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


@pytest.fixture
def run_variables():
    """Fixture to reset the run variables after each test."""
    from virtual_ecosystem.core import variables

    vars_bkp = variables.RUN_VARIABLES_REGISTRY.copy()
    variables.RUN_VARIABLES_REGISTRY.clear()
    yield variables.RUN_VARIABLES_REGISTRY
    variables.RUN_VARIABLES_REGISTRY.clear()
    variables.RUN_VARIABLES_REGISTRY.update(vars_bkp)


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


def test_collect_initialise_by_vars(known_variables, run_variables):
    """Test the _collect_initialise_by_vars function."""
    from virtual_ecosystem.core import variables

    class TestModel:
        model_name = "TestModel"
        vars_initialised = ("test_var",)

    with pytest.raises(ValueError, match="not in the known variables registry."):
        variables._collect_initialise_by_vars([TestModel])

    variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )

    variables._collect_initialise_by_vars([TestModel])

    assert "test_var" in variables.RUN_VARIABLES_REGISTRY
    assert variables.RUN_VARIABLES_REGISTRY["test_var"].initialised_by == "TestModel"

    with pytest.raises(ValueError, match="already in registry"):
        variables._collect_initialise_by_vars([TestModel])


def test_collect_updated_by_vars(known_variables, run_variables, caplog):
    """Test the _collect_updated_by_vars function."""
    from virtual_ecosystem.core import variables

    class TestModel:
        model_name = "TestModel"
        vars_updated = ("test_var",)

    with pytest.raises(ValueError, match="not in the known variables registry."):
        variables._collect_updated_by_vars([TestModel])

    var = variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )

    with pytest.raises(ValueError, match="is not initialised"):
        variables._collect_updated_by_vars([TestModel])

    variables.RUN_VARIABLES_REGISTRY["test_var"] = var
    variables.RUN_VARIABLES_REGISTRY["test_var"].initialised_by = "AnotherModel"

    variables._collect_updated_by_vars([TestModel])
    assert variables.RUN_VARIABLES_REGISTRY["test_var"].updated_by == ["TestModel"]

    variables._collect_initialise_by_vars([TestModel])
    assert caplog.records[-1].levelname == "WARNING"
    assert "is already updated" in caplog.get_records[-1].message
    assert variables.RUN_VARIABLES_REGISTRY["test_var"].updated_by == [
        "TestModel",
        "TestModel",
    ]


def test_collect_required_update_vars(known_variables, run_variables):
    """Test the _collect_required_update_vars function."""
    from virtual_ecosystem.core import variables

    class TestModel:
        model_name = "TestModel"
        required_update_vars = ("test_var",)

    with pytest.raises(ValueError, match="not in the known variables registry."):
        variables._collect_required_update_vars([TestModel])

    var = variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )

    with pytest.raises(ValueError, match="is not initialised"):
        variables._collect_required_update_vars([TestModel])

    variables.RUN_VARIABLES_REGISTRY["test_var"] = var
    variables.RUN_VARIABLES_REGISTRY["test_var"].initialised_by = "AnotherModel"

    variables._collect_required_update_vars([TestModel])
    assert variables.RUN_VARIABLES_REGISTRY["test_var"].required_update_by == [
        "TestModel"
    ]
