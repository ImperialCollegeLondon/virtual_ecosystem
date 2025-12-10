"""Test the virtual_ecosystem.models.plants.subcanopy module."""

import numpy as np
import pytest
import xarray as xr
from numpy.testing import assert_allclose


def test_Nutrient(fixture_plants_constants):
    """Simple test of nutrient constructor and factory method."""
    from virtual_ecosystem.models.plants.subcanopy import Nutrient

    elemental_masses = np.arange(0.1, 2.0, 0.1)
    nutrient_one = Nutrient(
        "n",
        ideal_ratio=fixture_plants_constants.subcanopy_seedbank_c_n_ratio,
        masses=elemental_masses,
    )

    nutrient_two = Nutrient.from_constants(
        tissue_name="subcanopy_vegetation",
        element="n",
        constants=fixture_plants_constants,
        masses=elemental_masses
        * fixture_plants_constants.subcanopy_vegetation_c_n_ratio,
    )

    assert_allclose(nutrient_one.masses, nutrient_two.masses)


def test_SubcanopyBiomass(fixture_plants_constants):
    """Test the simple SubcanopyBiomass class and methods."""
    from virtual_ecosystem.models.plants.subcanopy import Nutrient, SubcanopyBiomass

    n_cells = 20
    carbon_mass = np.arange(n_cells) + 1.0

    cn_ratio = fixture_plants_constants.subcanopy_vegetation_c_n_ratio
    cp_ratio = fixture_plants_constants.subcanopy_vegetation_c_p_ratio

    # Direct construction
    stoich_one = SubcanopyBiomass(
        carbon_mass=carbon_mass.copy(),
        nutrients={
            "n": Nutrient(
                name="n", ideal_ratio=cn_ratio, masses=carbon_mass / cn_ratio
            ),
            "p": Nutrient(
                name="p", ideal_ratio=cp_ratio, masses=carbon_mass / cp_ratio
            ),
        },
    )

    # Test the cn_ratio and cp_ratio properties
    assert_allclose(stoich_one.c_x_ratio("n"), np.full(n_cells, cn_ratio))
    assert_allclose(stoich_one.c_x_ratio("p"), np.full(n_cells, cp_ratio))

    # Test mass removal method and maintenance of ratios
    stoich_two = stoich_one.remove_mass_fraction(mass_fraction=0.25)

    assert_allclose(stoich_one.carbon_mass, carbon_mass * 0.75)
    assert_allclose(stoich_two.carbon_mass, carbon_mass * 0.25)

    assert_allclose(stoich_one.c_x_ratio("n"), np.full(n_cells, cn_ratio))
    assert_allclose(stoich_one.c_x_ratio("p"), np.full(n_cells, cp_ratio))

    # Test addition method
    stoich_one.add_mass(stoich_two)

    assert_allclose(stoich_one.carbon_mass, carbon_mass)
    assert_allclose(stoich_one.c_x_ratio("n"), np.full(n_cells, cn_ratio))
    assert_allclose(stoich_one.c_x_ratio("p"), np.full(n_cells, cp_ratio))

    # Test ratio calculations by adding pure carbon
    stoich_three = SubcanopyBiomass(
        carbon_mass=carbon_mass.copy(),
        nutrients={
            "n": Nutrient(name="n", ideal_ratio=cn_ratio, masses=np.zeros(n_cells)),
            "p": Nutrient(name="p", ideal_ratio=cp_ratio, masses=np.zeros(n_cells)),
        },
    )

    stoich_one.add_mass(stoich_three)

    # Carbon masses double and ratios also double.
    assert_allclose(stoich_one.carbon_mass, carbon_mass * 2)
    assert_allclose(stoich_one.c_x_ratio("n"), np.full(n_cells, cn_ratio * 2))
    assert_allclose(stoich_one.c_x_ratio("p"), np.full(n_cells, cp_ratio * 2))

    # Test excess nutrient method - values for N and P give ideal ratios at mass 10 but
    # excess for smaller masses and deficit for larger masses
    stoich_varying_ratios = SubcanopyBiomass(
        carbon_mass=carbon_mass.copy(),
        nutrients={
            "n": Nutrient(name="n", ideal_ratio=cn_ratio, masses=np.full(n_cells, 0.5)),
            "p": Nutrient(name="p", ideal_ratio=cp_ratio, masses=np.full(n_cells, 0.2)),
        },
    )

    excess_n_p = stoich_varying_ratios.get_excess_nutrients()

    # Check masses in excess
    assert_allclose(
        excess_n_p["n"].masses,
        np.where(carbon_mass > 10, 0, 0.5 - (carbon_mass / cn_ratio)),
    )
    assert_allclose(
        excess_n_p["p"].masses,
        np.where(carbon_mass > 10, 0, 0.2 - (carbon_mass / cp_ratio)),
    )

    # Check ratios in sources
    assert_allclose(stoich_varying_ratios.carbon_mass, carbon_mass)
    assert_allclose(
        stoich_varying_ratios.c_x_ratio("n"),
        np.where(carbon_mass <= 10, cn_ratio, (carbon_mass / 0.5)),
    )
    assert_allclose(
        stoich_varying_ratios.c_x_ratio("p"),
        np.where(carbon_mass <= 10, cp_ratio, (carbon_mass / 0.2)),
    )


