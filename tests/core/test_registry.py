"""Test the registry functionality."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import pytest

from tests.conftest import log_check


@pytest.mark.parametrize(
    argnames="module_name, raises, exp_log",
    argvalues=[
        pytest.param(
            "virtual_ecosystem.core",
            does_not_raise(),
            (
                (INFO, "Registering module: virtual_ecosystem.core"),
                (
                    INFO,
                    "Configuration class registered for virtual_ecosystem.core",
                ),
            ),
            id="core_import_good",
        ),
        pytest.param(
            "virtual_ecosystem.models.testing",
            does_not_raise(),
            (
                (INFO, "Registering module: virtual_ecosystem.models.testing"),
                (
                    INFO,
                    "Registering model class for "
                    "virtual_ecosystem.models.testing: TestingModel",
                ),
                (
                    INFO,
                    "Configuration class registered for "
                    "virtual_ecosystem.models.testing",
                ),
            ),
            id="testing_import_good",
        ),
        pytest.param(
            "tests.core.test_modules.one_model",
            does_not_raise(),
            (
                (INFO, "Registering module: tests.core.test_modules.one_model"),
                (
                    INFO,
                    "Registering model class for "
                    "tests.core.test_modules.one_model: OneModelModel",
                ),
                (
                    INFO,
                    "Configuration class registered for "
                    "tests.core.test_modules.one_model",
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
def test_register_module(caplog, module_name, raises, exp_log):
    """Test the registry loading.

    This runs tests on the actual core and testing modules and then uses some local
    badly formatted models to check error handling.
    """

    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.core.configuration import Configuration
    from virtual_ecosystem.core.registry import (
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

            assert issubclass(mod_info.config, Configuration)

        # Check the last N entries in the log match the expectation.
        log_check(
            caplog=caplog, expected_log=exp_log, subset=slice(-len(exp_log), None, None)
        )


@pytest.mark.parametrize(
    argnames="module_name, raises, exp_log",
    argvalues=[
        pytest.param(
            "virtual_ecosystem.disturbances.disturbance_testing",
            does_not_raise(),
            (
                (
                    INFO,
                    "Registering module: "
                    "virtual_ecosystem.disturbances.disturbance_testing",
                ),
                (
                    INFO,
                    "Registering model class for "
                    "virtual_ecosystem.disturbances.disturbance_testing: "
                    "DisturbanceTestingModel",
                ),
                (
                    INFO,
                    "Configuration class registered for "
                    "virtual_ecosystem.disturbances.disturbance_testing",
                ),
            ),
            id="disturbance_testing_import_good",
        ),
    ],
)
def test_register_disturbance(caplog, module_name, raises, exp_log):
    """Test the registry loading.

    This runs tests on the actual core and testing modules and then uses some local
    badly formatted models to check error handling.
    """

    from virtual_ecosystem.core.base_model import BaseDisturbance
    from virtual_ecosystem.core.configuration import Configuration
    from virtual_ecosystem.core.registry import (
        DISTURBANCE_REGISTRY,
        ModuleInfo,
        register_disturbance,
    )

    # Get the short name
    _, _, short_name = module_name.rpartition(".")

    caplog.clear()

    with raises:
        register_disturbance(module_name=module_name)

        if isinstance(raises, does_not_raise):
            # Test the detailed structure of the registry for the module
            assert short_name in DISTURBANCE_REGISTRY
            mod_info = DISTURBANCE_REGISTRY[short_name]
            assert isinstance(mod_info, ModuleInfo)

            if not mod_info.is_core:
                assert issubclass(mod_info.model, BaseDisturbance)

            assert issubclass(mod_info.config, Configuration)

        # Check the last N entries in the log match the expectation.
        log_check(
            caplog=caplog, expected_log=exp_log, subset=slice(-len(exp_log), None, None)
        )
