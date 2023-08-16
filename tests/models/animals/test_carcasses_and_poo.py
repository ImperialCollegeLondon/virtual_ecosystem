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
        assert poo.stored_energy == 25.0
