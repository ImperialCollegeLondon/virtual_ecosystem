"""Test module for plant_resources.py."""

import pytest


class TestPlantResources:
    """Test Plant class."""

    def test_get_eaten(self, plant_instance, herbivore_cohort_instance):
        """Test the get_eaten method for PlantResources."""

        consumed_mass = 50.0  # Define a mass to be consumed for the test
        initial_mass_current = plant_instance.mass_current

        # Call the method
        actual_mass_gain, excess_mass = plant_instance.get_eaten(
            consumed_mass, herbivore_cohort_instance
        )

        # Check if the plant mass has been correctly reduced
        assert plant_instance.mass_current == pytest.approx(
            initial_mass_current - consumed_mass
        ), "Plant mass should be reduced by the consumed amount."

        # Expected mechanical and conversion efficiency calculations
        expected_mass_gain_total = (
            consumed_mass
            * herbivore_cohort_instance.functional_group.mechanical_efficiency
            * herbivore_cohort_instance.functional_group.conversion_efficiency
        )

        # Expected nutrient gains in C, N, P
        expected_mass_gain = {
            element: expected_mass_gain_total * proportion
            for element, proportion in plant_instance.cnp_proportions.items()
        }

        # Check if the actual mass gain matches the expected value for each element
        for nutrient in expected_mass_gain:
            assert actual_mass_gain[nutrient] == pytest.approx(
                expected_mass_gain[nutrient], rel=1e-6
            ), (
                f"Mismatch in {nutrient}: Expected {expected_mass_gain[nutrient]}, "
                f"Got {actual_mass_gain[nutrient]}"
            )

        # Expected excess mass calculations
        expected_excess_mass_total = consumed_mass * (
            1 - herbivore_cohort_instance.functional_group.mechanical_efficiency
        )

        expected_excess_mass = {
            element: expected_excess_mass_total * proportion
            for element, proportion in plant_instance.cnp_proportions.items()
        }

        # Check if the excess mass has been calculated correctly
        for nutrient in expected_excess_mass:
            assert excess_mass[nutrient] == pytest.approx(
                expected_excess_mass[nutrient], rel=1e-6
            ), (
                f"Mismatch in {nutrient} excess mass:"
                f"Expected {expected_excess_mass[nutrient]}, "
                f"Got {excess_mass[nutrient]}"
            )
