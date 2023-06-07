"""Test module for animal_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import INFO

import pint
import pytest

from tests.conftest import log_check


@pytest.fixture
def functional_group_list_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list


def test_animal_model_initialization(
    caplog, data_instance, functional_group_list_instance
):
    """Test `AnimalModel` initialization."""
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    # Initialize model
    model = AnimalModel(
        data_instance,
        pint.Quantity("1 week"),
        functional_group_list_instance,
    )

    # In cases where it passes then checks that the object has the right properties
    assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
    assert model.model_name == "animals"
    assert str(model) == "A animals model instance"
    assert repr(model) == "AnimalModel(update_interval = 1 week)"
    assert type(model.communities) is dict


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
                        "update_interval": "7 days",
                    }
                },
                "animals": {
                    "model_time_step": "12 hours",
                    "functional_groups": (
                        ("carnivorous_bird", "bird", "carnivore", "endothermic"),
                        ("herbivorous_bird", "bird", "herbivore", "endothermic"),
                        ("carnivorous_mammal", "mammal", "carnivore", "endothermic"),
                        ("herbivorous_mammal", "mammal", "herbivore", "endothermic"),
                    ),
                },
            },
            pint.Quantity("7 days"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the animal model successfully "
                    "extracted.",
                ),
            ),
        ),
    ],
)
def test_generate_animal_model(
    caplog,
    data_instance,
    config,
    time_interval,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the animal model behaves as expected."""
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AnimalModel.from_config(
            data_instance,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.update_interval == time_interval
        # Run the update step (once this does something should check output)
        model.update()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
