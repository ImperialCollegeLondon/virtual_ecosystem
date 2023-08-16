"""Test module for carcasses.py.

This module tests the functionality of carcasses.py
"""


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_rainforest.models.animals.carcasses import CarcassPool

        c1 = CarcassPool(1000.7)
        assert c1.stored_energy == 1000.7
