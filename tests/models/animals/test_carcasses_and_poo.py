"""Test module for carcasses.py.

This module tests the functionality of carcasses.py
"""


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_rainforest.models.animals.carcasses_and_poo import CarcassPool

        c1 = CarcassPool(1000.7, 1)
        assert c1.stored_energy == 1000.7


class TestExcrementPool:
    """Test the ExcrementPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_rainforest.models.animals.carcasses_and_poo import ExcrementPool

        poo = ExcrementPool(25.0)
        # Test that function to calculate stored carbon works as expected
        assert poo.stored_energy == 25.0
        assert poo.stored_carbon(1.0) == 2.5e-5
        assert poo.stored_carbon(10.0) == 2.5e-6
        assert poo.stored_carbon(25.0) == 1.0e-6
        assert poo.stored_carbon(5000.0) == 5.0e-9
