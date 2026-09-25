"""Test the virtual_ecosystem.models.plants.subcanopy module."""

from contextlib import nullcontext as does_not_raise
from types import SimpleNamespace

import numpy as np
import pytest
import xarray as xr
from numpy.testing import assert_allclose


@pytest.mark.parametrize(
    argnames="initial_masses, outcome",
    argvalues=(
        pytest.param(
            np.broadcast_to([[1, np.nan, np.nan]], (5, 3)),
            does_not_raise(),
            id="only_carbon",
        ),
        pytest.param(
            np.broadcast_to([[1, 0.1, 0.01]], (5, 3)),
            does_not_raise(),
            id="all_provided",
        ),
        pytest.param(
            np.broadcast_to([[1, 0.1, np.nan]], (5, 3)),
            pytest.raises(ValueError),
            id="partial",
        ),
    ),
)
def test_SubcanopyBiomass__init__(initial_masses, outcome):
    """Simple test of SubcanopyBiomass__init__.

    Check the method handles np.nan in inputs correctly.
    """
    from virtual_ecosystem.models.plants.subcanopy import SubcanopyBiomass

    with outcome:
        tissue = SubcanopyBiomass(
            initial_masses=initial_masses, ideal_ratios=(1, 10, 100), var_name="var"
        )

        # Check the auto calculation from ideal ratios
        assert np.allclose(
            tissue.elemental_masses, np.broadcast_to([[1, 0.1, 0.01]], (5, 3))
        )


def test_SubcanopyBiomass_methods(fixture_plants_constants):
    """Test the SubcanopyBiomass class and methods."""
    from virtual_ecosystem.models.plants.subcanopy import SubcanopyBiomass

    n_cells = 20
    carbon_mass = (np.arange(n_cells) + 1.0)[:, None]
    ideal_ratios = np.array(
        [
            1,
            fixture_plants_constants.subcanopy_vegetation_c_n_ratio,
            fixture_plants_constants.subcanopy_vegetation_c_p_ratio,
        ]
    )

    # Complete mass at ideal ratios
    initial_mass = carbon_mass / ideal_ratios

    # Direct construction
    stoich_one = SubcanopyBiomass(
        initial_masses=initial_mass.copy(), ideal_ratios=ideal_ratios, var_name="var"
    )

    # Test mass removal method and maintenance of ratios
    stoich_two = stoich_one.remove_mass_fraction(mass_fraction=0.25)

    assert_allclose(stoich_one.elemental_masses, initial_mass * 0.75)
    assert_allclose(stoich_two.elemental_masses, initial_mass * 0.25)

    # Test addition method
    stoich_one.add_mass(stoich_two)

    assert_allclose(stoich_one.elemental_masses, initial_mass)

    # Test excess nutrient extraction - values for N and P give ideal ratios at mass 10
    # but  excess for smaller masses and deficit for larger masses
    variable_ratios = np.concatenate(
        [carbon_mass, np.full_like(carbon_mass, 0.5), np.full_like(carbon_mass, 0.2)],
        axis=1,
    )
    stoich_three = SubcanopyBiomass(
        initial_masses=variable_ratios, ideal_ratios=ideal_ratios, var_name="var"
    )

    # Remove excess - result should be the difference between variable and ideal, where
    # that difference is positive
    excess = stoich_three.get_excess_nutrients()

    np.allclose(
        excess.elemental_masses,
        np.clip(variable_ratios - initial_mass, a_min=0, a_max=None),
    )

    # Remove excess again - should now be zero
    excess = stoich_three.get_excess_nutrients()
    np.allclose(
        excess.elemental_masses,
        np.zeros_like(excess.elemental_masses),
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

    # Update carbon mass data from scenario
    plants_data["subcanopy_vegetation_cnp"][:, 0] = veg_biomass
    plants_data["subcanopy_seedbank_cnp"][:, 0] = seedbank_biomass

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
        data_object_template=cnp_template,
    )

    # Test initialisation sets the biomasses
    assert_allclose(
        subcanopy.subcanopy_vegetation_cnp.elemental_masses[:, 0], veg_biomass
    )
    assert_allclose(
        subcanopy.subcanopy_seedbank_cnp.elemental_masses[:, 0], seedbank_biomass
    )

    # Set the subcanopy shortwave absorption - don't need finesse here - either
    # vegetation present or not
    subcanopy.set_light_capture(below_canopy_light_fraction=np.ones(4))

    # Run the GPP estimation with a simple fake of the P Model structure.
    shape = (subcanopy.layer_index + 1, 4)
    subcanopy.estimate_gpp(
        pmodel=SimpleNamespace(
            lue=np.ones(shape),
            iwue=np.ones(shape),
            env=SimpleNamespace(tc=np.full(shape, 20), patm=np.full(shape, 101235)),
        ),
        swd=np.ones(4),
    )

    subcanopy.calculate_dynamics()

    # Assert that biomasses have been written and are either equal to zero or greater.
    assert np.all(
        veg_comparator(
            plants_data["subcanopy_vegetation_cnp"].to_numpy(), np.zeros((4, 3))
        )
    )
    assert np.all(
        seedbank_comparator(
            plants_data["subcanopy_seedbank_cnp"].to_numpy(), np.zeros((4, 3))
        )
    )
