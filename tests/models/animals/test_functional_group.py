"""Test module for functional_group.py."""

import pytest


class TestFunctionalGroup:
    """Test Animal class."""

    @pytest.mark.parametrize(
        "taxa, diet, dam_law_exp, dam_law_coef, conv_eff",
        [
            ("mammal", "herbivore", -0.75, 4.23, 0.1),
            ("mammal", "carnivore", -0.75, 1.00, 0.25),
            ("bird", "herbivore", -0.75, 5.00, 0.1),
            ("bird", "carnivore", -0.75, 2.00, 0.25),
        ],
    )
    def test_initialization(self, taxa, diet, dam_law_exp, dam_law_coef, conv_eff):
        """Testing initialization of derived parameters for animal cohorts."""
        from virtual_rainforest.models.animals.functional_group import FunctionalGroup

        func_group = FunctionalGroup(taxa, diet)
        assert func_group.damuths_law_terms[0] == dam_law_exp
        assert func_group.damuths_law_terms[1] == dam_law_coef
        assert func_group.conversion_efficiency == conv_eff
