"""Test module for cnp.py."""

import pytest

from virtual_ecosystem.models.animal.cnp import CNP


class TestCNP:
    """Test the CNP dataclass."""

    @pytest.mark.parametrize(
        "carbon, nitrogen, phosphorus, expected_total",
        [
            (10.0, 5.0, 2.0, 17.0),
            (0.0, 0.0, 0.0, 0.0),
            (1.2, 0.8, 0.5, 2.5),
        ],
    )
    def test_total(self, carbon, nitrogen, phosphorus, expected_total):
        """Test total mass calculation."""
        cnp = CNP(carbon, nitrogen, phosphorus)
        assert cnp.total == pytest.approx(expected_total)

    @pytest.mark.parametrize(
        "carbon, nitrogen, phosphorus, key, expected_value",
        [
            (10.0, 5.0, 2.0, "carbon", 10.0),
            (10.0, 5.0, 2.0, "nitrogen", 5.0),
            (10.0, 5.0, 2.0, "phosphorus", 2.0),
        ],
    )
    def test_getitem(self, carbon, nitrogen, phosphorus, key, expected_value):
        """Test dictionary-style access."""
        cnp = CNP(carbon, nitrogen, phosphorus)
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
                {"carbon": 3.0, "nitrogen": 2.0, "phosphorus": 1.0},
                (13.0, 7.0, 3.0),
                False,
            ),  # Regular addition
            # Successful subtractions
            (
                (10.0, 5.0, 2.0),
                {"carbon": -3.0, "nitrogen": -2.0, "phosphorus": -1.0},
                (7.0, 3.0, 1.0),
                False,
            ),  # Regular subtraction
            (
                (2.0, 2.0, 2.0),
                {"carbon": -1.0, "nitrogen": -1.0, "phosphorus": -1.0},
                (1.0, 1.0, 1.0),
                False,
            ),  # No negative totals
            # Error cases (negative totals)
            (
                (1.0, 1.0, 1.0),
                {"carbon": -2.0, "nitrogen": 0.0, "phosphorus": 0.0},
                None,
                True,
            ),  # Carbon negative
            (
                (1.0, 1.0, 1.0),
                {"carbon": 0.0, "nitrogen": -2.0, "phosphorus": 0.0},
                None,
                True,
            ),  # Nitrogen negative
            (
                (1.0, 1.0, 1.0),
                {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": -2.0},
                None,
                True,
            ),  # Phosphorus negative
            (
                (0.0, 0.0, 0.0),
                {"carbon": -0.1, "nitrogen": -0.1, "phosphorus": -0.1},
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
            assert cnp.carbon == pytest.approx(expected[0]), "Carbon mass mismatch"
            assert cnp.nitrogen == pytest.approx(expected[1]), "Nitrogen mass mismatch"
            assert cnp.phosphorus == pytest.approx(expected[2]), (
                "Phosphorus mass mismatch"
            )

    def test_from_dict(self):
        """Test creating CNP instance from a dictionary."""
        data = {"carbon": 10.0, "nitrogen": 5.0, "phosphorus": 2.0}
        cnp = CNP.from_dict(data)
        assert cnp.carbon == pytest.approx(10.0)
        assert cnp.nitrogen == pytest.approx(5.0)
        assert cnp.phosphorus == pytest.approx(2.0)

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

        assert proportions["carbon"] == pytest.approx(10.0 / total_mass)
        assert proportions["nitrogen"] == pytest.approx(5.0 / total_mass)
        assert proportions["phosphorus"] == pytest.approx(2.0 / total_mass)

    def test_get_proportions_zero_handling(self):
        """Test proportion calculation when total mass is zero."""
        cnp = CNP(0.0, 0.0, 0.0)
        proportions = cnp.get_proportions()
        assert proportions["carbon"] == 0.0
        assert proportions["nitrogen"] == 0.0
        assert proportions["phosphorus"] == 0.0


def test_find_microbial_stoichiometries(fixture_configuration):
    """Check that extraction of stoichiometries from microbial groups works."""
    from virtual_ecosystem.models.animal.cnp import find_microbial_stoichiometries

    expected_ratios = {
        "bacteria": {"nitrogen": 5.2, "phosphorus": 16.0},
        "saprotrophic_fungi": {"nitrogen": 6.5, "phosphorus": 40.0},
        "arbuscular_mycorrhiza": {"nitrogen": 18.0, "phosphorus": 120.0},
        "ectomycorrhiza": {"nitrogen": 18.0, "phosphorus": 120.0},
    }

    actual_ratios = find_microbial_stoichiometries(config=fixture_configuration)

    assert expected_ratios == actual_ratios
