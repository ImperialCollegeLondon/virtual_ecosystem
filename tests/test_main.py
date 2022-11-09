"""Test module for main.py (and associated functionality).

This module tests both the main simulation function `vr_run` and the other functions
defined in main.py that it calls.
"""

from logging import ERROR, INFO

import pytest

from virtual_rainforest.core.model import BaseModel
from virtual_rainforest.main import select_models

from .conftest import log_check


@pytest.mark.parametrize(
    "model_list,no_models,expected_log_entries",
    [
        (
            ["soil"],  # valid input
            1,
            (
                (
                    INFO,
                    "Attempting to configure the following models: ['soil']",
                ),
            ),
        ),
        (
            ["soil", "core"],
            1,
            (
                (
                    INFO,
                    "Attempting to configure the following models: ['soil']",
                ),
            ),
        ),
        (
            ["soil", "freshwater"],  # Model that hasn't been defined
            0,
            (
                (
                    INFO,
                    "Attempting to configure the following models: ['soil', "
                    "'freshwater']",
                ),
                (
                    ERROR,
                    "The following models cannot be configured as they are not found in"
                    " the registry: ['freshwater']",
                ),
            ),
        ),
    ],
)
def test_select_models(caplog, model_list, no_models, expected_log_entries):
    """Test the model selecting function."""

    models = select_models(model_list)

    log_check(caplog, expected_log_entries)

    # Finally check that output is as expected
    if no_models > 0:
        assert len(models) == no_models
        assert all([type(model) == type(BaseModel) for model in models])
    else:
        assert models is None
