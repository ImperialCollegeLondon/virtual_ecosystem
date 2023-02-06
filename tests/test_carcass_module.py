"""Test module for carcass_module.py.

This module tests the functionality of dummy_animal_module.py
"""


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_rainforest.models.carcasses.carcass_module import CarcassPool

        c1 = CarcassPool(1000.7, 1)
        assert c1.energy == 1000.7
