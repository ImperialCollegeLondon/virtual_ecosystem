"""Test module for model.py (and associated functionality).

This module tests the functionality of model.py, as well as other bits of code that
define models based on the class defined in model.py
"""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO, WARNING
from typing import Any

import pytest
from numpy import datetime64, timedelta64

from .conftest import log_check


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
    argnames="code, cls_name, exp_raise, exp_msg, exp_log",
    argvalues=[
        pytest.param(
            """class UnnamedModel(BaseModel):
                # Model where a model_name has not been included.
                pass
            """,
            "UnnamedModel",
            pytest.raises(NotImplementedError),
            "Property model_name is not implemented in UnnamedModel",
            [(ERROR, "Property model_name is not implemented in UnnamedModel")],
            id="undefined model_name",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                # Model where a model_name has not been included.
                model_name = 9
            """,
            "UnnamedModel",
            pytest.raises(TypeError),
            "Property model_name in UnnamedModel is not a string",
            [(ERROR, "Property model_name in UnnamedModel is not a string")],
            id="nonstring model_name",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                # Model where a model_name has not been included.
                model_name = 'should_pass'
            """,
            "UnnamedModel",
            pytest.raises(NotImplementedError),
            "Property required_init_vars is not implemented in UnnamedModel",
            [(ERROR, "Property required_init_vars is not implemented in UnnamedModel")],
            id="Undefined required_init_vars",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                # Model where a model_name has not been included.
                model_name = 'should_pass'
                required_init_vars = tuple()
            """,
            "UnnamedModel",
            does_not_raise(),
            None,
            [(INFO, "UnnamedModel registered under name 'should_pass'")],
            id="should pass and register",
        ),
        pytest.param(
            """class UnnamedModel2(BaseModel):
                # Model where a model_name has not been included.
                model_name = 'should_pass'
                required_init_vars = tuple()
            """,
            "UnnamedModel2",
            does_not_raise(),
            None,
            [
                (
                    WARNING,
                    "UnnamedModel already registered under name 'should_pass', "
                    "replaced with UnnamedModel2",
                )
            ],
            id="should pass and replace",
        ),
    ],
)
def test_init_subclass(caplog, code, cls_name, exp_raise, exp_msg, exp_log):
    """Test that  __init_subclass__ gives expected behaviours.

    This test uses exec() to concisely pass in a bunch of different model definitions.
    Although exec() can be harmful, should be ok here.
    """

    # BaseModel is required here in the code being exec'd from the params.
    from virtual_rainforest.core.model import MODEL_REGISTRY, BaseModel  # noqa: F401

    with exp_raise as err:
        # Run the code to define the model
        exec(code)

    if err:
        # Check any error message
        assert str(err.value) == exp_msg
    else:
        # Check the model is registered as expected.
        assert "should_pass" in MODEL_REGISTRY
        assert MODEL_REGISTRY["should_pass"].__name__ == cls_name

    log_check(caplog, exp_log)


def test_check_failure_on_missing_methods(data_instance):
    """Test that a model without methods raises an error.

    The two properties get caught earlier, when __init_subclass__ runs, but missing
    methods are caught when anyone tries to get an instance of the model.
    """
    from virtual_rainforest.core.model import BaseModel

    class InitVarModel(BaseModel):
        model_name = "init_var"
        required_init_vars = ()

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
            [("temperature", ("special",))],
            pytest.raises(ValueError),
            "init_var model: error checking required_init_vars, see log.",
            (
                (
                    ERROR,
                    "init_var model: unknown axis names set in model definition for "
                    "var 'temperature': special",
                ),
                (
                    ERROR,
                    "init_var model: error checking required_init_vars, see log.",
                ),
            ),
            id="unknown axis",
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
        pytest.param(
            [
                ("temperature", ("special",)),
                ("precipitation", ("spatial",)),
            ],
            pytest.raises(ValueError),
            "init_var model: error checking required_init_vars, see log.",
            (
                (
                    ERROR,
                    "init_var model: unknown axis names set in model definition for "
                    "var 'temperature': special",
                ),
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
            id="both unknown and missing",
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

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.logger import LOGGER
    from virtual_rainforest.core.model import BaseModel

    # Class uses DEBUG
    # TODO - might want to do this centrally in conf_test.py
    LOGGER.setLevel(DEBUG)

    class TestCaseModel(BaseModel):
        model_name = "init_var"
        required_init_vars = []

        def setup(self) -> None:
            return super().setup()

        def spinup(self) -> None:
            return super().spinup()

        def update(self) -> None:
            return super().update()

        def cleanup(self) -> None:
            return super().cleanup()

        @classmethod
        def from_config(cls, data: Data, config: dict[str, Any]) -> Any:
            return super().from_config(data, config)

    # Registration of TestClassModel emits logging messages - discard.
    caplog.clear()

    # Override the required_init_vars for different test cases against the data_instance
    TestCaseModel.required_init_vars = req_init_vars

    # Create an instance to check the handling
    with raises as err:
        inst = TestCaseModel(  # noqa: F841
            data=data_instance,
            update_interval=timedelta64(1, "W"),
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
