"""Check that the system to register constants is working as expected."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO

import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    "model_name,class_name,raises,expected_log_entries",
    [
        (
            "litter",
            "LitterConsts",
            pytest.raises(ValueError),
            (
                (
                    CRITICAL,
                    "The constants class litter.LitterConsts is already registered",
                ),
            ),
        ),
        (
            "litter",
            "NonExistentConsts",
            pytest.raises(AttributeError),
            (
                (
                    CRITICAL,
                    "Registration for litter.NonExistentConsts constants class failed: "
                    "check log",
                ),
            ),
        ),
    ],
)
def test_register_constants_class(
    caplog, mocker, model_name, class_name, raises, expected_log_entries
):
    """Test that the function to register constant classes works as expected."""

    from virtual_rainforest.core.constants import register_constants_class

    # Check that construct_combined_schema fails as expected
    with raises:
        register_constants_class(model_name, class_name)

    # Then check that the correct (critical error) log messages are emitted
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config,raises,exp_log",
    [
        pytest.param(
            {
                "abiotic_simple": {
                    "constants": {
                        "AbioticSimpleConsts": {"air_temperature_gradient": -1.0}
                    }
                }
            },
            does_not_raise(),
            (),
            id="expected_constants",
        ),
        pytest.param(
            {
                "abiotic_simple": {
                    "constants": {
                        "AbioticSimpleConsts": {
                            "air_temperature_gradient": -1.0,
                            "invented_constant": 37.9,
                            "saturation_vapour_pressure_factor4": 0.07,
                        }
                    }
                }
            },
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for AbioticSimpleConsts: ",
                ),
                (
                    INFO,
                    "Valid names are as follows: ",
                ),
            ),
            id="unexpected_constants",
        ),
    ],
)
def test_check_valid_constant_names(caplog, config, raises, exp_log):
    """Check that function to check constants behaves as expected."""
    from virtual_rainforest.core.constants import check_valid_constant_names

    with raises:
        check_valid_constant_names(
            config, model_name="abiotic_simple", class_name="AbioticSimpleConsts"
        )

    # Final check that expected logging entries are produced
    log_check(caplog, exp_log)


@pytest.mark.parametrize(
    "config,model_name,class_name,raises",
    [
        pytest.param(
            {},
            "litter",
            "LitterConsts",
            does_not_raise(),
            id="empty_config",
        ),
        pytest.param(
            {
                "litter": {
                    "constants": {
                        "LitterConsts": {"litter_decomp_reference_temp": 35.0}
                    }
                }
            },
            "litter",
            "LitterConsts",
            does_not_raise(),
            id="full_config",
        ),
        pytest.param(
            {
                "not_a_model": {
                    "constants": {
                        "LitterConsts": {"litter_decomp_reference_temp": 35.0}
                    }
                }
            },
            "not_a_model",
            "LitterConsts",
            pytest.raises(KeyError),
            id="bad_model_name",
        ),
        pytest.param(
            {
                "litter": {
                    "constants": {"NotConsts": {"litter_decomp_reference_temp": 35.0}}
                }
            },
            "litter",
            "NotConsts",
            pytest.raises(KeyError),
            id="bad_class_name",
        ),
    ],
)
def test_load_constants(config, model_name, class_name, raises):
    """Check that function to load in specified constants classes works as expected."""
    from virtual_rainforest.core.constants import load_constants
    from virtual_rainforest.models.litter.constants import LitterConsts

    with raises:
        constants = load_constants(config, model_name, class_name)
        # All tests that are supposed to pass generate a LitterConsts object
        assert isinstance(constants, LitterConsts)
        # The litter_decomp_offset_temp should take the default value
        assert constants.litter_decomp_offset_temp == 31.79
        # If the config isn't empty then the litter_decomp_reference_temp should differ
        # from the default value
        if config:
            assert constants.litter_decomp_reference_temp == 35.0
        else:
            assert constants.litter_decomp_reference_temp == 40.0
