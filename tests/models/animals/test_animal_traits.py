"""Test module for animal_traits.py."""

import pytest

from virtual_ecosystem.models.animal.animal_traits import DietType


class TestDietType:
    """Test the methods of the DietType class."""

    def test_single_flags(self):
        """Test individual diet flags exist and behave correctly."""

        assert DietType.FOLIAGE.name == "FOLIAGE"
        assert DietType.FRUIT.name == "FRUIT"
        assert DietType.VERTEBRATES.name == "VERTEBRATES"
        assert isinstance(DietType.FRUIT, DietType)

    def test_combined_flags(self):
        """Test combining diet flags using bitwise OR."""

        combo = DietType.FOLIAGE | DietType.FRUIT
        assert DietType.FOLIAGE in combo
        assert DietType.FRUIT in combo
        assert DietType.VERTEBRATES not in combo

    @pytest.mark.parametrize(
        "diet_string, expected_flag",
        [
            ("foliage", "FOLIAGE"),
            ("fruit", "FRUIT"),
            ("nectar", "NECTAR"),
            ("carcasses", "CARCASSES"),
            ("blood", "BLOOD"),
            ("waste", "WASTE"),
            ("detritus", "DETRITUS"),
            ("algae", "ALGAE"),
            ("wood", "WOOD"),
            ("invertebrates", "INVERTEBRATES"),
            ("fungi", "FUNGI"),
            ("seeds", "SEEDS"),
            ("flowers", "FLOWERS"),
            ("nonfeeding", "NONFEEDING"),
            ("foliage_fruit", "FOLIAGE|FRUIT"),
            ("fruit_blood", "FRUIT|BLOOD"),
            ("foliage_fruit_blood", "FOLIAGE|FRUIT|BLOOD"),
            ("algae_detritus_wood", "ALGAE|DETRITUS|WOOD"),
            ("carcasses_blood_waste", "CARCASSES|BLOOD|WASTE"),
            ("nectar_fungi_seeds", "NECTAR|FUNGI|SEEDS"),
            ("flowers_fruit_seeds", "FLOWERS|FRUIT|SEEDS"),
        ],
    )
    def test_parse(self, diet_string, expected_flag):
        """Test parse() with underscore-separated flag names."""
        from virtual_ecosystem.models.animal.animal_traits import DietType

        expected = None
        for part in expected_flag.split("|"):
            part_flag = getattr(DietType, part)
            expected = part_flag if expected is None else expected | part_flag

        result = DietType.parse(diet_string)
        assert result == expected

    def test_diettype_parse_composites(self):
        """Test the composite diets parse correctly."""
        from virtual_ecosystem.models.animal.animal_traits import DietType

        assert DietType.parse("carnivore") == DietType.CARNIVORE
        assert DietType.parse("herbivore") == DietType.HERBIVORE
        assert DietType.parse("omnivore") == DietType.OMNIVORE

    def test_parse_invalid(self):
        """Test that invalid parse strings raise ValueError."""

        with pytest.raises(ValueError):
            DietType.parse("moonlight")

    def test_coarse_category(self):
        """Test that coarse_category returns correct value."""

        assert DietType.FOLIAGE.coarse_category() == DietType.HERBIVORE
        assert DietType.VERTEBRATES.coarse_category() == DietType.CARNIVORE
        combo = DietType.FOLIAGE | DietType.VERTEBRATES
        assert combo.coarse_category() == DietType.OMNIVORE

    @pytest.mark.parametrize(
        "diet_string, expected_count",
        [
            # Single tag, single channel
            pytest.param("foliage", 1, id="foliage"),
            pytest.param("invertebrates", 1, id="invertebrates"),
            pytest.param("detritus", 1, id="detritus"),
            pytest.param("waste", 1, id="waste"),
            pytest.param("carcasses", 1, id="carcasses"),
            pytest.param("mushrooms", 1, id="mushrooms"),
            # Several tags sharing one channel: the bug case, where tags != calls
            pytest.param("foliage_fruit", 1, id="foliage_fruit"),
            pytest.param("foliage_fruit_seeds", 1, id="foliage_fruit_seeds"),
            pytest.param("vertebrates_invertebrates", 1, id="vert_invert"),
            pytest.param(
                "vertebrates_invertebrates_carcasses", 2, id="vert_invert_carcasses"
            ),
            # Several tags each with their own channel
            pytest.param(
                "detritus_fungi_pom_bacteria", 4, id="detritus_fungi_pom_bacteria"
            ),
            # Both array resources, but foraged by separate calls
            pytest.param("foliage_detritus", 2, id="foliage_detritus"),
            # Fruiting bodies and soil fungi are distinct channels
            pytest.param("mushrooms_fungi", 2, id="mushrooms_fungi"),
            # Composites: herbivory, detritivory
            pytest.param("herbivore", 2, id="herbivore"),
            # Composites: predation, carcasses, excrement (BLOOD/FISH add nothing)
            pytest.param("carnivore", 3, id="carnivore"),
            # Composites: herbivory, detritivory, predation, carcasses, excrement
            pytest.param("omnivore", 5, id="omnivore"),
            # No foraging route
            pytest.param("nonfeeding", 0, id="nonfeeding"),
            pytest.param("blood", 0, id="blood"),
            pytest.param("fish", 0, id="fish"),
        ],
    )
    def test_count_foraging_channels(
        self, diet_string: str, expected_count: int
    ) -> None:
        """Test the number of foraging channels engaged by a diet.

        Expected values are counted by hand from the foraging calls made in
        AnimalCohort.forage_cohort, not from FORAGING_CHANNELS, so that a wrong mask
        is caught rather than reproduced.
        """
        from virtual_ecosystem.models.animal.animal_traits import DietType

        diet = DietType.parse(diet_string)

        assert diet.count_foraging_channels() == expected_count

    def test_foraging_channels_are_disjoint(self) -> None:
        """Test that no diet flag is served by more than one foraging channel.

        A flag in two masks would engage two channels for a single tag and divide the
        foraging time budget by one too many.
        """
        from virtual_ecosystem.models.animal.animal_traits import (
            FORAGING_CHANNELS,
            DietType,
        )

        masks = list(FORAGING_CHANNELS.values())

        for i, first in enumerate(masks):
            for second in masks[i + 1 :]:
                assert first & second == DietType(0)


class TestVerticalOccupancy:
    """Test the methods of the VerticalOccupancy class."""

    @pytest.mark.parametrize(
        "occupancy_string, expected_flag",
        [
            ("soil", "SOIL"),
            ("ground", "GROUND"),
            ("canopy", "CANOPY"),
            ("soil_ground", "SOIL|GROUND"),
            ("ground_canopy", "GROUND|CANOPY"),
            ("soil_canopy", "SOIL|CANOPY"),
            ("soil_ground_canopy", "SOIL|GROUND|CANOPY"),
            ("canopy_ground", "CANOPY|GROUND"),  # order robustness
            ("ground_soil", "GROUND|SOIL"),
        ],
    )
    def test_parse_vertical_occupancy(self, occupancy_string, expected_flag):
        """Test parse() with underscore-separated vertical occupancy layers."""
        from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy

        expected = None
        for part in expected_flag.split("|"):
            part_flag = getattr(VerticalOccupancy, part)
            expected = part_flag if expected is None else expected | part_flag

        result = VerticalOccupancy.parse(occupancy_string)
        assert result == expected
