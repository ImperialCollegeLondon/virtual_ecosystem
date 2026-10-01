"""Tests for the virtual_ecosystem.core.variables module."""

from contextlib import nullcontext as does_not_raise
from importlib import resources

import pytest


@pytest.fixture
def fixture_variable():
    """Fixture variable for use in testing."""
    from virtual_ecosystem.core.variables import VariableMetadata

    return VariableMetadata(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("spatial",),
    )


@pytest.fixture
def fixture_test_model():
    """Provides a template model that can be updated to test variable checking."""

    class TestModel:
        model_name = "TestModel"
        vars_required_for_init = tuple()
        vars_populated_by_init = tuple()
        vars_required_for_update = tuple()
        vars_populated_by_first_update = tuple()
        vars_updated = tuple()

    return TestModel


@pytest.mark.parametrize(
    argnames="variable_definition,outcome,exc_text",
    argvalues=(
        pytest.param(
            dict(
                name="test_var",
                description="Test variable",
                unit="m",
                variable_type="float",
                axis=("spatial",),
            ),
            does_not_raise(),
            None,
            id="good",
        ),
        pytest.param(
            dict(
                name="test_var",
                unit="m",
                variable_type="float",
                axis=("spatial",),
            ),
            pytest.raises(ValueError),
            "Field required",
            id="missing_field",
        ),
        pytest.param(
            dict(
                name="test_var",
                description="Test variable",
                unit="m",
                variable_type="float",
                axis=("spatial", "spatial"),
            ),
            pytest.raises(ValueError),
            "Axis values not unique in variable: test_var",
            id="repeated axis",
        ),
        pytest.param(
            dict(
                name="test_var",
                description="Test variable",
                unit="m",
                variable_type="float",
                axis=("cellid",),
            ),
            pytest.raises(ValueError),
            "Variable test_var uses unknown axes:",
            id="unknown axis",
        ),
    ),
)
def test_VariableMetadata(variable_definition, outcome, exc_text):
    """Test the VariableMetadata class validation."""

    from virtual_ecosystem.core.variables import VariableMetadata

    with outcome as out:
        _ = VariableMetadata(**variable_definition)
        return

    assert exc_text in str(out.value)


def test_VariableMetadata_related_models():
    """Test the VariablesFile.related_models property."""

    from virtual_ecosystem.core.variables import VariableMetadata

    var = VariableMetadata(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("spatial",),
    )

    # Check that the related models are empty when no data is provided
    assert var.related_models == set()

    # Check that the related models are correctly returned
    var.vars_populated_by_init = ["model1"]
    var.vars_populated_by_first_update = ["model2"]
    var.vars_required_by_init = ["model3"]
    var.vars_required_by_update = ["model4", "model5"]
    var.vars_updated = ["model5"]

    assert var.related_models == set(["model1", "model2", "model3", "model4", "model5"])

    # Test that data is not included in the related models
    var.vars_updated = ["data"]
    assert var.related_models == set(["model1", "model2", "model3", "model4", "model5"])


def test_VariablesFile():
    """Test the VariablesFile class validation."""

    from virtual_ecosystem.core.variables import VariableMetadata, VariablesFile

    v1 = VariableMetadata(
        name="test_var",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("spatial",),
    )

    v2 = VariableMetadata(
        name="test_var2",
        description="Test variable",
        unit="m",
        variable_type="float",
        axis=("spatial",),
    )

    with does_not_raise():
        _ = VariablesFile(variable=[v1, v2])

    with pytest.raises(ValueError) as out:
        _ = VariablesFile(variable=[v1, v1, v2])

    assert "Duplicate variable names in variables file" in str(out.value)


@pytest.mark.parametrize(argnames="filepath_is_none", argvalues=(True, False))
def test_load_known_variables(filepath_is_none):
    """Test the load_known_variables function."""
    from virtual_ecosystem.core.variables import (
        VariableMetadata,
        load_known_variables,
    )

    filepath = (
        None
        if filepath_is_none
        else str(resources.files("virtual_ecosystem") / "data_variables.toml")
    )
    variables = load_known_variables(variable_file=filepath)

    assert len(variables) > 0

    for ky, var in variables.items():
        assert isinstance(ky, str)
        assert isinstance(var, VariableMetadata)


def test_check_model_variables_are_known(fixture_variable, fixture_test_model):
    """Test the _collect_vars_populated_by_init function."""
    from virtual_ecosystem.core.variables import _check_model_variables_are_known

    fixture_test_model.vars_populated_by_init = ("test_var",)

    known_variables = {}

    with pytest.raises(
        ValueError,
        match="Unknown variables in the definition of the following models, check log: "
        + "TestModel",
    ):
        _check_model_variables_are_known(
            [fixture_test_model], known_variables=known_variables
        )

    known_variables = {"test_var": fixture_variable}

    with does_not_raise():
        _check_model_variables_are_known(
            [fixture_test_model], known_variables=known_variables
        )


