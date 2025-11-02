"""Test module for animal_traits.py."""

import pytest
from pydantic import ValidationError

from virtual_ecosystem.models.animal.animal_traits import DietType, TaxaType
from virtual_ecosystem.models.animal.model_config import AnimalConstants


class TestAnimalConstants:
    """Tests for the AnimalConstants dataclass methods."""

    def test_get_population_density_terms_damuth(self):
        """Test Damuth method returns correct terms."""

        # Create instance with damuth method
        animal_consts = AnimalConstants(density_scaling_method="damuth")

        # Get terms for Mammal Herbivore
        result = animal_consts.get_population_density_terms(
            TaxaType.MAMMAL, DietType.HERBIVORE
        )

        # Expected result
        expected = animal_consts.damuths_law_terms[TaxaType.MAMMAL][DietType.HERBIVORE]

        # Assert they match
        assert result == expected

    def test_get_population_density_terms_madingley(self):
        """Test Madingley method returns correct terms."""

        # Create instance with madingley method
        animal_consts = AnimalConstants(density_scaling_method="madingley")

        # Get terms (taxa/diet ignored in madingley)
        result = animal_consts.get_population_density_terms(
            TaxaType.BIRD, DietType.CARNIVORE
        )

        # Assert it returns the default tuple
        assert result == animal_consts.madingley_biomass_scaling_terms

    def test_get_population_density_terms_invalid_method(self):
        """Test invalid scaling method raises ValueError."""

        # Ensure ValidationError is raised
        with pytest.raises(ValidationError):
            AnimalConstants(density_scaling_method="invalid_method")