@pytest.mark.parametrize(
    argnames="veg_biomass, seedbank_biomass, veg_comparator, seedbank_comparator",
    argvalues=(
        pytest.param(
            np.ones(4), np.zeros(4), np.greater, np.greater, id="seedbank_repopulates"
        ),
        pytest.param(
            np.zeros(4), np.ones(4), np.greater, np.greater, id="vegetation_repopulates"
        ),
        pytest.param(
            np.zeros(4), np.zeros(4), np.equal, np.equal, id="no_biomass_persists"
        ),
    ),
)
def test_subcanopy_vegetation_dynamics(
    plants_data,
    fixture_plants_constants,
    fixture_pyrealm_config,
    fixture_core_components,
    veg_biomass,
    seedbank_biomass,
    veg_comparator,
    seedbank_comparator,
):
    """Test that subcanopy dynamics work at a coarse scale.

    The parameterised scenarios simulate the recovery of empty vegetation or seedbank as
    long as the other pool contains some biomass.
    """

    from virtual_ecosystem.models.plants.subcanopy import Subcanopy

    # Update data from scenario
    plants_data["subcanopy_vegetation_biomass"][:] = veg_biomass
    plants_data["subcanopy_seedbank_biomass"][:] = seedbank_biomass

    template = fixture_core_components.layer_structure.from_template()
    template[:] = 0

    cnp_template = xr.DataArray(
        data=np.zeros((fixture_core_components.grid.n_cells, 3)),
        coords={
            "cell_id": fixture_core_components.grid.cell_id,
            "element": ["C", "N", "P"],
        },
    )

    plants_data["shortwave_absorption"] = template.copy()
    plants_data["leaf_area_index"] = template.copy()
    plants_data["layer_fapar"] = template.copy()
    plants_data["transpiration"] = template.copy()

    subcanopy = Subcanopy(
        data=plants_data,
        pyrealm_core_constants=fixture_pyrealm_config.core,
        model_constants=fixture_plants_constants,
        layer_index=fixture_core_components.layer_structure.index_surface_scalar,
        model_timing=fixture_core_components.model_timing,
    )

    # Test initialisation sets the biomasses
    assert_allclose(subcanopy.vegetation_biomass.carbon_mass, veg_biomass)
    assert_allclose(subcanopy.seedbank_biomass.carbon_mass, seedbank_biomass)

    # Set the subcanopy shortwave absorption - don't need finesse here - either
    # vegetation present or not

    subcanopy.set_light_capture(below_canopy_light_fraction=np.ones(4))

    subcanopy.calculate_dynamics(
        lue=np.ones(4),
        iwue=np.ones(4),
        swd=np.ones(4),
        data_object_template=cnp_template,
    )

    # Assert that biomasses are either equal to zero or greater.
    assert np.all(
        veg_comparator(
            plants_data["subcanopy_vegetation_biomass"].to_numpy(), np.zeros(4)
        )
    )
    assert np.all(
        seedbank_comparator(
            plants_data["subcanopy_seedbank_biomass"].to_numpy(), np.zeros(4)
        )
    )
