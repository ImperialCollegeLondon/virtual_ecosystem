"""Tests for the virtual_ecosystem.core.variables module."""

import sys

import pytest

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # noqa: F401


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


@pytest.fixture
def axis_validators():
    """Fixture to reset the axis validators after each test."""
    import virtual_ecosystem.core.axes as axes

    vars_bkp = axes.AXIS_VALIDATORS.copy()
    axes.AXIS_VALIDATORS.clear()
    yield axes.AXIS_VALIDATORS
    axes.AXIS_VALIDATORS.clear()
    axes.AXIS_VALIDATORS.update(vars_bkp)


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


def test_discover_models(known_variables):
    """Test the discover_all_variables_usage function."""
    from virtual_ecosystem.core import base_model, variables

    models = variables._discover_models()
    assert len(models) > 0
    assert all(issubclass(x, base_model.BaseModel) for x in models)


def test_output_known_variables(known_variables, mocker, tmpdir):
    """Test the output_known_variables function."""
    from virtual_ecosystem.core import variables

    mocker.patch("virtual_ecosystem.core.variables.register_all_variables")
    mocker.patch("virtual_ecosystem.core.variables._discover_models")
    mocker.patch("virtual_ecosystem.core.variables._collect_initialise_by_vars")
    mocker.patch("virtual_ecosystem.core.variables._collect_required_init_vars")
    mocker.patch("virtual_ecosystem.core.variables._collect_updated_by_vars")
    mocker.patch("virtual_ecosystem.core.variables._collect_required_update_vars")

    variables._discover_models.return_value = []

    variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )
    path = tmpdir / "variables.rst"

    variables.output_known_variables(path)

    assert "test_var" in variables.RUN_VARIABLES_REGISTRY
    variables.register_all_variables.assert_called_once()
    variables._discover_models.assert_called_once()
    variables._collect_initialise_by_vars.assert_called_once_with([])
    variables._collect_required_init_vars.assert_called_once_with([])
    variables._collect_updated_by_vars.assert_called_once_with([])
    variables._collect_required_update_vars.assert_called_once_with([])
    assert path.exists()

    with open(path) as f:
        assert "test_var" in f.read()


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

    variables._collect_updated_by_vars([TestModel])
    assert caplog.records[-1].levelname == "WARNING"
    assert "is already updated" in caplog.records[-1].message
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


def test_collect_required_init_vars(known_variables, run_variables):
    """Test the _collect_required_init_vars function."""
    from virtual_ecosystem.core import variables

    class TestModel:
        model_name = "TestModel"
        required_init_vars = (("test_var", tuple()),)

    with pytest.raises(ValueError, match="not in the known variables registry."):
        variables._collect_required_init_vars([TestModel])

    var = variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )

    with pytest.raises(ValueError, match="is not initialised"):
        variables._collect_required_init_vars([TestModel])

    variables.RUN_VARIABLES_REGISTRY["test_var"] = var
    variables.RUN_VARIABLES_REGISTRY["test_var"].initialised_by = "AnotherModel"

    variables._collect_required_init_vars([TestModel])
    assert variables.RUN_VARIABLES_REGISTRY["test_var"].required_init_by == [
        "TestModel"
    ]


def test_collect_initial_data_vars(known_variables, run_variables):
    """Test the _collect_initial_data_vars function."""
    from virtual_ecosystem.core import variables

    with pytest.raises(ValueError, match="defined in data object is not known"):
        variables._collect_initial_data_vars(["test_var"])

    variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )

    variables._collect_initial_data_vars(["test_var"])

    assert "test_var" in variables.RUN_VARIABLES_REGISTRY
    assert variables.RUN_VARIABLES_REGISTRY["test_var"].initialised_by == "data"

    with pytest.raises(ValueError, match="already in registry"):
        variables._collect_initial_data_vars(["test_var"])


def test_setup_variables(mocker):
    """Test the _collect_initial_data_vars function."""
    from virtual_ecosystem.core import variables

    mocker.patch("virtual_ecosystem.core.variables._collect_initial_data_vars")
    mocker.patch("virtual_ecosystem.core.variables._collect_initialise_by_vars")
    mocker.patch("virtual_ecosystem.core.variables._collect_required_init_vars")
    mocker.patch("virtual_ecosystem.core.variables._collect_updated_by_vars")
    mocker.patch("virtual_ecosystem.core.variables._collect_required_update_vars")

    class TestModel:
        pass

    variables.setup_variables([TestModel], ["test_var"])

    variables._collect_initial_data_vars.assert_called_once_with(["test_var"])
    variables._collect_initialise_by_vars.assert_called_once_with([TestModel])
    variables._collect_required_init_vars.assert_called_once_with([TestModel])
    variables._collect_updated_by_vars.assert_called_once_with([TestModel])
    variables._collect_required_update_vars.assert_called_once_with([TestModel])


def test_verify_variables_axis(known_variables, run_variables, axis_validators):
    """Test the verify_variables_axis function."""
    from virtual_ecosystem.core import variables

    var = variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )
    variables.RUN_VARIABLES_REGISTRY["test_var"] = var

    with pytest.raises(ValueError, match="uses unknown axis: x,y,z"):
        variables.verify_variables_axis()

    axis_validators["x"] = lambda x: x

    with pytest.raises(ValueError, match="uses unknown axis: y,z"):
        variables.verify_variables_axis()

    axis_validators["y"] = lambda x: x
    axis_validators["z"] = lambda x: x

    variables.verify_variables_axis()


def test_get_variable(known_variables, run_variables):
    """Test the get_variable function."""
    from virtual_ecosystem.core import variables

    with pytest.raises(KeyError, match="not a known variable."):
        variables.get_variable("test_var")

    var = variables.Variable(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("x", "y", "z"),
    )

    with pytest.raises(
        KeyError, match="not initialised by any model or provided as input data"
    ):
        variables.get_variable("test_var")

    variables.RUN_VARIABLES_REGISTRY["test_var"] = var
    result = variables.get_variable("test_var")
    assert result == var


def test_to_camel_case():
    """Test the to_camel_case function."""
    from virtual_ecosystem.core.variables import to_camel_case

    assert to_camel_case("abiotic") == "Abiotic"
    assert to_camel_case("abiotic_simple") == "AbioticSimple"
    assert to_camel_case("abiotic_super_simple") == "AbioticSuperSimple"


def test_format_variables_list():
    """Test the _format_varriables_list function."""
    from virtual_ecosystem.core.variables import _format_varriables_list

    vars = {
        "var1": {
            "name": "Variable 1",
            "description": "Description 1",
            "unit": "m",
            "variable_type": "float",
            "axis": ("x", "y", "z"),
        },
        "var2": {
            "name": "Variable 2",
            "description": "Description 2",
            "unit": "s",
            "variable_type": "int",
            "axis": ("x", "y"),
        },
    }

    expected_output = """1- Variable 1
=============

=============  ===============
name           Variable 1
description    Description 1
unit           m
variable_type  float
axis           ('x', 'y', 'z')
=============  ===============

2- Variable 2
=============

=============  =============
name           Variable 2
description    Description 2
unit           s
variable_type  int
axis           ('x', 'y')
=============  =============
"""

    assert _format_varriables_list(vars) == expected_output
