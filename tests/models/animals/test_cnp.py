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

    def test_add(self):
        """Test element-wise addition of two CNP objects."""
        cnp1 = CNP(10.0, 5.0, 2.0)
        cnp2 = CNP(3.0, 2.0, 1.0)
        result = cnp1.add(cnp2)

        assert result.carbon == pytest.approx(13.0)
        assert result.nitrogen == pytest.approx(7.0)
        assert result.phosphorus == pytest.approx(3.0)

    def test_subtract(self):
        """Test element-wise subtraction of two CNP objects."""
        cnp1 = CNP(10.0, 5.0, 2.0)
        cnp2 = CNP(3.0, 2.0, 1.0)
        result = cnp1.subtract(cnp2)

        assert result.carbon == pytest.approx(7.0)
        assert result.nitrogen == pytest.approx(3.0)
        assert result.phosphorus == pytest.approx(1.0)

    def test_to_dict(self):
        """Test conversion of CNP object to dictionary."""
        cnp = CNP(10.0, 5.0, 2.0)
        expected_dict = {"carbon": 10.0, "nitrogen": 5.0, "phosphorus": 2.0}
        assert cnp.to_dict() == expected_dict

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