def test_collect_vars_populated_by_init(fixture_variable, fixture_test_model):
    """Test the _collect_vars_populated_by_init function."""
    from virtual_ecosystem.core.variables import _collect_vars_populated_by_init

    fixture_test_model.vars_populated_by_init = ("test_var",)

    runtime_variables = {}
    known_variables = {"test_var": fixture_variable}

    _collect_vars_populated_by_init(
        [fixture_test_model],
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )

    assert "test_var" in runtime_variables
    assert runtime_variables["test_var"].vars_populated_by_init == ["TestModel"]

    # Rerunning should detect that there is already an entry in vars_populated_by_init
    with pytest.raises(ValueError, match="already initialised"):
        _collect_vars_populated_by_init(
            [fixture_test_model],
            runtime_variables=runtime_variables,
            known_variables=known_variables,
        )


def test_collect_vars_populated_by_first_update(fixture_variable, fixture_test_model):
    """Test the _collect_vars_populated_by_first_update function."""
    from virtual_ecosystem.core.variables import (
        _collect_vars_populated_by_first_update,
        _collect_vars_populated_by_init,
    )

    fixture_test_model.vars_populated_by_first_update = ("test_var",)
    fixture_test_model.vars_populated_by_init = ("test_var",)

    runtime_variables = {}
    known_variables = {"test_var": fixture_variable}

    # Running the collect should add the variable to the runtime variables
    _collect_vars_populated_by_first_update(
        [fixture_test_model],
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )

    assert "test_var" in runtime_variables
    assert runtime_variables["test_var"].vars_populated_by_first_update == ["TestModel"]

    # Rerunning should detect that there is already an entry in
    # vars_populated_by_first_update
    with pytest.raises(ValueError, match="already initialised during first update"):
        _collect_vars_populated_by_first_update(
            [fixture_test_model],
            runtime_variables=runtime_variables,
            known_variables=known_variables,
        )

    # If the variable was initialised during init...
    runtime_variables.pop("test_var")
    _collect_vars_populated_by_init(
        [fixture_test_model],
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )

    # re-registering during update will also fail
    with pytest.raises(ValueError, match="already initialised during init"):
        _collect_vars_populated_by_first_update(
            [fixture_test_model],
            runtime_variables=runtime_variables,
            known_variables=known_variables,
        )


def test_collect_vars_updated(caplog, fixture_variable, fixture_test_model):
    """Test the _collect_updated_by_vars function."""
    from virtual_ecosystem.core.variables import _collect_vars_updated

    fixture_test_model.vars_updated = ("test_var",)

    runtime_variables = {}

    # Model wants to update an uninitialised variable and fails
    with pytest.raises(ValueError, match="is not initialised"):
        _collect_vars_updated(
            [fixture_test_model],
            runtime_variables=runtime_variables,
        )

    # Model can successfully update an initialised variable
    fixture_variable.vars_populated_by_init = ["AnotherModel"]
    runtime_variables["test_var"] = fixture_variable

    _collect_vars_updated([fixture_test_model], runtime_variables=runtime_variables)
    assert runtime_variables["test_var"].vars_updated == ["TestModel"]

    # Model gets told off for updating a variable already updated
    _collect_vars_updated([fixture_test_model], runtime_variables=runtime_variables)
    assert caplog.records[-1].levelname == "WARNING"
    assert "is already updated" in caplog.records[-1].message
    assert runtime_variables["test_var"].vars_updated == [
        "TestModel",
        "TestModel",
    ]


def test_collect_vars_required_for_update(fixture_variable, fixture_test_model):
    """Test the _collect_vars_required_for_update function."""
    from virtual_ecosystem.core.variables import _collect_vars_required_for_update

    fixture_test_model.vars_required_for_update = ("test_var",)

    runtime_variables = {}

    # Model requires an uninitialised variable to update and fails
    with pytest.raises(ValueError, match="is not initialised"):
        _collect_vars_required_for_update(
            [fixture_test_model], runtime_variables=runtime_variables
        )

    fixture_variable.vars_populated_by_init = ["AnotherModel"]
    runtime_variables["test_var"] = fixture_variable

    # Model now has the variables required for update
    _collect_vars_required_for_update(
        [fixture_test_model], runtime_variables=runtime_variables
    )
    assert runtime_variables["test_var"].vars_required_by_update == ["TestModel"]


def test_collect_vars_required_for_init(fixture_variable, fixture_test_model):
    """Test the _collect_vars_required_for_init function."""
    from virtual_ecosystem.core.variables import _collect_vars_required_for_init

    fixture_test_model.vars_required_for_init = ("test_var",)

    runtime_variables = {}

    # Model requires an uninitialised variable to init and fails
    with pytest.raises(ValueError, match="is not initialised"):
        _collect_vars_required_for_init(
            [fixture_test_model], runtime_variables=runtime_variables
        )

    fixture_variable.vars_populated_by_init = ["AnotherModel"]
    runtime_variables["test_var"] = fixture_variable

    # Model now has the variables required for update
    _collect_vars_required_for_init(
        [fixture_test_model], runtime_variables=runtime_variables
    )
    assert runtime_variables["test_var"].vars_required_by_init == ["TestModel"]


