"""Check that the constants loader helper function is working as expected."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    "cfg_strings,model_name,class_name,raises,exp_val,exp_log",
    [
        pytest.param(
            "[core]",
            "core",
            "CoreConsts",
            does_not_raise(),
            123.4,
            ((INFO, "Initialised core.CoreConsts from config"),),
            id="default_values",
        ),
        pytest.param(
            "[core.constants.CoreConsts]\nplaceholder=432.1",
            "core",
            "CoreConsts",
            does_not_raise(),
            432.1,
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

    from scipy import constants

    from virtual_rainforest.core.config import Config
    from virtual_rainforest.core.constants import CoreConsts
    from virtual_rainforest.core.constants_loader import load_constants
    from virtual_rainforest.core.registry import register_module

    register_module("virtual_rainforest.core")

    config = Config(cfg_strings=cfg_strings)
    caplog.clear()

    with raises:
        constants_instance = load_constants(config, model_name, class_name)

        if isinstance(raises, does_not_raise):
            # All tests that are supposed to pass generate a CoreConsts object
            assert isinstance(constants_instance, CoreConsts)
            # The unconfigurable zero_Celsius should take the default value
            assert constants_instance.zero_Celsius == constants.zero_Celsius
            # Check the placeholder constant has been configured
            assert constants_instance.placeholder == exp_val

        log_check(caplog=caplog, expected_log=exp_log)
