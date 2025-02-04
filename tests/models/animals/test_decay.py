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
            scavengeable_cnp={
                "carbon": 1.0007e-2,
                "nitrogen": 0.000133333332,
                "phosphorus": 1.33333332e-6,
            },
            decomposed_cnp={
                "carbon": 2.5e-5,
                "nitrogen": 3.3333333e-6,
                "phosphorus": 3.3333333e-8,
            },
        )
        assert pytest.approx(carcasses.scavengeable_cnp["carbon"]) == 1.0007e-2
        assert pytest.approx(carcasses.decomposed_cnp["carbon"]) == 2.5e-5
        assert pytest.approx(carcasses.scavengeable_cnp["nitrogen"]) == 0.000133333332
        assert pytest.approx(carcasses.decomposed_cnp["nitrogen"]) == 3.3333333e-6
        assert pytest.approx(carcasses.scavengeable_cnp["phosphorus"]) == 1.33333332e-6
        assert pytest.approx(carcasses.decomposed_cnp["phosphorus"]) == 3.3333333e-8

    def test_decomposed_nutrient_per_area(self):
        """Test conversion of decomposed carcass nutrient content to per area basis."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            decomposed_cnp={
                "carbon": 2.5e-5,
                "nitrogen": 3.3333333e-6,
                "phosphorus": 3.3333333e-8,
            }
        )

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

        with pytest.raises(ValueError):
            carcasses.decomposed_nutrient_per_area("molybdenum", 10000)

    @pytest.mark.parametrize(
        "input_mass, expected_c, expected_n, expected_p, raises_exception",
        [
            (
                {"carbon": 5.0, "nitrogen": 1.0, "phosphorus": 0.5},
                5.0,
                1.0,
                0.5,
                False,
            ),  # Normal case
            (
                {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0},
                0.0,
                0.0,
                0.0,
                False,
            ),  # Zero mass
            (
                {"carbon": -1.0, "nitrogen": 1.0, "phosphorus": 0.5},
                None,
                None,
                None,
                True,
            ),  # Negative value
            ({"carbon": 5.0, "nitrogen": 1.0}, None, None, None, True),  # Missing key
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
            assert carcasses.scavengeable_cnp["carbon"] == expected_c
            assert carcasses.scavengeable_cnp["nitrogen"] == expected_n
            assert carcasses.scavengeable_cnp["phosphorus"] == expected_p

    def test_reset(self):
        """Test resetting of the carcass pool."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            decomposed_cnp={
                "carbon": 2.5e-5,
                "nitrogen": 3.3333333e-6,
                "phosphorus": 3.3333333e-8,
            }
        )
        carcasses.reset()

        assert carcasses.decomposed_cnp["carbon"] == 0.0
        assert carcasses.decomposed_cnp["nitrogen"] == 0.0
        assert carcasses.decomposed_cnp["phosphorus"] == 0.0