def test_collect_initial_data_vars(fixture_variable, fixture_test_model):
    """Test the _collect_initial_data_vars function."""
    from virtual_ecosystem.core.variables import _collect_initial_data_vars

    runtime_variables = {}
    known_variables = {}

    with pytest.raises(ValueError, match="Unknown variable test_var in data object"):
        _collect_initial_data_vars(
            ["test_var"],
            runtime_variables=runtime_variables,
            known_variables=known_variables,
        )

    known_variables["test_var"] = fixture_variable

    _collect_initial_data_vars(
        ["test_var"],
        runtime_variables=runtime_variables,
        known_variables=known_variables,
    )

    assert "test_var" in runtime_variables
    assert runtime_variables["test_var"].vars_populated_by_init == ["data"]

    with pytest.raises(ValueError, match="already populated from data"):
        _collect_initial_data_vars(
            ["test_var"],
            runtime_variables=runtime_variables,
            known_variables=known_variables,
        )


def test_setup_variables(mocker, fixture_variable, fixture_test_model):
    """Test the _collect_initial_data_vars function."""
    from virtual_ecosystem.core import variables

    mocker.patch("virtual_ecosystem.core.variables._collect_initial_data_vars")
    mocker.patch("virtual_ecosystem.core.variables._collect_vars_populated_by_init")
    mocker.patch(
        "virtual_ecosystem.core.variables._collect_vars_populated_by_first_update"
    )
    mocker.patch("virtual_ecosystem.core.variables._collect_vars_required_for_init")
    mocker.patch("virtual_ecosystem.core.variables._collect_vars_updated")
    mocker.patch("virtual_ecosystem.core.variables._collect_vars_required_for_update")

    variables.setup_variables(
        [fixture_test_model],
        ["test_var"],
        known_variables={"test_var": fixture_variable},
    )

    variables._collect_initial_data_vars.assert_called_once_with(
        vars=["test_var"],
        known_variables={"test_var": fixture_variable},
        runtime_variables={},
    )
    variables._collect_vars_populated_by_init.assert_called_once_with(
        models=[fixture_test_model],
        known_variables={"test_var": fixture_variable},
        runtime_variables={},
    )

    variables._collect_vars_populated_by_first_update.assert_called_once_with(
        models=[fixture_test_model],
        known_variables={"test_var": fixture_variable},
        runtime_variables={},
    )
    variables._collect_vars_required_for_init.assert_called_once_with(
        models=[fixture_test_model],
        runtime_variables={},
    )
    variables._collect_vars_updated.assert_called_once_with(
        models=[fixture_test_model],
        runtime_variables={},
    )
    variables._collect_vars_required_for_update.assert_called_once_with(
        models=[fixture_test_model],
        runtime_variables={},
    )


def test_get_model_order():
    """Test the get_model_order function."""
    from virtual_ecosystem.core.exceptions import ConfigurationError
    from virtual_ecosystem.core.variables import VariableMetadata, get_model_order

    var1 = VariableMetadata("var1", "", "", "", ())
    var2 = VariableMetadata("var2", "", "", "", ())
    var3 = VariableMetadata("var3", "", "", "", ())

    runtime_variables = {"var1": var1, "var2": var2, "var3": var3}

    # Test wrong stage
    with pytest.raises(
        ConfigurationError, match=r"Stage must be either 'init' or 'update'."
    ):
        get_model_order("wrong_stage", {})

    # Test cyclic dependencies issues
    var1.vars_required_by_init = ["model2"]
    var1.vars_populated_by_init = ["model1"]
    var2.vars_required_by_init = ["model1"]
    var2.vars_populated_by_init = ["model2"]

    with pytest.raises(ConfigurationError, match="Model init dependencies are cyclic"):
        get_model_order("init", runtime_variables=runtime_variables)

    # Check that a model that does not depend on init is still included (model3)
    var2.vars_required_by_init = ["model2"]
    var2.vars_populated_by_init = ["model1"]
    var3.vars_required_by_update = ["model3"]
    assert get_model_order("init", runtime_variables=runtime_variables) == [
        "model1",
        "model3",
        "model2",
    ]

    # Check that a model that depends on data is still included, but data isn't
    var3.vars_required_by_init = ["model3"]
    var3.vars_populated_by_init = ["data"]
    var3.vars_required_by_update = []
    assert get_model_order("init", runtime_variables=runtime_variables) == [
        "model1",
        "model3",
        "model2",
    ]

    # Check that a cascade of dependencies is correctly ordered (model3 should be last)
    var2.vars_required_by_init = ["model3"]
    var2.vars_populated_by_init = ["model1"]
    var3.vars_required_by_init = ["model3"]
    var3.vars_populated_by_init = ["model2"]
    assert get_model_order("init", runtime_variables=runtime_variables) == [
        "model1",
        "model2",
        "model3",
    ]
