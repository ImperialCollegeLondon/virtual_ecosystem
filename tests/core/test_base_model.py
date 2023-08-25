"""Test module for base_model.py (and associated functionality).

This module tests the functionality of base_model.py
"""

import sys
from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
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
    argnames="code, reg_name, cls_name, exp_raise, exp_msg, exp_log",
    argvalues=[
        pytest.param(
            """class UnnamedModel(BaseModel):
                pass
            """,
            None,
            "UnnamedModel",
            pytest.raises(NotImplementedError),
            "Property model_name is not implemented in UnnamedModel",
            [
                (ERROR, "Property model_name is not implemented in UnnamedModel"),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="undefined model_name",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 9
            """,
            None,
            "UnnamedModel",
            pytest.raises(TypeError),
            "Property model_name in UnnamedModel is not a string",
            [
                (ERROR, "Property model_name in UnnamedModel is not a string"),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="nonstring model_name",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_pass'
            """,
            None,
            "UnnamedModel",
            pytest.raises(NotImplementedError),
            "Property required_init_vars is not implemented in UnnamedModel",
            [
                (
                    ERROR,
                    "Property required_init_vars is not implemented in UnnamedModel",
                ),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="Undefined required_init_vars",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'shouldnt_pass'
                required_init_vars = tuple()
            """,
            None,
            "UnnamedModel",
            pytest.raises(NotImplementedError),
            "Property vars_updated is not implemented in UnnamedModel",
            [
                (
                    ERROR,
                    "Property vars_updated is not implemented in UnnamedModel",
                ),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="Undefined vars_updated",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_pass'
                required_init_vars = tuple()
                vars_updated = []
            """,
            None,
            "UnnamedModel",
            pytest.raises(NotImplementedError),
            "Property lower_bound_on_time_scale is not implemented in UnnamedModel",
            [
                (
                    ERROR,
                    "Property lower_bound_on_time_scale is not implemented in "
                    "UnnamedModel",
                ),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="No lower_bound_on_time_scale",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_pass'
                required_init_vars = tuple()
                lower_bound_on_time_scale = "1 day"
                vars_updated = []
            """,
            None,
            "UnnamedModel",
            pytest.raises(NotImplementedError),
            "Property upper_bound_on_time_scale is not implemented in UnnamedModel",
            [
                (
                    ERROR,
                    "Property upper_bound_on_time_scale is not implemented in "
                    "UnnamedModel",
                ),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="No upper_bound_on_time_scale",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_pass'
                required_init_vars = tuple()
                lower_bound_on_time_scale = "1 day"
                upper_bound_on_time_scale = "1 time"
                vars_updated = []
            """,
            None,
            "UnnamedModel",
            pytest.raises(ValueError),
            "Invalid units for model time bound, see above errors.",
            [
                (ERROR, "Upper bound for UnnamedModel not given a valid unit."),
                (
                    ERROR,
                    "Invalid units for model time bound, see above errors.",
                ),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="Bad unit for upper_bound_on_time_scale",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_pass'
                required_init_vars = tuple()
                lower_bound_on_time_scale = "1 day"
                upper_bound_on_time_scale = "1 day"
                vars_updated = []
            """,
            None,
            "UnnamedModel",
            pytest.raises(ValueError),
            "Lower time bound for UnnamedModel is not less than the upper bound.",
            [
                (
                    ERROR,
                    "Lower time bound for UnnamedModel is not less than the upper "
                    "bound.",
                ),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="Lower and upper bound equal",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_pass'
                required_init_vars = tuple()
                lower_bound_on_time_scale = "1 month"
                upper_bound_on_time_scale = "1 day"
                vars_updated = []
            """,
            None,
            "UnnamedModel",
            pytest.raises(ValueError),
            "Lower time bound for UnnamedModel is not less than the upper bound.",
            [
                (
                    ERROR,
                    "Lower time bound for UnnamedModel is not less than the upper "
                    "bound.",
                ),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="Lower bound greater",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_pass'
                required_init_vars = tuple()
                lower_bound_on_time_scale = "1 meter"
                upper_bound_on_time_scale = "1 month"
                vars_updated = []
            """,
            None,
            "UnnamedModel",
            pytest.raises(ValueError),
            "Invalid units for model time bound, see above errors.",
            [
                (ERROR, "Lower bound for UnnamedModel given a non-time unit."),
                (
                    ERROR,
                    "Invalid units for model time bound, see above errors.",
                ),
                (CRITICAL, "Errors in UnnamedModel class properties: see log"),
            ],
            id="Distance unit for lower_bound_on_time_scale",
        ),
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_pass'
                required_init_vars = tuple()
                lower_bound_on_time_scale = "1 day"
                upper_bound_on_time_scale = "1 month"
                vars_updated = []
            """,
            "should_pass",
            "UnnamedModel",
            does_not_raise(),
            None,
            [(INFO, "UnnamedModel registered under name 'should_pass'")],
            id="should pass and register",
        ),
        pytest.param(
            """class UnnamedModel2(BaseModel):
                model_name = 'should_pass'
                required_init_vars = tuple()
                lower_bound_on_time_scale = "1 day"
                upper_bound_on_time_scale = "1 month"
                vars_updated = []
            """,
            "should_pass",
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
        pytest.param(
            """class UnnamedModel(BaseModel):
                model_name = 'should_also_pass'
                required_init_vars = (('temperature', ('spatial',),),)
                lower_bound_on_time_scale = "1 day"
                upper_bound_on_time_scale = "1 month"
                vars_updated = []
            """,
            "should_also_pass",
            "UnnamedModel",
            does_not_raise(),
            None,
            [
                (INFO, "UnnamedModel registered under name 'should_also_pass'"),
            ],
            id="should pass - RIV not empty",
        ),
    ],
)
def test_init_subclass(caplog, code, reg_name, cls_name, exp_raise, exp_msg, exp_log):
    """Test that  __init_subclass__ gives expected behaviours.

    This test uses exec() to concisely pass in a bunch of different model definitions.
    Although exec() can be harmful, should be ok here.
    """

    # BaseModel is required here in the code being exec'd from the params.
    from virtual_rainforest.core.base_model import BaseModel  # noqa: F401
    from virtual_rainforest.core.base_model import MODEL_REGISTRY

    with exp_raise as err:
        # Run the code to define the model
        exec(code)

    if err:
        # Check any error message
        assert str(err.value) == exp_msg
    else:
        # Check the model is registered as expected.
        assert reg_name in MODEL_REGISTRY
        assert MODEL_REGISTRY[reg_name].__name__ == cls_name

    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    argnames="riv_value, exp_raise, exp_msg",
    argvalues=[
        pytest.param(
            "1",
            pytest.raises(TypeError),
            "Property required_init_vars has the wrong structure in UM",
            id="RIV is integer",
        ),
        pytest.param(
            "['temperature', (1, 2)]",
            pytest.raises(TypeError),
            "Property required_init_vars has the wrong structure in UM",
            id="RIV is list",
        ),
        pytest.param(
            "('temperature', ('spatial',))",
            pytest.raises(TypeError),
            "Property required_init_vars has the wrong structure in UM",
            id="RIV is not nested enough",
        ),
        pytest.param(
            "(('temperature', (1,)),)",
            pytest.raises(TypeError),
            "Property required_init_vars has the wrong structure in UM",
            id="RIV axis is not string",
        ),
        pytest.param(
            "(('temperature', (1,), (2,)),)",
            pytest.raises(TypeError),
            "Property required_init_vars has the wrong structure in UM",
            id="RIV entry is too long",
        ),
        pytest.param(
            "(('temperature', ('special',)),)",
            pytest.raises(ValueError),
            "Property required_init_vars uses unknown core axes in UM: special",
            id="RIV entry has bad axis name",
        ),
        pytest.param(
            "(('temperature', ('spatial',)),)",
            does_not_raise(),
            None,
            id="RIV ok",
        ),
    ],
)
def test_check_required_init_var_structure(caplog, riv_value, exp_raise, exp_msg):
    """Test that  __init_subclass__ traps different bad values for required_init_vars.

    This test uses exec() to concisely pass in a bunch of different model definitions.
    Although exec() can be harmful, should be ok here.
    """

    # BaseModel is required here in the code being exec'd from the params.
    from virtual_rainforest.core.base_model import BaseModel  # noqa: F401

    code = f"""class UM(BaseModel):
        model_name = 'should_also_pass'
        required_init_vars = {riv_value}
        lower_bound_on_time_scale = "1 day"
        upper_bound_on_time_scale = "1 month"
        vars_updated = []
    """

    with exp_raise as err:
        # Run the code to define the model
        exec(code)

    if err:
        # Check any error message
        assert str(err.value) == exp_msg


def test_check_failure_on_missing_methods(data_instance):
    """Test that a model without methods raises an error.

    The two properties get caught earlier, when __init_subclass__ runs, but missing
    methods are caught when anyone tries to get an instance of the model.
    """
    from virtual_rainforest.core.base_model import BaseModel

    class InitVarModel(BaseModel):
        model_name = "init_var"
        lower_bound_on_time_scale = "1 second"
        upper_bound_on_time_scale = "1 year"
        required_init_vars = ()
        vars_updated = []

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
    from virtual_rainforest.core.data import Data

    class TestCaseModel(BaseModel):
        model_name = "init_var"
        lower_bound_on_time_scale = "1 second"
        upper_bound_on_time_scale = "1 year"
        required_init_vars = ()
        vars_updated = []

        def setup(self) -> None:
            return super().setup()

        def spinup(self) -> None:
            return super().spinup()

        def update(self, time_index: int) -> None:
            return super().update(time_index)

        def cleanup(self) -> None:
            return super().cleanup()

        @classmethod
        def from_config(
            cls, data: Data, config: dict[str, Any], update_interval: pint.Quantity
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
            (
                (
                    ERROR,
                    "The update interval is shorter than the model's lower bound",
                ),
            ),
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
            (
                (
                    ERROR,
                    "The update interval is longer than the model's upper bound",
                ),
            ),
        ),
    ],
)
def test_check_update_speed(caplog, config, raises, timestep, expected_log):
    """Tests check on update speed."""

    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.core.data import Data

    class TimingTestModel(BaseModel):
        model_name = "timing_test"
        lower_bound_on_time_scale = "1 day"
        upper_bound_on_time_scale = "1 month"
        required_init_vars = ()
        vars_updated = []

        def setup(self) -> None:
            return super().setup()

        def spinup(self) -> None:
            return super().spinup()

        def update(self, time_index: int) -> None:
            return super().update(time_index)

        def cleanup(self) -> None:
            return super().cleanup()

        @classmethod
        def from_config(
            cls, data: Data, config: dict[str, Any], update_interval: pint.Quantity
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


def test_register_model(caplog, expected_log):
    """Test that helper function for model registration works correctly."""
    from virtual_rainforest.core.base_model import register_model

    with pytest.raises(ValueError):
        register_model("virtual_rainforest.models.animals", "animals_schema.json")

    expected_log = ((CRITICAL, "The module schema for animals is already registered"),)

    log_check(caplog, expected_log)


def test_register_invalid_model(mocker, monkeypatch, caplog):
    """Test that registration of an invalid model fails as expected."""
    from virtual_rainforest.core.base_model import register_model

    custom_mock_module = mocker.Mock()
    monkeypatch.setitem(
        sys.modules, "virtual_rainforest.models.fake", custom_mock_module
    )

    with pytest.raises(ConfigurationError):
        register_model("virtual_rainforest.models.fake", "fake_schema.json")

    expected_log = ((CRITICAL, "Model <Mock id='"),)

    log_check(caplog, expected_log)
