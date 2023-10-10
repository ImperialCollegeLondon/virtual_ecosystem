"""Test module for abiotic.abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import INFO

import pint
import pytest

from tests.conftest import log_check
from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel


def test_abiotic_model_initialization(
    dummy_climate_data,
    layer_roles_fixture,
):
    """Test `AbioticModel` initialization."""
    from virtual_rainforest.models.abiotic.constants import AbioticConsts

    # Initialize model
    model = AbioticModel(
        dummy_climate_data,
        pint.Quantity("1 hour"),
        soil_layers=[-0.5, -1.0],
        canopy_layers=10,
        constants=AbioticConsts(),
    )

    # In cases where it passes then checks that the object has the right properties
    assert set(
        [
            "setup",
            "spinup",
            "update",
            "cleanup",
        ]
    ).issubset(dir(model))
    assert model.model_name == "abiotic"
    assert repr(model) == "AbioticModel(update_interval = 1 hour)"
    assert model.layer_roles == layer_roles_fixture


@pytest.mark.parametrize(
    "config,time_interval,raises,expected_log_entries",
    [
        (
            {},
            None,
            pytest.raises(KeyError),
            (),  # This error isn't handled so doesn't generate logging
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "1 day",
                    },
                    "layers": {
                        "soil_layers": [-0.5, -1.0],
                        "canopy_layers": 10,
                    },
                },
            },
            pint.Quantity("1 day"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the abiotic model "
                    "successfully extracted.",
                ),
            ),
        ),
    ],
)
def test_generate_abiotic_model(
    caplog,
    dummy_climate_data,
    config,
    time_interval,
    raises,
    expected_log_entries,
    layer_roles_fixture,
):
    """Test that the initialisation of the abiotic model works as expected."""

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticModel.from_config(
            dummy_climate_data,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.layer_roles == layer_roles_fixture
        assert model.update_interval == time_interval

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
