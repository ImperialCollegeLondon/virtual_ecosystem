"""Check that the constants loader helper function is working as expected."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import pytest

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    "cfg_strings,model_name,class_name,raises,exp_val,exp_log",
    [
        pytest.param(
            "[core]",
            "core",
            "CoreConsts",
            does_not_raise(),
            0.25,
            ((INFO, "Initialised core.CoreConsts from config"),),
            id="default_values",
        ),
        pytest.param(
            "[core.constants.CoreConsts]\ndepth_of_active_soil_layer=1.5",
            "core",
            "CoreConsts",
            does_not_raise(),
            1.5,
            ((INFO, "Initialised core.CoreConsts from config"),),
            id="configured_value",
        ),
        pytest.param(
            "[core.constants.CoreConsts]\nnot_a_valid_constant=432.1",
            "core",
            "CoreConsts",
            pytest.raises(ConfigurationError),
            None,
            ((CRITICAL, "Could not initialise core.CoreConsts from config"),),
            id="bad_configuration",
        ),
        pytest.param(
            "[core]\n[soil]\n",
            "soil",
            "SoilConsts",
            pytest.raises(KeyError),
            None,
            ((CRITICAL, "Configuration does not include module: soil"),),
            id="bad_configuration_does_not_include_constants",
        ),
        pytest.param(
            "[core]",
            "coral",
            "CoreConsts",
            pytest.raises(KeyError),
            None,
            ((CRITICAL, "Unknown or unregistered module in coral.CoreConsts"),),
            id="bad_module",
        ),
        pytest.param(
            "[core]",
            "core",
            "CoralConsts",
            pytest.raises(KeyError),
            None,
            ((CRITICAL, "Unknown constants class: core.CoralConsts"),),
            id="bad_constant_class",
        ),
    ],
)
def test_load_constants(
    caplog, cfg_strings, model_name, class_name, raises, exp_val, exp_log
):
    """Check that function to load in specified constants classes works as expected."""

    from scipy import constants  # type: ignore

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.core.constants_loader import load_constants
    from virtual_ecosystem.core.registry import register_module

    register_module("virtual_ecosystem.core")
    # Artificially create a configuration that omits the soil module. The soil module
    # should be registered by the config creation, but trap what happens if the config
    # doesn't match to the registered modules.
    config = Config(cfg_strings=cfg_strings)
    _ = config.pop("soil") if "soil" in config else None
    caplog.clear()

    with raises:
        constants_instance = load_constants(config, model_name, class_name)

        if isinstance(raises, does_not_raise):
            # All tests that are supposed to pass generate a CoreConsts object
            assert isinstance(constants_instance, CoreConsts)
            # The unconfigurable zero_Celsius should take the default value
            assert constants_instance.zero_Celsius == constants.zero_Celsius
            # Check the depth_of_active_soil_layer constant has been configured
            assert constants_instance.depth_of_active_soil_layer == exp_val

        log_check(caplog=caplog, expected_log=exp_log)
