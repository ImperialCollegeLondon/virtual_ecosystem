"""Test module for decay.py.

This module tests the functionality of decay.py
"""

import pytest


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_rainforest.models.animals.decay import CarcassPool

        c1 = CarcassPool(1000.7, 0.0)
        assert pytest.approx(c1.scavengeable_energy) == 1000.7


class TestExcrementPool:
    """Test the ExcrementPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_rainforest.models.animals.decay import ExcrementPool

        poo = ExcrementPool(77.7, 25.0)
        # Test that function to calculate stored carbon works as expected
        assert pytest.approx(poo.scavengeable_energy) == 77.7
        assert pytest.approx(poo.decomposed_energy) == 25.0
        assert pytest.approx(poo.decomposed_carbon(1.0)) == 2.5e-5
        assert pytest.approx(poo.decomposed_carbon(10.0)) == 2.5e-6
        assert pytest.approx(poo.decomposed_carbon(25.0)) == 1.0e-6
        assert pytest.approx(poo.decomposed_carbon(5000.0)) == 5.0e-9
