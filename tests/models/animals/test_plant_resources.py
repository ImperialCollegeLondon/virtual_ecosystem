"""Test module for plant_resources.py."""


class TestPlantResources:
    """Test Plant class."""

    def test_get_eaten(
        self, plant_instance, herbivore_cohort_instance, excrement_instance
    ):
        """Testing get_eaten.

        Currently, this just tests rough execution. As the model gets paramterized,
        these tests will be expanded to specific values.
        """

        initial_plant_mass = plant_instance.mass_current
        initial_decay_pool_energy = excrement_instance.decomposed_energy

        # Execution
        plant_instance.get_eaten(herbivore_cohort_instance, excrement_instance)

        # Assertions
        assert plant_instance.mass_current < initial_plant_mass
        assert excrement_instance.decomposed_energy > initial_decay_pool_energy
