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
            scavengeable_cnp={"C": 1.0007e-2, "N": 0.000133333332, "P": 1.33333332e-6},
            decomposed_cnp={"C": 2.5e-5, "N": 3.3333333e-6, "P": 3.3333333e-8},
        )
        assert pytest.approx(carcasses.scavengeable_cnp["C"]) == 1.0007e-2
        assert pytest.approx(carcasses.decomposed_cnp["C"]) == 2.5e-5
        assert pytest.approx(carcasses.scavengeable_cnp["N"]) == 0.000133333332
        assert pytest.approx(carcasses.decomposed_cnp["N"]) == 3.3333333e-6
        assert pytest.approx(carcasses.scavengeable_cnp["P"]) == 1.33333332e-6
        assert pytest.approx(carcasses.decomposed_cnp["P"]) == 3.3333333e-8

    def test_decomposed_nutrient_per_area(self):
        """Test conversion of decomposed carcass nutrient content to per area basis."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            decomposed_cnp={"C": 2.5e-5, "N": 3.3333333e-6, "P": 3.3333333e-8}
        )

        assert (
            pytest.approx(carcasses.decomposed_nutrient_per_area("C", 10000)) == 2.5e-9
        )
        assert (
            pytest.approx(carcasses.decomposed_nutrient_per_area("N", 10000))
            == 3.3333333e-10
        )
        assert (
            pytest.approx(carcasses.decomposed_nutrient_per_area("P", 10000))
            == 3.3333333e-12
        )

        with pytest.raises(ValueError):
            carcasses.decomposed_nutrient_per_area("molybdenum", 10000)

    @pytest.mark.parametrize(
        "input_mass, expected_c, expected_n, expected_p, raises_exception",
        [
            ({"C": 5.0, "N": 1.0, "P": 0.5}, 5.0, 1.0, 0.5, False),  # Normal case
            ({"C": 0.0, "N": 0.0, "P": 0.0}, 0.0, 0.0, 0.0, False),  # Zero mass
            ({"C": -1.0, "N": 1.0, "P": 0.5}, None, None, None, True),  # Negative value
            ({"C": 5.0, "N": 1.0}, None, None, None, True),  # Missing key
        ],
    )
    def test_add_carcass(
        self, input_mass, expected_c, expected_n, expected_p, raises_exception
    ):
        """Test adding carcass mass to the pool with various inputs."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool()

        if raises_exception:
            with pytest.raises(ValueError):
                carcasses.add_carcass(input_mass)
        else:
            carcasses.add_carcass(input_mass)
            assert carcasses.scavengeable_cnp["C"] == expected_c
            assert carcasses.scavengeable_cnp["N"] == expected_n
            assert carcasses.scavengeable_cnp["P"] == expected_p

    def test_reset(self):
        """Test resetting of the carcass pool."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            decomposed_cnp={"C": 2.5e-5, "N": 3.3333333e-6, "P": 3.3333333e-8}
        )
        carcasses.reset()

        assert carcasses.decomposed_cnp["C"] == 0.0
        assert carcasses.decomposed_cnp["N"] == 0.0
        assert carcasses.decomposed_cnp["P"] == 0.0


class TestExcrementPool:
    """Test the ExcrementPool class."""

    def test_initialization(self):
        """Testing initialization of ExcrementPool."""
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool(
            scavengeable_cnp={"C": 7.77e-5, "N": 1e-5, "P": 1e-7},
            decomposed_cnp={"C": 2.5e-5, "N": 3.3333333e-6, "P": 3.3333333e-8},
        )
        assert pytest.approx(excrement.scavengeable_cnp["C"]) == 7.77e-5
        assert pytest.approx(excrement.decomposed_cnp["C"]) == 2.5e-5
        assert pytest.approx(excrement.scavengeable_cnp["N"]) == 1e-5
        assert pytest.approx(excrement.decomposed_cnp["N"]) == 3.3333333e-6
        assert pytest.approx(excrement.scavengeable_cnp["P"]) == 1e-7
        assert pytest.approx(excrement.decomposed_cnp["P"]) == 3.3333333e-8

    @pytest.mark.parametrize(
        "input_mass, expected_c, expected_n, expected_p, raises_exception",
        [
            ({"C": 5.0, "N": 1.0, "P": 0.5}, 5.0, 1.0, 0.5, False),  # Normal case
            ({"C": 0.0, "N": 0.0, "P": 0.0}, 0.0, 0.0, 0.0, False),  # Zero mass
            ({"C": -1.0, "N": 1.0, "P": 0.5}, None, None, None, True),  # Negative value
            ({"C": 5.0, "N": 1.0}, None, None, None, True),  # Missing key
        ],
    )
    def test_add_excrement(
        self, input_mass, expected_c, expected_n, expected_p, raises_exception
    ):
        """Test adding excrement mass to the pool with various inputs."""
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool()

        if raises_exception:
            with pytest.raises(ValueError):
                excrement.add_excrement(input_mass)
        else:
            excrement.add_excrement(input_mass)
            assert excrement.scavengeable_cnp["C"] == expected_c
            assert excrement.scavengeable_cnp["N"] == expected_n
            assert excrement.scavengeable_cnp["P"] == expected_p

    def test_reset(self):
        """Test resetting of the excrement pool."""
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool(
            decomposed_cnp={"C": 2.5e-5, "N": 3.3333333e-6, "P": 3.3333333e-8}
        )
        excrement.reset()

        assert excrement.decomposed_cnp["C"] == 0.0
        assert excrement.decomposed_cnp["N"] == 0.0
        assert excrement.decomposed_cnp["P"] == 0.0


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


class TestLitterPool:
    """Test the LitterPool class."""

    def test_initialization(self, mocker):
        """Test initialization of LitterPool."""

        import numpy as np

        from virtual_ecosystem.core.data import Data
        from virtual_ecosystem.models.animal.decay import LitterPool

        # Use MagicMock to allow dictionary-like access
        mock_data = mocker.MagicMock(spec=Data)

        # Define test parameters
        pool_name = "above_metabolic"
        cell_area = 100.0  # Example cell area

        # Create mock data values for litter pool and stoichiometric ratios
        litter_mass = np.array([0.5, 0.7, 1.0])  # kg C/m^2
        c_n_ratio = np.array([20.0, 25.0, 30.0])
        c_p_ratio = np.array([100.0, 120.0, 140.0])

        # Mock data to return NumPy arrays directly
        mock_data.__getitem__.side_effect = lambda key: {
            f"litter_pool_{pool_name}": mocker.Mock(to_numpy=lambda: litter_mass),
            f"c_n_ratio_{pool_name}": mocker.Mock(to_numpy=lambda: c_n_ratio),
            f"c_p_ratio_{pool_name}": mocker.Mock(to_numpy=lambda: c_p_ratio),
        }[key]

        # Initialize the LitterPool instance
        litter_pool = LitterPool(pool_name, mock_data, cell_area)

        # Expected mass values (converting from density to total mass)
        expected_carbon_mass = litter_mass * cell_area
        expected_nitrogen_mass = expected_carbon_mass / c_n_ratio
        expected_phosphorus_mass = expected_carbon_mass / c_p_ratio

        # Assertions to check initialization values
        assert np.allclose(litter_pool.mass_cnp["C"], expected_carbon_mass)
        assert np.allclose(litter_pool.mass_cnp["N"], expected_nitrogen_mass)
        assert np.allclose(litter_pool.mass_cnp["P"], expected_phosphorus_mass)
