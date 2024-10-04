"""Test module for plant_resources.py."""


class TestPlantResources:
    """Test Plant class."""

    def test_get_eaten(self, plant_instance, herbivore_cohort_instance):
        """Test the get_eaten method for PlantResources."""
        import pytest

        consumed_mass = 50.0  # Define a mass to be consumed for the test
        initial_mass_current = plant_instance.mass_current

        actual_mass_gain, actual_excess_mass = plant_instance.get_eaten(
            consumed_mass, herbivore_cohort_instance
        )

        # Check if the plant mass has been correctly reduced
        assert plant_instance.mass_current == pytest.approx(
            initial_mass_current - consumed_mass
        ), "Plant mass should be reduced by the consumed amount."

        # Check if the actual mass gain matches the expected value after
        # efficiency adjustments
        expected_mass_gain = (
            consumed_mass
            * herbivore_cohort_instance.functional_group.mechanical_efficiency
            * herbivore_cohort_instance.functional_group.conversion_efficiency
        )
        assert actual_mass_gain == pytest.approx(
            expected_mass_gain
        ), "Actual mass gain should match expected value after efficiency adjustments."

        # Check if the excess mass has been correctly added to the excrement pool
        excess_mass = consumed_mass * (
            1 - herbivore_cohort_instance.functional_group.mechanical_efficiency
        )
        assert actual_excess_mass == pytest.approx(
            excess_mass
        ), "Excrement pool energy should increase by energy value of the excess mass."
