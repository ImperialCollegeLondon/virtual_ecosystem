"""Test module for base_model.py (and associated functionality).

This module tests the functionality of base_model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR
from typing import Any

import pytest

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError


@pytest.fixture(scope="module")
def data_instance():
    """Creates a simple data instance for use in testing."""
    from xarray import DataArray

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    grid = Grid()
    data = Data(grid=grid)

    data["temperature"] = DataArray([20] * 100, dims="cell_id")
    data["precipitation"] = DataArray([20] * 100, dims="not_cell_id")

    return data


@pytest.mark.parametrize(
    argnames="init_args,  exp_raise, exp_msg, exp_log",
    argvalues=[
        pytest.param(
            {},
            pytest.raises(TypeError),
            "BaseModel.__init_subclass__() missing 4 required positional arguments: "
            "'model_name', 'model_update_bounds', 'required_init_vars', "
            "and 'vars_updated'",
            [],
            id="missing_all_args",
        ),
        pytest.param(
            {"model_name": 9},
            pytest.raises(TypeError),
            "BaseModel.__init_subclass__() missing 3 required positional arguments: "
            "'model_update_bounds', 'required_init_vars', and 'vars_updated'",
            [],
            id="missing_3_args",
        ),
        pytest.param(
            {
                "model_name": "should_pass",
                "required_init_vars": (
                    (
                        "temperature",
                        ("spatial",),
                    ),
                ),
                "model_update_bounds": ("1 day", "1 month"),
                "vars_updated": [],
            },
            does_not_raise(),
            None,
            [],
            id="all_vars",
        ),
        pytest.param(
            {
                "model_name": 9,
                "required_init_vars": (),
                "model_update_bounds": ("1 day", "1 month"),
                "vars_updated": [],
            },
            pytest.raises(TypeError),
            "Class attribute model_name in UnnamedModel is not a string",
            [
                (ERROR, "Class attribute model_name in UnnamedModel is not a string"),
                (CRITICAL, "Errors in defining UnnamedModel class attributes: see log"),
            ],
            id="nonstring model_name",
        ),
        pytest.param(
            {
                "model_name": "should_pass",
                "required_init_vars": (),
                "model_update_bounds": ("1 day", "1 time"),
                "vars_updated": [],
            },
            pytest.raises(ValueError),
            "Class attribute model_update_bounds for UnnamedModel "
            "contains undefined units.",
            [
                (
                    ERROR,
                    "Class attribute model_update_bounds for UnnamedModel "
                    "contains undefined units.",
                ),
                (CRITICAL, "Errors in defining UnnamedModel class attributes: see log"),
            ],
            id="Bad unit for upper_bound_on_time_scale",
        ),
        pytest.param(
            {
                "model_name": "should_pass",
                "required_init_vars": (),
                "model_update_bounds": ("1 day", "1 day"),
                "vars_updated": [],
            },
            pytest.raises(ValueError),
            "Lower time bound for UnnamedModel is not less than the upper bound.",
            [
                (
                    ERROR,
                    "Lower time bound for UnnamedModel is not less than the upper "
                    "bound.",
                ),
                (CRITICAL, "Errors in defining UnnamedModel class attributes: see log"),
            ],
            id="Lower and upper bound equal",
        ),
        pytest.param(
            {
                "model_name": "should_pass",
                "required_init_vars": (),
                "model_update_bounds": ("1 day", "1 second"),
                "vars_updated": [],
            },
            pytest.raises(ValueError),
            "Lower time bound for UnnamedModel is not less than the upper bound.",
            [
                (
                    ERROR,
                    "Lower time bound for UnnamedModel is not less than the upper "
                    "bound.",
                ),
                (CRITICAL, "Errors in defining UnnamedModel class attributes: see log"),
            ],
            id="Lower bound greater",
        ),
        pytest.param(
            {
                "model_name": "should_pass",
                "required_init_vars": (),
                "model_update_bounds": ("1 meter", "1 day"),
                "vars_updated": [],
            },
            pytest.raises(ValueError),
            "Class attribute model_update_bounds for UnnamedModel "
            "contains non-time units.",
            [
                (
                    ERROR,
                    "Class attribute model_update_bounds for UnnamedModel "
                    "contains non-time units.",
                ),
                (CRITICAL, "Errors in defining UnnamedModel class attributes: see log"),
            ],
            id="Distance unit for model_update_bounds",
        ),
        pytest.param(
            {
                "model_name": "should_pass",
                "required_init_vars": (),
                "model_update_bounds": ("1 spongebob", "1 day"),
                "vars_updated": [],
            },
            pytest.raises(ValueError),
            "Class attribute model_update_bounds for UnnamedModel "
            "contains undefined units.",
            [
                (
                    ERROR,
                    "Class attribute model_update_bounds for UnnamedModel "
                    "contains undefined units.",
                ),
                (CRITICAL, "Errors in defining UnnamedModel class attributes: see log"),
            ],
            id="Distance unit for model_update_bounds",
        ),
    ],
)
def test_init_subclass(caplog, init_args, exp_raise, exp_msg, exp_log):
    """Test that  __init_subclass__ gives expected behaviours.

    TODO - this could broken down into tests of the individual private checking methods,
    but this tests the ensemble behaviour of the __init_subclass__ method.
    """

    from virtual_ecosystem.core.base_model import BaseModel

    caplog.clear()

    with exp_raise as err:

        class UnnamedModel(BaseModel, **init_args):
            pass

    if err:
        # Check any error message
        assert str(err.value) == exp_msg

    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames="riv_value, exp_raise, exp_msg",
    argvalues=[
        pytest.param(
            1,
            pytest.raises(TypeError),
            "Class attribute required_init_vars has the wrong structure in UM",
            id="RIV is integer",
        ),
        pytest.param(
            ["temperature", (1, 2)],
            pytest.raises(TypeError),
            "Class attribute required_init_vars has the wrong structure in UM",
            id="RIV is list",
        ),
        pytest.param(
            ("temperature", ("spatial",)),
            pytest.raises(TypeError),
            "Class attribute required_init_vars has the wrong structure in UM",
            id="RIV is not nested enough",
        ),
        pytest.param(
            (("temperature", (1,)),),
            pytest.raises(TypeError),
            "Class attribute required_init_vars has the wrong structure in UM",
            id="RIV axis is not string",
        ),
        pytest.param(
            (("temperature", (1,), (2,)),),
            pytest.raises(TypeError),
            "Class attribute required_init_vars has the wrong structure in UM",
            id="RIV entry is too long",
        ),
        pytest.param(
            (("temperature", ("special",)),),
            pytest.raises(ValueError),
            "Class attribute required_init_vars uses unknown core axes in UM: special",
            id="RIV entry has bad axis name",
        ),
        pytest.param(
            (("temperature", ("spatial",)),),
            does_not_raise(),
            None,
            id="RIV ok",
        ),
    ],
)
def test_check_required_init_var_structure(riv_value, exp_raise, exp_msg):
    """Test that  __init_subclass__ traps bad values for required_init_vars."""

    # BaseModel is required here in the code being exec'd from the params.
    from virtual_ecosystem.core.base_model import BaseModel  # noqa: F401

    with exp_raise as err:
        # Run the code to define the model
        class UM(
            BaseModel,
            model_name="should_also_pass",
            required_init_vars=riv_value,
            model_update_bounds=("1 day", "1 month"),
            vars_updated=[],
        ):
            pass

    if err:
        # Check any error message
        assert str(err.value) == exp_msg


def test_check_failure_on_missing_methods(data_instance, fixture_core_components):
    """Test that a model without methods raises an error.

    The two properties get caught earlier, when __init_subclass__ runs, but missing
    methods are caught when anyone tries to get an instance of the model.
    """
    from virtual_ecosystem.core.base_model import BaseModel

    class InitVarModel(
        BaseModel,
        model_name="init_var",
        model_update_bounds=("1 second", "1 year"),
        required_init_vars=(),
        vars_updated=[],
    ):
        pass

    with pytest.raises(TypeError) as err:
        _ = InitVarModel(data=data_instance, core_components=fixture_core_components)

    # Note python version specific exception messages:
    # - Can't instantiate abstract class InitVarModel with abstract methods cleanup,
    #   from_config, setup, spinup, update
    # versus
    # - Can't instantiate abstract class InitVarModel without an implementation for
    #   abstract methods 'cleanup', 'from_config', 'setup', 'spinup', 'update'
    assert str(err.value).startswith("Can't instantiate abstract class InitVarModel ")


@pytest.mark.parametrize(
    argnames="req_init_vars, raises, exp_err_msg, exp_log",
    argvalues=[
        pytest.param(
            [("temperature", ("spatial",))],
            does_not_raise(),
            None,
            ((DEBUG, "init_var model: required var 'temperature' checked"),),
            id="single var with axes ok",
        ),
        pytest.param(
            [("precipitation", tuple())],
            does_not_raise(),
            None,
            ((DEBUG, "init_var model: required var 'precipitation' checked"),),
            id="single var without axes ok",
        ),
        pytest.param(
            [("temperature", ("spatial",)), ("precipitation", tuple())],
            does_not_raise(),
            None,
            (
                (DEBUG, "init_var model: required var 'temperature' checked"),
                (DEBUG, "init_var model: required var 'precipitation' checked"),
            ),
            id="multivar ok",
        ),
        pytest.param(
            [("precipitation", ("spatial",))],
            pytest.raises(ValueError),
            "init_var model: error checking required_init_vars, see log.",
            (
                (
                    ERROR,
                    "init_var model: required var 'precipitation' not on required "
                    "axes: spatial",
                ),
                (
                    ERROR,
                    "init_var model: error checking required_init_vars, see log.",
                ),
            ),
            id="missing axis",
        ),
    ],
)
def test_check_required_init_vars(
    caplog,
    data_instance,
    fixture_core_components,
    req_init_vars,
    raises,
    exp_err_msg,
    exp_log,
):
    """Tests the validation of the required_init_vars property on init."""

    # This gets registered for each parameterisation but I can't figure out how to
    # create the instance via a module-scope fixture and the alternative is just
    # defining it at the top, which isn't encapsulated in a test.

    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.core.data import Data

    class TestCaseModel(
        BaseModel,
        model_name="init_var",
        model_update_bounds=("1 second", "1 year"),
        required_init_vars=(),
        vars_updated=[],
    ):
        def setup(self) -> None:
            pass

        def spinup(self) -> None:
            pass

        def update(self, time_index: int, **kwargs: Any) -> None:
            pass

        def cleanup(self) -> None:
            pass

        @classmethod
        def from_config(
            cls,
            data: Data,
            core_components: CoreComponents,
            config: Config,
        ) -> Any:
            return super().from_config(
                data=data, core_components=core_components, config=config
            )

    # Registration of TestClassModel emits logging messages - discard.
    caplog.clear()

    # Override the required_init_vars for different test cases against the data_instance
    TestCaseModel.required_init_vars = req_init_vars

    # Create an instance to check the handling
    with raises as err:
        inst = TestCaseModel(
            data=data_instance,
            core_components=fixture_core_components,
        )

    if err:
        # Check any error message
        assert str(err.value) == exp_err_msg
    else:
        # Check the special methods
        assert repr(inst).startswith("TestCaseModel(")
        assert str(inst) == "A init_var model instance"

    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames=["config_string", "raises", "expected_log"],
    argvalues=[
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "1 month"
            """,
            does_not_raise(),
            (),
            id="correct 1",
        ),
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "1 day"
            """,
            does_not_raise(),
            (),
            id="correct 2",
        ),
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "30 minutes"
            """,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "The update interval is faster than the timing_test "
                    "lower bound of 1 day.",
                ),
            ),
            id="too fast",
        ),
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "3 months"
            """,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "The update interval is slower than the timing_test upper "
                    "bound of 1 month.",
                ),
            ),
            id="too slow",
        ),
    ],
)
def test_check_update_speed(caplog, config_string, raises, expected_log):
    """Tests check on update speed."""

    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.core.data import Data

    class TimingTestModel(
        BaseModel,
        model_name="timing_test",
        model_update_bounds=("1 day", "1 month"),
        required_init_vars=(),
        vars_updated=[],
    ):
        def setup(self) -> None:
            pass

        def spinup(self) -> None:
            pass

        def update(self, time_index: int, **kwargs: Any) -> None:
            pass

        def cleanup(self) -> None:
            pass

        @classmethod
        def from_config(
            cls,
            data: Data,
            core_components: CoreComponents,
            config: Config,
        ) -> Any:
            return super().from_config(
                data=data, core_components=core_components, config=config
            )

    config = Config(cfg_strings=config_string)
    core_components = CoreComponents(config=config)
    # Clear model registration and configuration messages
    caplog.clear()

    with raises:
        _ = TimingTestModel(data=data_instance, core_components=core_components)

    log_check(caplog, expected_log)
