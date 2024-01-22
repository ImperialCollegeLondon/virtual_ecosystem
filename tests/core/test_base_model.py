"""Test module for base_model.py (and associated functionality).

This module tests the functionality of base_model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR
from typing import Any

import pint
import pytest
from numpy import datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


@pytest.fixture(scope="module")
def data_instance():
    """Creates a simple data instance for use in testing."""
    from xarray import DataArray

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

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

    from virtual_rainforest.core.base_model import BaseModel

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
    from virtual_rainforest.core.base_model import BaseModel  # noqa: F401

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


def test_check_failure_on_missing_methods(data_instance):
    """Test that a model without methods raises an error.

    The two properties get caught earlier, when __init_subclass__ runs, but missing
    methods are caught when anyone tries to get an instance of the model.
    """
    from virtual_rainforest.core.base_model import BaseModel

    class InitVarModel(
        BaseModel,
        model_name="init_var",
        model_update_bounds=("1 second", "1 year"),
        required_init_vars=(),
        vars_updated=[],
    ):
        pass

    with pytest.raises(TypeError) as err:
        inst = InitVarModel(  # noqa: F841
            data=data_instance,
            update_interval=timedelta64(1, "W"),
            start_time=datetime64("2022-11-01"),
        )

    assert (
        str(err.value) == "Can't instantiate abstract class InitVarModel with "
        "abstract methods cleanup, from_config, setup, spinup, update"
    )


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
    caplog, data_instance, req_init_vars, raises, exp_err_msg, exp_log
):
    """Tests the validation of the required_init_vars property on init."""

    # This gets registered for each parameterisation but I can't figure out how to
    # create the instance via a module-scope fixture and the alternative is just
    # defining it at the top, which isn't encapsulated in a test.

    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.data import Data

    class TestCaseModel(
        BaseModel,
        model_name="init_var",
        model_update_bounds=("1 second", "1 year"),
        required_init_vars=(),
        vars_updated=[],
    ):
        def setup(self) -> None:
            return super().setup()

        def spinup(self) -> None:
            return super().spinup()

        def update(self, time_index: int, **kwargs: Any) -> None:
            return super().update(time_index)

        def cleanup(self) -> None:
            return super().cleanup()

        @classmethod
        def from_config(
            cls, data: Data, config: Config, update_interval: pint.Quantity
        ) -> Any:
            return super().from_config(data, config, update_interval)

    # Registration of TestClassModel emits logging messages - discard.
    caplog.clear()

    # Override the required_init_vars for different test cases against the data_instance
    TestCaseModel.required_init_vars = req_init_vars

    # Create an instance to check the handling
    with raises as err:
        inst = TestCaseModel(  # noqa: F841
            data=data_instance,
            update_interval=pint.Quantity("1 week"),
            start_time=datetime64("2022-11-01"),
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
    argnames=["config", "raises", "timestep", "expected_log"],
    argvalues=[
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 month",
                    }
                },
            },
            does_not_raise(),
            pint.Quantity("1 month"),
            (),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 day",
                    }
                },
            },
            does_not_raise(),
            pint.Quantity("1 day"),
            (),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "30 minutes",
                    }
                },
            },
            pytest.raises(ConfigurationError),
            None,
            ((ERROR, "The update interval is faster than the model update bounds."),),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "3 months",
                    }
                },
            },
            pytest.raises(ConfigurationError),
            None,
            ((ERROR, "The update interval is slower than the model update bounds."),),
        ),
    ],
)
def test_check_update_speed(caplog, config, raises, timestep, expected_log):
    """Tests check on update speed."""

    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.data import Data

    class TimingTestModel(
        BaseModel,
        model_name="timing_test",
        model_update_bounds=("1 day", "1 month"),
        required_init_vars=(),
        vars_updated=[],
    ):
        def setup(self) -> None:
            return super().setup()

        def spinup(self) -> None:
            return super().spinup()

        def update(self, time_index: int, **kwargs: Any) -> None:
            return super().update(time_index)

        def cleanup(self) -> None:
            return super().cleanup()

        @classmethod
        def from_config(
            cls, data: Data, config: Config, update_interval: pint.Quantity
        ) -> Any:
            return super().from_config(data, config, update_interval)

    # Registration of TestClassModel emits logging messages - discard.
    caplog.clear()

    with raises:
        inst = TimingTestModel(
            data=data_instance,
            update_interval=pint.Quantity(config["core"]["timing"]["update_interval"]),
            start_time=datetime64(config["core"]["timing"]["start_date"]),
        )
        assert inst.update_interval == timestep

    log_check(caplog, expected_log)
