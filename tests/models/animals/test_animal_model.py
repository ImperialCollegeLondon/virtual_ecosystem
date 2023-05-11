"""Test module for animal_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import ERROR, INFO

import pytest
from numpy import datetime64, timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import InitialisationError


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
        timedelta64(1, "W"),
        datetime64("2022-11-01"),
        functional_group_list_instance,
    )

    # In cases where it passes then checks that the object has the right properties
    assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
    assert model.model_name == "animals"
    assert str(model) == "A animals model instance"
    assert (
        repr(model)
        == "AnimalModel(update_interval = 1 weeks, next_update = 2022-11-08)"
    )
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
                "core": {"timing": {"start_date": "2020-01-01"}},
                "animals": {
                    "model_time_step": "12 hours",
                    "functional_groups": (
                        ("carnivorous_bird", "bird", "carnivore"),
                        ("herbivorous_bird", "bird", "herbivore"),
                        ("carnivorous_mammal", "mammal", "carnivore"),
                        ("herbivorous_mammal", "mammal", "herbivore"),
                    ),
                },
            },
            timedelta64(12, "h"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the animal model successfully "
                    "extracted.",
                ),
            ),
        ),
        (
            {
                "core": {"timing": {"start_date": "2020-01-01"}},
                "animals": {"model_time_step": "20 interminable minutes"},
                "functional_groups": (
                    ("carnivorous_bird", "bird", "carnivore"),
                    ("herbivorous_bird", "bird", "herbivore"),
                    ("carnivorous_mammal", "mammal", "carnivore"),
                    ("herbivorous_mammal", "mammal", "herbivore"),
                ),
            },
            None,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "Model timing error: 'interminable' is not defined in the unit "
                    "registry",
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
        model = AnimalModel.from_config(data_instance, config)
        assert model.update_interval == time_interval
        assert (
            model.next_update
            == datetime64(config["core"]["timing"]["start_date"]) + time_interval
        )
        # Run the update step and check that next_update has incremented properly
        model.update()
        assert (
            model.next_update
            == datetime64(config["core"]["timing"]["start_date"]) + 2 * time_interval
        )
        assert len(model.communities) == 100

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)
