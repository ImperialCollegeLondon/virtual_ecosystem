"""Test module for decay.py.

This module tests the functionality of decay.py
"""

from contextlib import nullcontext as does_not_raise

import pytest


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            scavengeable_cnp=CNP(C=1.0007e-2, N=0.000133333332, P=1.33333332e-6),
            decomposed_cnp=CNP(C=2.5e-5, N=3.3333333e-6, P=3.3333333e-8),
        )

        assert pytest.approx(carcasses.scavengeable_cnp.C) == 1.0007e-2
        assert pytest.approx(carcasses.decomposed_cnp.C) == 2.5e-5
        assert pytest.approx(carcasses.scavengeable_cnp.N) == 0.000133333332
        assert pytest.approx(carcasses.decomposed_cnp.N) == 3.3333333e-6
        assert pytest.approx(carcasses.scavengeable_cnp.P) == 1.33333332e-6
        assert pytest.approx(carcasses.decomposed_cnp.P) == 3.3333333e-8

    def test_decomposed_nutrient_per_area(self):
        """Test conversion of decomposed carcass nutrient content to per area basis."""
        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcasses = CarcassPool(
            decomposed_cnp=CNP(C=2.5e-5, N=3.3333333e-6, P=3.3333333e-8)
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
        "C, N, P, expected_c, expected_n, expected_p,raises_exception",
        [
            (5.0, 1.0, 0.5, 5.0, 1.0, 0.5, False),  # Normal case
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False),  # Zero mass
            (-1.0, 1.0, 0.5, None, None, None, True),  # Negative value
        ],
    )
    def test_add_carcass(
        self,
        C,
        N,
        P,
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
                carcasses.add_carcass(C, N, P)
        else:
            carcasses.add_carcass(C, N, P)
            assert carcasses.scavengeable_cnp.C == pytest.approx(expected_c)
            assert carcasses.scavengeable_cnp.N == pytest.approx(expected_n)
            assert carcasses.scavengeable_cnp.P == pytest.approx(expected_p)

        def test_reset(self):
            """Test resetting of the carcass pool."""
            from virtual_ecosystem.models.animal.decay import CarcassPool

            carcasses = CarcassPool(
                decomposed_cnp={
                    "C": 2.5e-5,
                    "N": 3.3333333e-6,
                    "P": 3.3333333e-8,
                }
            )
            carcasses.reset()

            assert carcasses.decomposed_cnp["C"] == 0.0
            assert carcasses.decomposed_cnp["N"] == 0.0
            assert carcasses.decomposed_cnp["P"] == 0.0


class TestExcrementPool:
    """Test the ExcrementPool class."""

    def test_initialization(self):
        """Testing initialization of ExcrementPool."""

        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool(
            scavengeable_cnp=CNP(C=7.77e-5, N=1e-5, P=1e-7),
            decomposed_cnp=CNP(C=2.5e-5, N=3.3333333e-6, P=3.3333333e-8),
        )

        assert pytest.approx(excrement.scavengeable_cnp.C) == 7.77e-5
        assert pytest.approx(excrement.decomposed_cnp.C) == 2.5e-5
        assert pytest.approx(excrement.scavengeable_cnp.N) == 1e-5
        assert pytest.approx(excrement.decomposed_cnp.N) == 3.3333333e-6
        assert pytest.approx(excrement.scavengeable_cnp.P) == 1e-7
        assert pytest.approx(excrement.decomposed_cnp.P) == 3.3333333e-8

    @pytest.mark.parametrize(
        "C, N, P, expected_c, expected_n, expected_p,raises_exception",
        [
            (5.0, 1.0, 0.5, 5.0, 1.0, 0.5, False),  # Normal case
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False),  # Zero mass
            (-1.0, 1.0, 0.5, None, None, None, True),  # Negative value
        ],
    )
    def test_add_excrement(
        self,
        C,
        N,
        P,
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
                excrement.add_excrement(C, N, P)
        else:
            excrement.add_excrement(C, N, P)
            assert excrement.scavengeable_cnp.C == pytest.approx(expected_c)
            assert excrement.scavengeable_cnp.N == pytest.approx(expected_n)
            assert excrement.scavengeable_cnp.P == pytest.approx(expected_p)

    def test_reset(self):
        """Test resetting of the excrement pool."""

        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement = ExcrementPool(
            decomposed_cnp=CNP(C=2.5e-5, N=3.3333333e-6, P=3.3333333e-8)
        )

        # Call reset (should set all values to 0.0)
        excrement.reset()

        assert excrement.decomposed_cnp.C == 0.0
        assert excrement.decomposed_cnp.N == 0.0
        assert excrement.decomposed_cnp.P == 0.0


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


class TestFungalFruitPool:
    """Test the FungalFruitPool class."""

    def test_initialization(self, mocker, fixture_core_constants):
        """Test initialization of FungalFruitPool."""
        import numpy as np

        from virtual_ecosystem.core.data import Data
        from virtual_ecosystem.models.animal.decay import FungalFruitPool

        mock_data = mocker.MagicMock(spec=Data)
        cell_id = 2
        cell_area = 100.0
        fungi_mass = np.array([0.5, 0.7, 1.0])

        # Inline mock chain for sel(cell_id=...).item()
        mock_data.__getitem__.side_effect = lambda key: {
            "fungal_fruiting_bodies": mocker.Mock(
                sel=lambda **kwargs: mocker.Mock(item=lambda: fungi_mass[cell_id])
            ),
        }[key]

        litter_pool = FungalFruitPool(
            cell_id=cell_id,
            data=mock_data,
            cell_area=cell_area,
            c_n_ratio=fixture_core_constants.fungal_fruiting_bodies_c_n_ratio,
            c_p_ratio=fixture_core_constants.fungal_fruiting_bodies_c_p_ratio,
        )

        c_mass = fungi_mass[cell_id] * cell_area
        n_mass = c_mass / 10.0
        p_mass = c_mass / 75.0

        assert np.isclose(litter_pool.mass_cnp.C, c_mass)
        assert np.isclose(litter_pool.mass_cnp.N, n_mass)
        assert np.isclose(litter_pool.mass_cnp.P, p_mass)

    def test_mass_current(self, mocker):
        """Test the mass_current property of FungalFruitPool."""
        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import FungalFruitPool

        # Create a mock FungalFruitPool with a single CNP object
        soil_pool = mocker.Mock()
        soil_pool.mass_cnp = CNP(C=12.34, N=1.0, P=0.5)

        # Access the property via descriptor protocol
        result = FungalFruitPool.mass_current.__get__(soil_pool)

        assert result == 12.34

    def test_get_eaten(self, mocker, dummy_animal_data, fixture_core_constants):
        """Test FungalFruitPool.get_eaten for correct nutrient consumption."""
        import numpy as np

        from virtual_ecosystem.models.animal.decay import FungalFruitPool

        cell_area = 1.0
        cell_id = 1

        fungal_fruit = FungalFruitPool(
            cell_id=cell_id,
            data=dummy_animal_data,
            cell_area=cell_area,
            c_n_ratio=fixture_core_constants.fungal_fruiting_bodies_c_n_ratio,
            c_p_ratio=fixture_core_constants.fungal_fruiting_bodies_c_p_ratio,
        )

        detritivore = mocker.MagicMock()
        detritivore.functional_group.mechanical_efficiency = 0.8

        consumed_mass = 0.2
        cell_cnp = fungal_fruit.mass_cnp

        total_mass_available = cell_cnp.total
        actual_consumed_mass = min(total_mass_available, consumed_mass) * 0.8

        nutrients, _ = fungal_fruit.get_eaten(consumed_mass, detritivore=detritivore)

        assert np.isclose(
            fungal_fruit.mass_cnp.total, total_mass_available - actual_consumed_mass
        )

        nutrient_proportions = cell_cnp.get_proportions()
        expected_nutrients = {
            "C": actual_consumed_mass * nutrient_proportions["C"],
            "N": actual_consumed_mass * nutrient_proportions["N"],
            "P": actual_consumed_mass * nutrient_proportions["P"],
        }

        for key in expected_nutrients:
            assert np.isclose(nutrients[key], expected_nutrients[key]), (
                f"{key} nutrient mismatch. Expected {expected_nutrients[key]},"
                f" got {nutrients[key]}"
            )

    def test_apply_decay(self, dummy_animal_data, fixture_core_constants):
        """Test FungalFruitPool.get_eaten for correct nutrient consumption."""
        import numpy as np

        from virtual_ecosystem.models.animal.decay import FungalFruitPool

        cell_area = 100.0
        cell_id = 1

        fungal_fruit = FungalFruitPool(
            cell_id=cell_id,
            data=dummy_animal_data,
            cell_area=cell_area,
            c_n_ratio=fixture_core_constants.fungal_fruiting_bodies_c_n_ratio,
            c_p_ratio=fixture_core_constants.fungal_fruiting_bodies_c_p_ratio,
        )

        total_decay = fungal_fruit.apply_decay(
            decay_constant=fixture_core_constants.fungal_fruiting_bodies_decay_rate,
            time_period=30.0,
        )
        assert np.isclose(total_decay, 51.036906692032936)
        assert np.isclose(fungal_fruit.mass_cnp["C"], 98.96309330796706)
        assert np.isclose(fungal_fruit.mass_cnp["N"], 9.896309330796706)
        assert np.isclose(fungal_fruit.mass_cnp["P"], 1.3195079107728942)


class TestLitterPool:
    """Test the LitterPool class."""

    def test_initialization(self, mocker):
        """Test initialization of LitterPool."""
        import numpy as np

        from virtual_ecosystem.core.data import Data
        from virtual_ecosystem.models.animal.decay import LitterPool

        mock_data = mocker.MagicMock(spec=Data)
        pool_name = "above_metabolic"
        cell_id = 2
        cell_area = 100.0
        litter_mass = np.array([0.5, 0.7, 1.0])
        c_n_ratio = np.array([20.0, 25.0, 30.0])
        c_p_ratio = np.array([100.0, 120.0, 140.0])

        # Inline mock chain for sel(cell_id=...).item()
        mock_data.__getitem__.side_effect = lambda key: {
            f"litter_pool_{pool_name}": mocker.Mock(
                sel=lambda **kwargs: mocker.Mock(item=lambda: litter_mass[cell_id])
            ),
            f"c_n_ratio_{pool_name}": mocker.Mock(
                sel=lambda **kwargs: mocker.Mock(item=lambda: c_n_ratio[cell_id])
            ),
            f"c_p_ratio_{pool_name}": mocker.Mock(
                sel=lambda **kwargs: mocker.Mock(item=lambda: c_p_ratio[cell_id])
            ),
        }[key]

        litter_pool = LitterPool(pool_name, cell_id, mock_data, cell_area)

        c_mass = litter_mass[cell_id] * cell_area
        n_mass = c_mass / c_n_ratio[cell_id]
        p_mass = c_mass / c_p_ratio[cell_id]

        assert np.isclose(litter_pool.mass_cnp.C, c_mass)
        assert np.isclose(litter_pool.mass_cnp.N, n_mass)
        assert np.isclose(litter_pool.mass_cnp.P, p_mass)

    def test_mass_current(self, mocker):
        """Test the mass_current property of LitterPool."""
        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import LitterPool

        # Create a mock LitterPool with a single CNP object
        litter_pool = mocker.Mock()
        litter_pool.mass_cnp = CNP(C=12.34, N=1.0, P=0.5)

        # Access the property via descriptor protocol
        result = LitterPool.mass_current.__get__(litter_pool)

        assert result == 12.34

    def test_get_eaten(self, mocker):
        """Test `get_eaten` method of LitterPool for correct nutrient consumption."""
        import numpy as np

        from virtual_ecosystem.models.animal.decay import LitterPool

        mock_data = mocker.MagicMock()
        pool_name = "test_pool"
        cell_area = 1.0
        cell_id = 1
        litter_mass = np.array([100.0, 200.0, 300.0])
        c_n_ratio = np.array([10.0, 20.0, 30.0])
        c_p_ratio = np.array([40.0, 50.0, 60.0])

        mock_data.__getitem__.side_effect = lambda key: {
            f"litter_pool_{pool_name}": mocker.Mock(
                sel=lambda **kwargs: mocker.Mock(item=lambda: litter_mass[cell_id])
            ),
            f"c_n_ratio_{pool_name}": mocker.Mock(
                sel=lambda **kwargs: mocker.Mock(item=lambda: c_n_ratio[cell_id])
            ),
            f"c_p_ratio_{pool_name}": mocker.Mock(
                sel=lambda **kwargs: mocker.Mock(item=lambda: c_p_ratio[cell_id])
            ),
        }[key]

        litter_pool = LitterPool(pool_name, cell_id, mock_data, cell_area)
        detritivore = mocker.MagicMock()
        detritivore.functional_group.mechanical_efficiency = 0.8

        consumed_mass = 100.0
        cell_cnp = litter_pool.mass_cnp

        total_mass_available = cell_cnp.total
        actual_consumed_mass = min(total_mass_available, consumed_mass) * 0.8

        nutrients, _ = litter_pool.get_eaten(consumed_mass, detritivore)

        assert np.isclose(
            litter_pool.mass_cnp.total,
            total_mass_available - actual_consumed_mass,
        )

        nutrient_proportions = cell_cnp.get_proportions()
        expected_nutrients = {
            "C": actual_consumed_mass * nutrient_proportions["C"],
            "N": actual_consumed_mass * nutrient_proportions["N"],
            "P": actual_consumed_mass * nutrient_proportions["P"],
        }

        for key in expected_nutrients:
            assert np.isclose(nutrients[key], expected_nutrients[key]), (
                f"{key} nutrient mismatch. Expected {expected_nutrients[key]},"
                f" got {nutrients[key]}"
            )


class TestSoilPool:
    """Test the SoilPool class."""

    @pytest.mark.parametrize(
        argnames=["pool_name", "expected_mass", "expected_error"],
        argvalues=[
            (
                "pom",
                {"C": 17.5, "N": 0.0714285, "P": 0.00285714},
                does_not_raise(),
            ),
            (
                "bacteria",
                {"C": 282.5, "N": 54.326923, "P": 17.65625},
                does_not_raise(),
            ),
            (
                "fungi",
                {"C": 258.25, "N": 19.7777778, "P": 3.07291667},
                does_not_raise(),
            ),
            ("lmwc", {}, pytest.raises(ValueError)),
        ],
    )
    def test_initialization(
        self,
        litter_soil_data_instance,
        fixture_core_constants,
        microbial_c_n_p_ratios,
        pool_name,
        expected_mass,
        expected_error,
    ):
        """Test initialization of LitterPool."""
        import numpy as np

        from virtual_ecosystem.models.animal.decay import SoilPool

        with expected_error:
            litter_pool = SoilPool(
                pool_name=pool_name,
                cell_id=2,
                data=litter_soil_data_instance,
                cell_area=100.0,
                max_depth_microbial_activity=fixture_core_constants.max_depth_of_microbial_activity,
                c_n_p_ratios=microbial_c_n_p_ratios,
            )

            assert np.isclose(litter_pool.mass_cnp.C, expected_mass["C"])
            assert np.isclose(litter_pool.mass_cnp.N, expected_mass["N"])
            assert np.isclose(litter_pool.mass_cnp.P, expected_mass["P"])

    def test_mass_current(self, mocker):
        """Test the mass_current property of SoilPool."""
        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import SoilPool

        # Create a mock SoilPool with a single CNP object
        soil_pool = mocker.Mock()
        soil_pool.mass_cnp = CNP(C=12.34, N=1.0, P=0.5)

        # Access the property via descriptor protocol
        result = SoilPool.mass_current.__get__(soil_pool)

        assert result == 12.34

    def test_get_eaten(
        self,
        mocker,
        litter_soil_data_instance,
        fixture_core_constants,
        microbial_c_n_p_ratios,
    ):
        """Test `get_eaten` method of SoilPool for correct nutrient consumption."""
        import numpy as np

        from virtual_ecosystem.models.animal.decay import SoilPool

        pool_name = "pom"
        cell_area = 1.0
        cell_id = 1

        soil_pool = SoilPool(
            pool_name=pool_name,
            cell_id=cell_id,
            data=litter_soil_data_instance,
            cell_area=cell_area,
            max_depth_microbial_activity=fixture_core_constants.max_depth_of_microbial_activity,
            c_n_p_ratios=microbial_c_n_p_ratios,
        )

        detritivore = mocker.MagicMock()
        detritivore.functional_group.mechanical_efficiency = 0.8

        consumed_mass = 0.2
        cell_cnp = soil_pool.mass_cnp

        total_mass_available = cell_cnp.total
        actual_consumed_mass = min(total_mass_available, consumed_mass) * 0.8

        nutrients, _ = soil_pool.get_eaten(consumed_mass, detritivore=detritivore)

        assert np.isclose(
            soil_pool.mass_cnp.total, total_mass_available - actual_consumed_mass
        )

        nutrient_proportions = cell_cnp.get_proportions()
        expected_nutrients = {
            "C": actual_consumed_mass * nutrient_proportions["C"],
            "N": actual_consumed_mass * nutrient_proportions["N"],
            "P": actual_consumed_mass * nutrient_proportions["P"],
        }

        for key in expected_nutrients:
            assert np.isclose(nutrients[key], expected_nutrients[key]), (
                f"{key} nutrient mismatch. Expected {expected_nutrients[key]},"
                f" got {nutrients[key]}"
            )
