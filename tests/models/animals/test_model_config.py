"""Test the custom validation and serialisation on the animals.model_config module."""

import pytest

from virtual_ecosystem.models.animal.animal_traits import DietType


@pytest.mark.parametrize(
    argnames="deserialised,serialised",
    argvalues=(
        (DietType.CARNIVORE, "CARNIVORE"),
        (DietType.FRUIT | DietType.NECTAR, "FRUIT|NECTAR"),
    ),
)
def test_DietType_serialisation(deserialised, serialised):
    """Check the DietType serialisation functions."""
    from virtual_ecosystem.models.animal.model_config import (
        deserialise_diet_type,
        serialise_diet_type,
    )

    as_json = serialise_diet_type(deserialised)
    as_diet_type = deserialise_diet_type(serialised)

    assert as_json == serialised
    assert as_diet_type == deserialised


def test_AnimalConstants_dump_and_load():
    """Test the AnimalConstants writes and reads as expected."""

    from virtual_ecosystem.models.animal.model_config import AnimalConstants

    model = AnimalConstants()

    json_data = model.model_dump_json()

    # Check a DietType has been correctly serialised as text
    assert "CARNIVORE" in json_data

    new_model = AnimalConstants.model_validate_json(json_data)

    assert model == new_model
