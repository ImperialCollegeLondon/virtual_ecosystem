"""Test the registry functionality."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import pytest

from tests.conftest import log_check


@pytest.mark.parametrize(
    argnames="module_name, raises, exp_log",
    argvalues=[
        pytest.param(
            "virtual_rainforest.core",
            does_not_raise(),
            (
                (INFO, "Registering module: virtual_rainforest.core"),
                (INFO, "Schema registered for virtual_rainforest.core:"),
                (
                    INFO,
                    "Constants class registered for "
                    "virtual_rainforest.core: CoreConsts",
                ),
            ),
            id="core_import_good",
        ),
        pytest.param(
            "tests.core.test_modules.one_model",
            does_not_raise(),
            (
                (INFO, "Registering module: tests.core.test_modules.one_model"),
                (
                    INFO,
                    "Registering model class for "
                    "tests.core.test_modules.one_model: ATestModel",
                ),
                (INFO, "Schema registered for tests.core.test_modules.one_model:"),
                (
                    INFO,
                    "Constants class registered for "
                    "tests.core.test_modules.one_model: TestConsts",
                ),
            ),
            id="model_import_good",
        ),
        pytest.param(
            "tests.core.test_modules.nothing_here",
            pytest.raises(ModuleNotFoundError),
            (
                (
                    CRITICAL,
                    "Unknown module - registration failed: "
                    "tests.core.test_modules.nothing_here",
                ),
            ),
            id="model_import_bad_module",
        ),
        pytest.param(
            "tests.core.test_modules.no_model",
            pytest.raises(RuntimeError),
            (
                (
                    CRITICAL,
                    "Model object not found in tests.core.test_modules.no_model",
                ),
            ),
            id="model_import_no_model",
        ),
        pytest.param(
            "tests.core.test_modules.two_models",
            pytest.raises(RuntimeError),
            (
                (
                    CRITICAL,
                    "More than one model defined in tests.core.test_modules.two_models",
                ),
            ),
            id="model_import_two_models",
        ),
        pytest.param(  # TODO - may become redundant if the name is set automatically.
            "tests.core.test_modules.bad_name",
            pytest.raises(RuntimeError),
            (
                (INFO, "Registering module: tests.core.test_modules.bad_name"),
                (
                    CRITICAL,
                    "Different model_name attribute and module name "
                    "in tests.core.test_modules.bad_name",
                ),
            ),
            id="model_import_bad_name",
        ),
    ],
)
def test_registry(caplog, module_name, raises, exp_log):
    """Test the registry loading.

    This uses a dummy model to impersonate the plant model, because importing any real
    models triggers `register_module` calls from the module __init__.py files.
    """

    from virtual_rainforest.core.base_model import BaseModel
    from virtual_rainforest.core.constants_class import ConstantsDataclass
    from virtual_rainforest.core.registry import (
        MODULE_REGISTRY,
        ModuleInfo,
        register_module,
    )

    # Get the short name
    _, _, short_name = module_name.rpartition(".")

    caplog.clear()

    with raises:
        register_module(module_name=module_name)

        if isinstance(raises, does_not_raise):
            # Test the detailed structure of the registry for the module
            assert short_name in MODULE_REGISTRY
            mod_info = MODULE_REGISTRY[short_name]
            assert isinstance(mod_info, ModuleInfo)

            if not mod_info.is_core:
                assert issubclass(mod_info.model, BaseModel)

            assert isinstance(mod_info.schema, dict)
            assert isinstance(mod_info.constants_classes, dict)
            for c_class in mod_info.constants_classes.values():
                assert issubclass(c_class, ConstantsDataclass)

        # Check the last N entries in the log match the expectation.
        log_check(
            caplog=caplog, expected_log=exp_log, subset=slice(-len(exp_log), None, None)
        )
