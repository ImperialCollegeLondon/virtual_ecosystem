"""Test module for decay.py.

This module tests the functionality of decay.py
"""

import pytest


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            scavengeable_cnp=CNP(
                carbon=1.0007e-2, nitrogen=0.000133333332, phosphorus=1.33333332e-6
            ),
            decomposed_cnp=CNP(
                carbon=2.5e-5, nitrogen=3.3333333e-6, phosphorus=3.3333333e-8
            ),
        )

        assert pytest.approx(carcasses.scavengeable_cnp.carbon) == 1.0007e-2
        assert pytest.approx(carcasses.decomposed_cnp.carbon) == 2.5e-5
        assert pytest.approx(carcasses.scavengeable_cnp.nitrogen) == 0.000133333332
        assert pytest.approx(carcasses.decomposed_cnp.nitrogen) == 3.3333333e-6
        assert pytest.approx(carcasses.scavengeable_cnp.phosphorus) == 1.33333332e-6
        assert pytest.approx(carcasses.decomposed_cnp.phosphorus) == 3.3333333e-8

    def test_decomposed_nutrient_per_area(self):
        """Test conversion of decomposed carcass nutrient content to per area basis."""
        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            decomposed_cnp=CNP(
                carbon=2.5e-5, nitrogen=3.3333333e-6, phosphorus=3.3333333e-8
            )
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
        "carbon, nitrogen, phosphorus, expected_c, expected_n, expected_p,"
        "raises_exception",
        [
            (5.0, 1.0, 0.5, 5.0, 1.0, 0.5, False),  # Normal case
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False),  # Zero mass
            (-1.0, 1.0, 0.5, None, None, None, True),  # Negative value
        ],
    )
    def test_add_carcass(
        self,
        carbon,
        nitrogen,
        phosphorus,
        expected_c,
        expected_n,
        expected_p,
        raises_exception,
    ):
        """Test adding carcass mass to the pool with various inputs."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool()

        if raises_exception:
            with pytest.raises(ValueError):
                carcasses.add_carcass(carbon, nitrogen, phosphorus)
        else:
            carcasses.add_carcass(carbon, nitrogen, phosphorus)
            assert carcasses.scavengeable_cnp.carbon == pytest.approx(expected_c)
            assert carcasses.scavengeable_cnp.nitrogen == pytest.approx(expected_n)
            assert carcasses.scavengeable_cnp.phosphorus == pytest.approx(expected_p)

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

        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool(
            scavengeable_cnp=CNP(carbon=7.77e-5, nitrogen=1e-5, phosphorus=1e-7),
            decomposed_cnp=CNP(
                carbon=2.5e-5, nitrogen=3.3333333e-6, phosphorus=3.3333333e-8
            ),
        )

        assert pytest.approx(excrement.scavengeable_cnp.carbon) == 7.77e-5
        assert pytest.approx(excrement.decomposed_cnp.carbon) == 2.5e-5
        assert pytest.approx(excrement.scavengeable_cnp.nitrogen) == 1e-5
        assert pytest.approx(excrement.decomposed_cnp.nitrogen) == 3.3333333e-6
        assert pytest.approx(excrement.scavengeable_cnp.phosphorus) == 1e-7
        assert pytest.approx(excrement.decomposed_cnp.phosphorus) == 3.3333333e-8

    @pytest.mark.parametrize(
        "carbon, nitrogen, phosphorus, expected_c, expected_n, expected_p,"
        "raises_exception",
        [
            (5.0, 1.0, 0.5, 5.0, 1.0, 0.5, False),  # Normal case
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False),  # Zero mass
            (-1.0, 1.0, 0.5, None, None, None, True),  # Negative value
        ],
    )
    def test_add_excrement(
        self,
        carbon,
        nitrogen,
        phosphorus,
        expected_c,
        expected_n,
        expected_p,
        raises_exception,
    ):
        """Test adding excrement mass to the pool with various inputs."""
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool()

        if raises_exception:
            with pytest.raises(ValueError):
                excrement.add_excrement(carbon, nitrogen, phosphorus)
        else:
            excrement.add_excrement(carbon, nitrogen, phosphorus)
            assert excrement.scavengeable_cnp.carbon == pytest.approx(expected_c)
            assert excrement.scavengeable_cnp.nitrogen == pytest.approx(expected_n)
            assert excrement.scavengeable_cnp.phosphorus == pytest.approx(expected_p)

    def test_reset(self):
        """Test resetting of the excrement pool."""

        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool(
            decomposed_cnp=CNP(
                carbon=2.5e-5, nitrogen=3.3333333e-6, phosphorus=3.3333333e-8
            )
        )

        # Call reset (should set all values to 0.0)
        excrement.reset()

        assert excrement.decomposed_cnp.carbon == 0.0
        assert excrement.decomposed_cnp.nitrogen == 0.0
        assert excrement.decomposed_cnp.phosphorus == 0.0


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

        mock_data = mocker.MagicMock(spec=Data)
        pool_name = "above_metabolic"
        cell_area = 100.0
        litter_mass = np.array([0.5, 0.7, 1.0])
        c_n_ratio = np.array([20.0, 25.0, 30.0])
        c_p_ratio = np.array([100.0, 120.0, 140.0])

        mock_data.__getitem__.side_effect = lambda key: {
            f"litter_pool_{pool_name}": mocker.Mock(to_numpy=lambda: litter_mass),
            f"c_n_ratio_{pool_name}": mocker.Mock(to_numpy=lambda: c_n_ratio),
            f"c_p_ratio_{pool_name}": mocker.Mock(to_numpy=lambda: c_p_ratio),
        }[key]

        litter_pool = LitterPool(pool_name, mock_data, cell_area)

        for i, cnp in enumerate(litter_pool.mass_cnp):
            assert np.isclose(cnp.carbon, litter_mass[i] * cell_area)
            assert np.isclose(cnp.nitrogen, (litter_mass[i] * cell_area) / c_n_ratio[i])
            assert np.isclose(
                cnp.phosphorus, (litter_mass[i] * cell_area) / c_p_ratio[i]
            )

    def test_mass_current(self, mocker):
        """Test the mass_current property of LitterPool."""
        import numpy as np

        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import LitterPool

        litter_pool = mocker.Mock()
        litter_pool.mass_cnp = [CNP(c, c / 2, c / 4) for c in [10.0, 20.0, 30.0]]

        result = LitterPool.mass_current.__get__(litter_pool)
        assert np.allclose(result.values, [10.0, 20.0, 30.0])

    def test_get_eaten(self, mocker):
        """Test `get_eaten` method of LitterPool for correct nutrient consumption."""
        import numpy as np

        from virtual_ecosystem.models.animal.decay import LitterPool

        mock_data = mocker.MagicMock()
        pool_name = "test_pool"
        cell_area = 1.0
        litter_mass = np.array([100.0, 200.0, 300.0])
        c_n_ratio = np.array([10.0, 20.0, 30.0])
        c_p_ratio = np.array([40.0, 50.0, 60.0])

        mock_data.__getitem__.side_effect = lambda key: {
            f"litter_pool_{pool_name}": mocker.Mock(to_numpy=lambda: litter_mass),
            f"c_n_ratio_{pool_name}": mocker.Mock(to_numpy=lambda: c_n_ratio),
            f"c_p_ratio_{pool_name}": mocker.Mock(to_numpy=lambda: c_p_ratio),
        }[key]

        litter_pool = LitterPool(pool_name, mock_data, cell_area)
        detritivore = mocker.MagicMock()
        detritivore.functional_group.mechanical_efficiency = 0.8

        grid_cell_id = 1
        consumed_mass = 100.0
        cell_cnp = litter_pool.mass_cnp[grid_cell_id]

        total_mass_available = cell_cnp.total
        actual_consumed_mass = min(total_mass_available, consumed_mass) * 0.8

        nutrients = litter_pool.get_eaten(consumed_mass, detritivore, grid_cell_id)

        assert np.isclose(
            litter_pool.mass_cnp[grid_cell_id].total,
            total_mass_available - actual_consumed_mass,
        )

        nutrient_proportions = cell_cnp.get_proportions()
        expected_nutrients = {
            "carbon": actual_consumed_mass * nutrient_proportions["carbon"],
            "nitrogen": actual_consumed_mass * nutrient_proportions["nitrogen"],
            "phosphorus": actual_consumed_mass * nutrient_proportions["phosphorus"],
        }

        for key in expected_nutrients:
            assert np.isclose(nutrients[key], expected_nutrients[key]), (
                f"{key} nutrient mismatch. Expected {expected_nutrients[key]},"
                f" got {nutrients[key]}"
            )
