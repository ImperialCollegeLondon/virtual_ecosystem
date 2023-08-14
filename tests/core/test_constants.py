"""Check that the system to register constants is working as expected."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, INFO

import pytest

from tests.conftest import log_check


@pytest.mark.parametrize(
    "model_name,class_name,raises,expected_log_entries",
    [
        (
            "litter",
            "LitterConsts",
            does_not_raise(),
            (
                (
                    INFO,
                    "Constants class litter.LitterConsts registered",
                ),
            ),
        ),
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
