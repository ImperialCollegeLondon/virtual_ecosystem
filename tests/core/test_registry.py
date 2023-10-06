"""Test the registry functionality."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import pytest

from tests.conftest import log_check


@pytest.mark.parametrize(
    argnames="module_name, model_name, raises, exp_log",
    argvalues=[
        pytest.param(
            "virtual_rainforest.core",
            None,
            does_not_raise(),
            (
                (INFO, "Registering virtual_rainforest.core module components"),
                (INFO, "Schema registered for module core:"),
                (INFO, "Constants class registered for module core: CoreConsts"),
            ),
            id="core_import_good",
        ),
        pytest.param(
            "tests.core.test_module",
            "test_module",
            does_not_raise(),
            (
                (INFO, "Registering tests.core.test_module module components"),
                (INFO, "Registering model class for test_module model: TestModel"),
                (INFO, "Schema registered for module test_module:"),
                (INFO, "Constants class registered for module test_module: TestConsts"),
            ),
            id="model_import_good",
        ),
        pytest.param(
            "tests.core.test_modelo",
            "test_modelo",
            pytest.raises(ModuleNotFoundError),
            (
                (
                    CRITICAL,
                    "Unknown module - registration failed: tests.core.test_modelo",
                ),
            ),
            id="model_import_bad_module",
        ),
        pytest.param(
            "virtual_rainforest.core",
            "test_modelo",
            pytest.raises(RuntimeError),
            (
                (INFO, "Registering virtual_rainforest.core module components"),
                (CRITICAL, "No model should be registered for the core module"),
            ),
            id="core_import_with_model",
        ),
        pytest.param(
            "tests.core.test_module",
            None,
            pytest.raises(RuntimeError),
            (
                (INFO, "Registering tests.core.test_module module components"),
                (CRITICAL, "A model class is required to register model modules"),
            ),
            id="model_import_without_model",
        ),
        pytest.param(
            "tests.core.test_module",
            "test_modelo",
            pytest.raises(RuntimeError),
            (
                (INFO, "Registering tests.core.test_module module components"),
                (
                    CRITICAL,
                    "Different model_name attribute and module name "
                    "in tests.core.test_module",
                ),
            ),
            id="model_import_bad_name",
        ),
    ],
)
def test_registry(caplog, module_name, model_name, raises, exp_log):
    """Test the registry loading.

    This uses a dummy model to impersonate the plant model, because importing any real
    models triggers `register_module` calls from the module __init__.py files.
    """

    from tests.core.test_module.test_model import TestModel
    from virtual_rainforest.core.registry import MODULE_REGISTRY, register_module

    # Get the short name
    _, _, short_name = module_name.rpartition(".")

    # Either do not provide a model (core) or provide a dummy with a name set by the
    # test
    if model_name is None:
        model = None
    else:
        setattr(TestModel, "model_name", model_name)
        model = TestModel

    caplog.clear()

    with raises:
        register_module(module_name=module_name, model=model)

        if isinstance(raises, does_not_raise):
            # Slightly random selection of checks
            assert short_name in MODULE_REGISTRY
            assert MODULE_REGISTRY[short_name].model is model
            assert isinstance(MODULE_REGISTRY[short_name].schema, dict)
            assert isinstance(MODULE_REGISTRY[short_name].constants_classes, dict)

        log_check(caplog=caplog, expected_log=exp_log)
