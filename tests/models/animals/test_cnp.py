"""Test module for cnp.py."""

import pytest

from virtual_ecosystem.models.animal.cnp import CNP


class TestCNP:
    """Test the CNP dataclass."""

    @pytest.mark.parametrize(
        "C, N, P, expected_total",
        [
            (10.0, 5.0, 2.0, 17.0),
            (0.0, 0.0, 0.0, 0.0),
            (1.2, 0.8, 0.5, 2.5),
        ],
    )
    def test_total(self, C, N, P, expected_total):
        """Test total mass calculation."""
        cnp = CNP(C, N, P)
        assert cnp.total == pytest.approx(expected_total)

    @pytest.mark.parametrize(
        "C, N, P, key, expected_value",
        [
            (10.0, 5.0, 2.0, "C", 10.0),
            (10.0, 5.0, 2.0, "N", 5.0),
            (10.0, 5.0, 2.0, "P", 2.0),
        ],
    )
    def test_getitem(self, C, N, P, key, expected_value):
        """Test dictionary-style access."""
        cnp = CNP(C, N, P)
        assert cnp[key] == pytest.approx(expected_value)

    def test_getitem_invalid_key(self):
        """Test invalid dictionary-style key raises KeyError."""
        cnp = CNP(10.0, 5.0, 2.0)
        with pytest.raises(KeyError):
            _ = cnp["oxygen"]

    @pytest.mark.parametrize(
        "initial, update_values, expected, expect_error",
        [
            # Successful additions
            (
                (10.0, 5.0, 2.0),
                {"C": 3.0, "N": 2.0, "P": 1.0},
                (13.0, 7.0, 3.0),
                False,
            ),  # Regular addition
            # Successful subtractions
            (
                (10.0, 5.0, 2.0),
                {"C": -3.0, "N": -2.0, "P": -1.0},
                (7.0, 3.0, 1.0),
                False,
            ),  # Regular subtraction
            (
                (2.0, 2.0, 2.0),
                {"C": -1.0, "N": -1.0, "P": -1.0},
                (1.0, 1.0, 1.0),
                False,
            ),  # No negative totals
            # Error cases (negative totals)
            (
                (1.0, 1.0, 1.0),
                {"C": -2.0, "N": 0.0, "P": 0.0},
                None,
                True,
            ),  # C negative
            (
                (1.0, 1.0, 1.0),
                {"C": 0.0, "N": -2.0, "P": 0.0},
                None,
                True,
            ),  # Nitrogen negative
            (
                (1.0, 1.0, 1.0),
                {"C": 0.0, "N": 0.0, "P": -2.0},
                None,
                True,
            ),  # Phosphorus negative
            (
                (0.0, 0.0, 0.0),
                {"C": -0.1, "N": -0.1, "P": -0.1},
                None,
                True,
            ),  # All negative from zero
        ],
    )
    def test_update(self, initial, update_values, expected, expect_error):
        """Test the update method for additions, subtractions, and errors."""
        cnp = CNP(*initial)

        if expect_error:
            with pytest.raises(ValueError, match="mass cannot be negative"):
                cnp.update(**update_values)
        else:
            cnp.update(**update_values)
            assert cnp.C == pytest.approx(expected[0]), "Carbon mass mismatch"
            assert cnp.N == pytest.approx(expected[1]), "Nitrogen mass mismatch"
            assert cnp.P == pytest.approx(expected[2]), "Phosphorus mass mismatch"

    def test_from_dict(self):
        """Test creating CNP instance from a dictionary."""
        data = {"C": 10.0, "N": 5.0, "P": 2.0}
        cnp = CNP.from_dict(data)
        assert cnp.C == pytest.approx(10.0)
        assert cnp.N == pytest.approx(5.0)
        assert cnp.P == pytest.approx(2.0)

    def test_get_ratios(self):
        """Test calculation of C:N and C:P ratios."""
        cnp = CNP(10.0, 5.0, 2.0)
        ratios = cnp.get_ratios()
        assert ratios["C:N"] == pytest.approx(2.0)
        assert ratios["C:P"] == pytest.approx(5.0)

    def test_get_ratios_zero_handling(self):
        """Test C:N and C:P ratio calculation when denominator is zero."""
        cnp = CNP(10.0, 0.0, 0.0)
        ratios = cnp.get_ratios()
        assert ratios["C:N"] == 0.0  # Should avoid division by zero
        assert ratios["C:P"] == 0.0

    def test_get_proportions(self):
        """Test calculation of element proportions relative to total mass."""
        cnp = CNP(10.0, 5.0, 2.0)
        proportions = cnp.get_proportions()
        total_mass = 17.0

        assert proportions["C"] == pytest.approx(10.0 / total_mass)
        assert proportions["N"] == pytest.approx(5.0 / total_mass)
        assert proportions["P"] == pytest.approx(2.0 / total_mass)

    def test_get_proportions_zero_handling(self):
        """Test proportion calculation when total mass is zero."""
        cnp = CNP(0.0, 0.0, 0.0)
        proportions = cnp.get_proportions()
        assert proportions["C"] == 0.0
        assert proportions["N"] == 0.0
        assert proportions["P"] == 0.0


def test_find_microbial_stoichiometries(fixture_configuration):
    """Check that extraction of stoichiometries from microbial groups works."""
    from virtual_ecosystem.models.animal.cnp import find_microbial_stoichiometries

    expected_ratios = {
        "bacteria": {"N": 5.2, "P": 16.0},
        "saprotrophic_fungi": {"N": 6.5, "P": 40.0},
        "arbuscular_mycorrhiza": {"N": 18.0, "P": 120.0},
        "ectomycorrhiza": {"N": 18.0, "P": 120.0},
    }

    actual_ratios = find_microbial_stoichiometries(config=fixture_configuration)

    assert expected_ratios == actual_ratios
