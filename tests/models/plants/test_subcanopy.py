"""Test the virtual_ecosystem.models.plants.subcanopy module."""

import numpy as np
from numpy.testing import assert_allclose


def test_SubcanopyStoichiometry():
    """Test the simple SubcanopyStoichiometry class and methods."""
    from virtual_ecosystem.models.plants.subcanopy import SubcanopyStoichiometry

    n_cells = 20
    carbon_mass = np.arange(n_cells) + 1.0
    ideal_cn_ratio = 20.0
    ideal_cp_ratio = 50.0

    stoich_one = SubcanopyStoichiometry(
        carbon_mass=carbon_mass.copy(),
        nitrogen_mass=carbon_mass / ideal_cn_ratio,
        phosphorous_mass=carbon_mass / ideal_cp_ratio,
        ideal_cn_ratio=ideal_cn_ratio,
        ideal_cp_ratio=ideal_cp_ratio,
    )

    # Test the cn_ratio and cp_ratio properties
    assert_allclose(stoich_one.cn_ratio, np.full(n_cells, ideal_cn_ratio))
    assert_allclose(stoich_one.cp_ratio, np.full(n_cells, ideal_cp_ratio))

    # Test mass removal method and maintenance of ratios
    stoich_two = stoich_one.remove_mass_fraction(mass_fraction=0.25)

    assert_allclose(stoich_one.carbon_mass, carbon_mass * 0.75)
    assert_allclose(stoich_two.carbon_mass, carbon_mass * 0.25)

    assert_allclose(stoich_one.cn_ratio, np.full(n_cells, ideal_cn_ratio))
    assert_allclose(stoich_one.cp_ratio, np.full(n_cells, ideal_cp_ratio))

    # Test addition method
    stoich_one.add_mass(stoich_two)

    assert_allclose(stoich_one.carbon_mass, carbon_mass)
    assert_allclose(stoich_one.cn_ratio, np.full(n_cells, ideal_cn_ratio))
    assert_allclose(stoich_one.cp_ratio, np.full(n_cells, ideal_cp_ratio))

    # Test ratio calculations by adding pure carbon
    stoich_three = SubcanopyStoichiometry(
        carbon_mass=carbon_mass.copy(),
        nitrogen_mass=np.zeros(n_cells),
        phosphorous_mass=np.zeros(n_cells),
        ideal_cn_ratio=ideal_cn_ratio,
        ideal_cp_ratio=ideal_cp_ratio,
    )

    stoich_one.add_mass(stoich_three)

    assert_allclose(stoich_one.carbon_mass, 2 * carbon_mass)
    assert_allclose(stoich_one.cn_ratio, np.full(n_cells, ideal_cn_ratio * 2))
    assert_allclose(stoich_one.cp_ratio, np.full(n_cells, ideal_cp_ratio * 2))

    # Test excess nutrient method - values for N and P give ideal ratios at mass 10 but
    # excess for smaller masses and deficit for larger masses
    stoich_varying_ratios = SubcanopyStoichiometry(
        carbon_mass=carbon_mass.copy(),
        nitrogen_mass=np.full(n_cells, 0.5),
        phosphorous_mass=np.full(n_cells, 0.2),
        ideal_cn_ratio=ideal_cn_ratio,
        ideal_cp_ratio=ideal_cp_ratio,
    )

    excess_n_p = stoich_varying_ratios.get_excess_nutrients()

    # Check masses in excess - no carbon, note ratios undefined here as C mass is zero
    # I'm not 100% sure I like this, but keeping the UI simple for now.
    assert_allclose(excess_n_p.carbon_mass, np.zeros(n_cells))
    assert_allclose(
        excess_n_p.nitrogen_mass,
        np.where(carbon_mass > 10, 0, 0.5 - (carbon_mass / ideal_cn_ratio)),
    )
    assert_allclose(
        excess_n_p.phosphorous_mass,
        np.where(carbon_mass > 10, 0, 0.2 - (carbon_mass / ideal_cp_ratio)),
    )

    # Check ratios in sources
    assert_allclose(stoich_varying_ratios.carbon_mass, carbon_mass)
    assert_allclose(
        stoich_varying_ratios.cn_ratio,
        np.where(carbon_mass <= 10, ideal_cn_ratio, (carbon_mass / 0.5)),
    )
    assert_allclose(
        stoich_varying_ratios.cp_ratio,
        np.where(carbon_mass <= 10, ideal_cp_ratio, (carbon_mass / 0.2)),
    )