class TestExcrementPool:
    """Test the ExcrementPool class."""

    def test_initialization(self):
        """Testing initialization of ExcrementPool."""
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool(
            scavengeable_cnp={"carbon": 7.77e-5, "nitrogen": 1e-5, "phosphorus": 1e-7},
            decomposed_cnp={
                "carbon": 2.5e-5,
                "nitrogen": 3.3333333e-6,
                "phosphorus": 3.3333333e-8,
            },
        )
        assert pytest.approx(excrement.scavengeable_cnp["carbon"]) == 7.77e-5
        assert pytest.approx(excrement.decomposed_cnp["carbon"]) == 2.5e-5
        assert pytest.approx(excrement.scavengeable_cnp["nitrogen"]) == 1e-5
        assert pytest.approx(excrement.decomposed_cnp["nitrogen"]) == 3.3333333e-6
        assert pytest.approx(excrement.scavengeable_cnp["phosphorus"]) == 1e-7
        assert pytest.approx(excrement.decomposed_cnp["phosphorus"]) == 3.3333333e-8

    @pytest.mark.parametrize(
        "input_mass, expected_c, expected_n, expected_p, raises_exception",
        [
            (
                {"carbon": 5.0, "nitrogen": 1.0, "phosphorus": 0.5},
                5.0,
                1.0,
                0.5,
                False,
            ),  # Normal case
            (
                {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0},
                0.0,
                0.0,
                0.0,
                False,
            ),  # Zero mass
            (
                {"carbon": -1.0, "nitrogen": 1.0, "phosphorus": 0.5},
                None,
                None,
                None,
                True,
            ),  # Negative value
            ({"carbon": 5.0, "nitrogen": 1.0}, None, None, None, True),  # Missing key
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
            assert excrement.scavengeable_cnp["carbon"] == expected_c
            assert excrement.scavengeable_cnp["nitrogen"] == expected_n
            assert excrement.scavengeable_cnp["phosphorus"] == expected_p

    def test_reset(self):
        """Test resetting of the excrement pool."""
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool(
            decomposed_cnp={
                "carbon": 2.5e-5,
                "nitrogen": 3.3333333e-6,
                "phosphorus": 3.3333333e-8,
            }
        )
        excrement.reset()

        assert excrement.decomposed_cnp["carbon"] == 0.0
        assert excrement.decomposed_cnp["nitrogen"] == 0.0
        assert excrement.decomposed_cnp["phosphorus"] == 0.0


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
        assert np.allclose(litter_pool.mass_cnp["carbon"], expected_carbon_mass)
        assert np.allclose(litter_pool.mass_cnp["nitrogen"], expected_nitrogen_mass)
        assert np.allclose(litter_pool.mass_cnp["phosphorus"], expected_phosphorus_mass)

    def test_mass_current(self, litter_pool_instance):
        """Test that mass_current correctly returns an xarray DataArray."""
        import numpy as np
        from xarray import DataArray

        # Call mass_current
        mass_current = litter_pool_instance.mass_current

        # Check that it returns an xarray DataArray
        assert isinstance(mass_current, DataArray), "mass_current should be a DataArray"

        # Ensure dimensions match expected structure
        assert "cell_id" in mass_current.dims, (
            "mass_current should have 'cell_id' dimension"
        )

        # Check that mass_current values match sum of individual nutrient masses
        expected_mass_current = sum(litter_pool_instance.mass_cnp.values())
        assert np.allclose(mass_current.values, expected_mass_current), (
            f"Mismatch: Expected {expected_mass_current}, Got {mass_current.values}"
        )

    def test_get_eaten(self, litter_pool_instance, caterpillar_cohort_instance):
        """Test the get_eaten method using the litter_pool_instance fixture."""

        import numpy as np

        # Define test parameters
        grid_cell_id = 1  # Test a specific grid cell
        consumed_mass = 50.0  # Mass intended to be consumed

        # Use real consumer instance (caterpillar cohort)
        detritivore = caterpillar_cohort_instance
        detritivore.functional_group.mechanical_efficiency = 0.8  # Example value

        # Store initial mass values for each nutrient before calling get_eaten
        initial_mass_c = litter_pool_instance.mass_cnp["carbon"][grid_cell_id]
        initial_mass_n = litter_pool_instance.mass_cnp["nitrogen"][grid_cell_id]
        initial_mass_p = litter_pool_instance.mass_cnp["phosphorus"][grid_cell_id]

        # Compute total initial mass in the litter pool (before modification)
        initial_mass_current = initial_mass_c + initial_mass_n + initial_mass_p

        # Debugging output
        print(
            f"Initial C: {initial_mass_c}, Initial N: {initial_mass_n}, Initial P:"
            f"{initial_mass_p}"
        )
        print(f"Initial Total Mass: {initial_mass_current}")

        # Call get_eaten method on the existing fixture instance
        nutrient_gain = litter_pool_instance.get_eaten(
            consumed_mass, detritivore, grid_cell_id
        )

        # Calculate expected nutrient consumption using the pre-update mass values
        actual_consumed_mass = (
            consumed_mass * detritivore.functional_group.mechanical_efficiency
        )
        expected_nutrient_gain = {
            "carbon": actual_consumed_mass * (initial_mass_c / initial_mass_current),
            "nitrogen": actual_consumed_mass * (initial_mass_n / initial_mass_current),
            "phosphorus": actual_consumed_mass
            * (initial_mass_p / initial_mass_current),
        }

        # Debugging output
        print(
            f"Expected C Gain: {expected_nutrient_gain['C']}, Actual C Gain:"
            f"{nutrient_gain['C']}"
        )
        print(
            f"Expected N Gain: {expected_nutrient_gain['N']}, Actual N Gain:"
            f"{nutrient_gain['N']}"
        )
        print(
            f"Expected P Gain: {expected_nutrient_gain['P']}, Actual P Gain:"
            f"{nutrient_gain['P']}"
        )

        # Assertions to check correct nutrient reduction and return values
        assert np.allclose(
            nutrient_gain["carbon"], expected_nutrient_gain["carbon"], atol=1e-6
        ), f"Mismatch: Expected {expected_nutrient_gain['C']}, Got {nutrient_gain['C']}"
        assert np.allclose(
            nutrient_gain["nitrogen"], expected_nutrient_gain["nitrogen"], atol=1e-6
        ), f"Mismatch: Expected {expected_nutrient_gain['N']}, Got {nutrient_gain['N']}"
        assert np.allclose(
            nutrient_gain["phosphorus"], expected_nutrient_gain["phosphorus"], atol=1e-6
        ), f"Mismatch: Expected {expected_nutrient_gain['P']}, Got {nutrient_gain['P']}"

        # **✅ Corrected Assertions for Mass Reduction**
        assert np.allclose(
            litter_pool_instance.mass_cnp["carbon"][grid_cell_id],
            initial_mass_c - expected_nutrient_gain["carbon"],
        ), "C mass not reduced correctly."

        assert np.allclose(
            litter_pool_instance.mass_cnp["nitrogen"][grid_cell_id],
            initial_mass_n
            - expected_nutrient_gain["nitrogen"],  # ✅ Corrected from initial_mass_c
        ), "N mass not reduced correctly."

        assert np.allclose(
            litter_pool_instance.mass_cnp["phosphorus"][grid_cell_id],
            initial_mass_p - expected_nutrient_gain["phosphorus"],
        ), "P mass not reduced correctly."
