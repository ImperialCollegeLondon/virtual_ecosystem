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
        "flag_str, expected_count",
        [
            ("FOLIAGE", 1),
            ("FOLIAGE | FRUIT | FUNGI", 3),
            ("NONFEEDING", 0),
            (
                "HERBIVORE | CARCASSES | FOLIAGE",
                9,
            ),  # includes 9 from HERBIVORE + CARCASSES
        ],
    )
    def test_count_dietary_categories(self, flag_str, expected_count):
        """Test number of counted dietary categories from a DietType flag."""
        from virtual_ecosystem.models.animal.functional_group import DietType

        parts = [getattr(DietType, part.strip()) for part in flag_str.split("|")]
        flag = parts[0]
        for part in parts[1:]:
            flag |= part

        assert flag.count_dietary_categories() == expected_count


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
