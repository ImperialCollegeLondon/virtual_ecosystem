"""Check that the ConstantsDataclass implementation is working as expected."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


def test_cannot_create_unfrozen_constants_dataclass():
    """Test users can't define mutable constants dataclasses."""
    from dataclasses import dataclass

    from virtual_rainforest.core.constants_class import ConstantsDataclass

    with pytest.raises(TypeError):
        # mypy warns about the very thing we're testing can't happen. That might mean
        # this test is redundant.
        @dataclass
        class Test(ConstantsDataclass):  # type: ignore [misc]
            a = 1


@pytest.mark.parametrize(
    "config,raises,exp_val,exp_log",
    [
        pytest.param(
            {},
            does_not_raise(),
            0.25,
            (),
            id="defaults_with_no_config",
        ),
        pytest.param(
            {"depth_of_active_soil_layer": 1.55},
            does_not_raise(),
            1.55,
            (),
            id="configured",
        ),
        pytest.param(
            {"plaiceholder": 432.1},
            pytest.raises(ConfigurationError),
            None,
            (
                (ERROR, "Unknown names supplied for CoreConsts: plaiceholder"),
                (INFO, "Valid names are: placeholder"),
            ),
            id="unknown_constant",
        ),
        pytest.param(
            {"zero_Celsius": 999.0},
            pytest.raises(ConfigurationError),
            None,
            (
                (ERROR, "Constant in CoreConsts not configurable: zero_Celsius"),
                (INFO, "Valid names are: placeholder"),
            ),
            id="unconfigurable_constant",
        ),
    ],
)
def test_ConstantsDataclass_from_config(caplog, config, raises, exp_val, exp_log):
    """Test failure and success modes of the ConstantsDataclass.from_config method."""
    from virtual_rainforest.core.constants import CoreConsts

    with raises:
        constants_instance = CoreConsts.from_config(config)

        if isinstance(raises, does_not_raise):
            assert constants_instance.depth_of_active_soil_layer == exp_val

        log_check(caplog=caplog, expected_log=exp_log)
