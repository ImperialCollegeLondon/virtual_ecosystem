"""Test module for decay.py.

This module tests the functionality of decay.py
"""

import pytest


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            scavengeable_carbon=1.0007e-2,
            decomposed_carbon=2.5e-5,
            scavengeable_nitrogen=0.000133333332,
            decomposed_nitrogen=3.3333333e-6,
            scavengeable_phosphorus=1.33333332e-6,
            decomposed_phosphorus=3.3333333e-8,
        )
        assert pytest.approx(carcasses.scavengeable_carbon) == 1.0007e-2
        assert pytest.approx(carcasses.decomposed_carbon) == 2.5e-5
        assert pytest.approx(carcasses.scavengeable_nitrogen) == 0.000133333332
        assert pytest.approx(carcasses.decomposed_nitrogen) == 3.3333333e-6
        assert pytest.approx(carcasses.scavengeable_phosphorus) == 1.33333332e-6
        assert pytest.approx(carcasses.decomposed_phosphorus) == 3.3333333e-8
        assert (
            pytest.approx(carcasses.decomposed_nutrient_per_area("carbon", 10000))
            == 2.5e-9
        )
        assert (
            pytest.approx(carcasses.decomposed_nutrient_per_area("nitrogen", 10000))
            == 3.3333333e-10
        )
        assert (
            pytest.approx(carcasses.decomposed_nutrient_per_area("phosphorus", 10000))
            == 3.3333333e-12
        )
        with pytest.raises(AttributeError):
            carcasses.decomposed_nutrient_per_area("molybdenum", 10000)


class TestExcrementPool:
    """Test the ExcrementPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        poo = ExcrementPool(
            scavengeable_carbon=7.77e-5,
            decomposed_carbon=2.5e-5,
            scavengeable_nitrogen=1e-5,
            decomposed_nitrogen=3.3333333e-6,
            scavengeable_phosphorus=1e-7,
            decomposed_phosphorus=3.3333333e-8,
        )
        # Test that function to calculate stored carbon works as expected
        assert pytest.approx(poo.scavengeable_carbon) == 7.77e-5
        assert pytest.approx(poo.decomposed_carbon) == 2.5e-5
        assert pytest.approx(poo.scavengeable_nitrogen) == 1e-5
        assert pytest.approx(poo.decomposed_nitrogen) == 3.3333333e-6
        assert pytest.approx(poo.scavengeable_phosphorus) == 1e-7
        assert pytest.approx(poo.decomposed_phosphorus) == 3.3333333e-8
        assert (
            pytest.approx(poo.decomposed_nutrient_per_area("carbon", 10000)) == 2.5e-9
        )
        assert (
            pytest.approx(poo.decomposed_nutrient_per_area("nitrogen", 10000))
            == 3.3333333e-10
        )
        assert (
            pytest.approx(poo.decomposed_nutrient_per_area("phosphorus", 10000))
            == 3.3333333e-12
        )
        with pytest.raises(AttributeError):
            poo.decomposed_nutrient_per_area("molybdenum", 10000)


@pytest.mark.parametrize(
    argnames=[
        "decay_rate",
        "scavenging_rate",
        "expected_split",
    ],
    argvalues=[
        (0.25, 0.25, 0.5),
        (0.0625, 0.25, 0.2),
        (0.25, 0.0625, 0.8),
    ],
)
def test_find_decay_consumed_split(decay_rate, scavenging_rate, expected_split):
    """Test the function to find decay/scavenged split works as expected."""
    from virtual_ecosystem.models.animal.decay import find_decay_consumed_split

    actual_split = find_decay_consumed_split(
        microbial_decay_rate=decay_rate, animal_scavenging_rate=scavenging_rate
    )

    assert actual_split == expected_split
