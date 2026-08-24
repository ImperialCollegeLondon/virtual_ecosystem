"""Tests for the model.plants.plants_model submodule.

The cohort data fixture used to run the full model in these tests has two payloads - one
with fairly sensible cohorts and the other with edge cases. These can be selected by
passing the tricky_plant_cohorts argument to the test function, which pytest passes down
to parameterise the `plants_cohort_data` fixture. Only one test in this module uses the
tricky data but the other tests still need to be parameterised (there doesn't seem to be
a way to set a default on the fixture).

@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
"""

from contextlib import nullcontext as does_not_raise
from copy import deepcopy

import numpy as np
import pytest
import xarray
from numpy.testing import assert_allclose, assert_array_less

from virtual_ecosystem.core.exceptions import InitialisationError


def data_validator(model, validation_data, skip):
    """Routine for validating that a test model state matches validation data.

    This is deliberately untyped to avoid having to import VE objects outside of tests.

    Args:
        model: A PlantsModel instance
        validation_data: A dictionary of validation data - see the
            fixture_canopy_layer_data fixture for the structure
        skip: A list of keys of validation data to be skipped in a given test.
    """

    to_validate = (val for ky, val in validation_data.items() if ky not in skip)

    for layer_name, expected_data in to_validate:
        # Check the layer is present
        assert layer_name in model.data

        # Check the values
        try:
            xarray.testing.assert_allclose(model.data[layer_name], expected_data)
        except AssertionError:
            print(f"Data invalid: {layer_name}")
            raise


def wipe_canopy_layers(model):
    """Simple routine to reset canopy layers in the model to nan to test calculation.

    This is deliberately untyped to avoid having to import VE objects outside of tests.

    Note this passes by reference - the model object is updated in place.
    """

    for layer in [
        "layer_heights",
        "leaf_area_index",
        "layer_fapar",
        "shortwave_absorption",
    ]:
        model.data[layer] = model.layer_structure.from_template()


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel__init__(
    plants_data,
    plants_cohort_data,
    fixture_flora,
    fixture_core_components,
    fixture_canopy_layer_data,
    fixture_exporter,
    tricky_plant_cohorts,
):
    """Test the PlantsModel.__init__ method."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel(
        data=plants_data,
        core_components=fixture_core_components,
        flora=fixture_flora,
        cohort_data=plants_cohort_data,
        exporter=fixture_exporter,
    )

    # Test the flora and community are as expected
    n_cells = fixture_core_components.grid.n_cells
    assert plants_model.flora.equals(fixture_flora)
    assert len(plants_model.communities) == n_cells

    # Check the canopy and subcanopy vegetation has been initialised and updated,
    # using the test cases providing full details, not the canopy only test cases.
    # TODO - amend this as and when layer heights gets centralised

    data_validator(
        plants_model,
        fixture_canopy_layer_data,
        skip=[
            "layer_heights_canopy",
            "leaf_area_index_canopy",
            "layer_fapar_canopy",
        ],
    )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
@pytest.mark.parametrize(
    argnames="new_data,context_manager,error_message",
    argvalues=(
        pytest.param({}, does_not_raise(), None, id="all_good"),
        pytest.param(
            {
                "plant_pft_propagules": xarray.DataArray(
                    data=np.full((4, 2), fill_value=100, dtype=np.int_),
                    coords={
                        "cell_id": np.arange(4),
                        "plant_functional_type": ["tree1", "tree2"],
                    },
                )
            },
            pytest.raises(InitialisationError),
            "The plant_pft_propagules data is missing 'pft' coordinates.",
            id="no_pft_coords",
        ),
        pytest.param(
            {
                "plant_pft_propagules": xarray.DataArray(
                    data=np.full((4, 2), fill_value=100, dtype=np.int_),
                    coords={
                        "cell_id": np.arange(4),
                        "pft": ["tree1", "tree2"],
                    },
                )
            },
            pytest.raises(InitialisationError),
            "The 'pft' coordinates in the plant_pft_propagules data do not match "
            "the PFT names configured in the PlantsModel flora",
            id="bad_pft_coords",
        ),
    ),
)
def test_PlantsModel__init__errors(
    plants_data,
    fixture_flora,
    plants_cohort_data,
    fixture_core_components,
    tricky_plant_cohorts,
    fixture_exporter,
    new_data,
    context_manager,
    error_message,
):
    """Check initialisation failure models for the PlantsModel."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    # Overwrite configuration data with new values. This is more complex than a simple
    # replacement because the new values are altering an existing axis, so the data
    # needs clearing out before being replaced.
    for ky, val in new_data.items():
        del plants_data.data[ky]
        del plants_data.data["pft"]
        plants_data[ky] = val

    with context_manager as ctxt:
        _ = PlantsModel(
            data=plants_data,
            core_components=fixture_core_components,
            flora=fixture_flora,
            cohort_data=plants_cohort_data,
            exporter=fixture_exporter,
        )
        return

    assert str(ctxt.value) == error_message


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_from_config(
    plants_data,
    fixture_configuration,
    fixture_core_components,
    fixture_canopy_layer_data,
    tricky_plant_cohorts,
):
    """Test the PlantsModel.from_config factory method."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel.from_config(
        data=plants_data,
        configuration=fixture_configuration,
        core_components=fixture_core_components,
    )

    # Currently trivial test.
    n_cells = fixture_core_components.grid.n_cells
    assert isinstance(plants_model, PlantsModel)
    assert len(plants_model.communities) == n_cells

    # Check the canopy has been initialised and updated, using the full layer heights
    # data
    # TODO - amend this as and when layer heights gets centralised

    data_validator(
        plants_model,
        fixture_canopy_layer_data,
        skip=[
            "layer_heights_canopy",
            "leaf_area_index_canopy",
            "layer_fapar_canopy",
        ],
    )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False, True])
def test_PlantsModel_update_canopy_layers(
    fxt_plants_model,
    fixture_canopy_layer_data,
    tricky_plant_cohorts,  # Passed down to fixtures to set cohort inputs
):
    """Simple test that update canopy layers restores overwritten data.

    The tricky_plant_cohorts argument is passed down to fixtures to swap between a set
    of cohorts that provide all PFTs in all cells and a set with odd edge cases (no
    cohorts at all, cohorts with no individuals, only one PFT)
    """

    # Overwrite the existing canopy derived data in each layer - this also nukes the
    # soil and surface depths _which_ are not correctly regenerated in this test, so the
    # test makes use of the canopy only layer heights in the fixture_canopy_layer_data
    # in testing.
    #
    # TODO - amend this as and when layer heights gets centralised

    wipe_canopy_layers(fxt_plants_model)

    # Calling the method resets to the expected values
    fxt_plants_model.update_canopy_layers()

    # Check the resulting repopulated canopy data - this will only repopulate the active
    # canopy layers so do not use the full layer test cases and also omit
    # shortwave_absorption, which should not have been regenerated yet.
    data_validator(
        fxt_plants_model,
        fixture_canopy_layer_data,
        skip=[
            "shortwave_absorption",
            "layer_heights_full",
            "leaf_area_index_full",
            "layer_fapar_full",
        ],
    )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_set_shortwave_absorption(
    fxt_plants_model, fixture_canopy_layer_data, tricky_plant_cohorts
):
    """Simple test that update canopy layers restores overwritten data."""

    # Overwrite the existing canopy derived data in each layer - this also nukes the
    # soil and surface depths _which_ are not correctly regenerated in this test, so the
    # test makes use of the canopy only layer heights in the fixture_canopy_layer_data
    #
    # TODO - amend this as and when layer heights gets centralised

    wipe_canopy_layers(fxt_plants_model)

    # Check that calling the methods after update resets to the expected values
    fxt_plants_model.set_canopy_top_radiation(time_index=0)
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.subcanopy.set_light_capture(
        below_canopy_light_fraction=fxt_plants_model.below_canopy_light_fraction
    )
    fxt_plants_model.set_shortwave_absorption()

    data_validator(
        fxt_plants_model,
        fixture_canopy_layer_data,
        skip=[
            "layer_heights_full",
            "leaf_area_index_canopy",
            "layer_fapar_canopy",
        ],
    )


@pytest.fixture
def fxt_plants_model_hbvry(fxt_plants_model):
    """Add herbivory to model.

    This fixture modifies the consumption pools in fxt_plants_model, which default to
    zero, to add herbivory of 50% of the fruit, seed and foliage in each cohort.
    """
    for cid in fxt_plants_model.grid.cell_id:
        for tissue in ("fruit", "seed", "foliage"):
            # Get the biomass and divide in half
            consumed_biomass = (
                fxt_plants_model.biomasses[cid].get_tissue(tissue).elemental_masses
            ) / 2

            # Construct an xarray with dimensions to make it easier to group cohort data
            # back up to PFT for insertion into PFT structured consumption pool
            target_array = fxt_plants_model.data[f"canopy_{tissue}_cnp_consumed"]
            consumed_biomass_by_pft = xarray.DataArray(
                consumed_biomass,
                dims=("pft", "element"),
                coords={
                    "pft": fxt_plants_model.communities[cid].cohorts["pft_name"],
                    "element": target_array.element,
                },
            )

            # Explicitly insert chunks of data grouped by PFT to enforce PFT order on
            # the consumption pool PFT dimension and handle possible missing PFTs within
            # communities.
            for pft_name, pft_data in consumed_biomass_by_pft.groupby("pft"):
                target_array.loc[cid, pft_name, :] = pft_data.sum("pft")

    return fxt_plants_model


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_apply_herbivory(fxt_plants_model_hbvry, tricky_plant_cohorts):
    """Check the sequencing and processes for applying herbivory."""

    from virtual_ecosystem.models.plants.canopy import calculate_canopies

    # Save (deep) copies of the initial biomasses and herbivory affected traits for
    # comparison to values after applying herbivory
    initial_biomasses = deepcopy(fxt_plants_model_hbvry.biomasses)
    initial_lai = {
        ky: cm.cohorts.lai.squeeze().copy()
        for ky, cm in fxt_plants_model_hbvry.communities.items()
    }
    initial_tau_f = {
        ky: cm.cohorts.tau_f.squeeze().copy()
        for ky, cm in fxt_plants_model_hbvry.communities.items()
    }

    # Calculate canopy characteristics of communities _before_ herbivory
    pristine_canopies = calculate_canopies(
        communities=fxt_plants_model_hbvry.communities,
        max_canopy_layers=fxt_plants_model_hbvry.layer_structure.n_canopy_layers,
    )

    # Run herbivory
    fxt_plants_model_hbvry.apply_herbivory()

    # Check that the modelled biomasses have been appropriately reduced by 50%,
    # including proportional distribution of PFT herbivory back down to cohort level.
    for cid in fxt_plants_model_hbvry.grid.cell_id:
        for tissue in ("fruit", "seed", "foliage"):
            assert_allclose(
                initial_biomasses[cid].get_tissue(tissue).elemental_masses / 2,
                fxt_plants_model_hbvry.biomasses[cid]
                .get_tissue(tissue)
                .elemental_masses,
            )

    # Check that the LAI has been reduced to 75%: 50% of foliage lost in total is an
    # average of 25% lost over the timestep and LAI scales linearly with foliage mass
    # (or vice versa).
    for cid in fxt_plants_model_hbvry.grid.cell_id:
        assert_allclose(
            fxt_plants_model_hbvry.communities[cid].cohorts["lai"].squeeze(),
            initial_lai[cid] * 0.75,
        )

    # Check that the tau_f has been increased to compensate for foliage loss. The
    # calculation here is: Wf / tau + H = Wf / tau', where Wf is the allometric
    # expectation of foliage mass and H is the mass of foliage lost to herbivory.
    for cid in fxt_plants_model_hbvry.grid.cell_id:
        W_f = fxt_plants_model_hbvry.communities[cid].stem_allometry.foliage_mass
        assert_allclose(
            W_f / initial_tau_f[cid] + W_f / 2,
            W_f / fxt_plants_model_hbvry.communities[cid].cohorts["tau_f"].squeeze(),
        )

    # Check the canopy asbsorption has been altered - here just simply checking that the
    # average community absorption has strictly decreased. _Might_ be able to work out
    # the expectated new values given a halving of leaf area index, but seems fussy. It
    # just should go down.
    damaged_canopies = calculate_canopies(
        communities=fxt_plants_model_hbvry.communities,
        max_canopy_layers=fxt_plants_model_hbvry.layer_structure.n_canopy_layers,
    )

    for pristine, damaged in zip(pristine_canopies.values(), damaged_canopies.values()):
        assert_array_less(
            damaged.community_data.average_layer_absorption,
            pristine.community_data.average_layer_absorption,
        )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_update_allometry(fxt_plants_model_hbvry, tricky_plant_cohorts):
    """Check update allometry correctly resets traits."""
    from pyrealm.demography.tmodel import StemAllometry

    # Store the original foliage mass from the allometry and the tau_f values
    original_Wf = [
        deepcopy(c.stem_allometry.foliage_mass)
        for c in fxt_plants_model_hbvry.communities.values()
    ]
    original_tau_f = [
        deepcopy(c.cohorts.tau_f) for c in fxt_plants_model_hbvry.communities.values()
    ]

    # Apply herbivory to perturb the traits
    fxt_plants_model_hbvry.apply_herbivory()

    # Calculate the foliage mass with perturbed LAI to make sure update_allometry has an
    # actual issue to fix
    perturbed_Wf = [
        StemAllometry(cohorts=c.cohorts).foliage_mass
        for c in fxt_plants_model_hbvry.communities.values()
    ]
    perturbed_tau_f = [
        deepcopy(c.cohorts.tau_f) for c in fxt_plants_model_hbvry.communities.values()
    ]

    # Herbivory effects on LAI should have reduced expected foliage mass by 25%
    for orig, pert in zip(original_Wf, perturbed_Wf):
        assert_allclose(orig * 0.75, pert)

    # And tau_f should be lower (reflecting shorter turnover)
    for orig, pert in zip(original_tau_f, perturbed_tau_f):
        assert_array_less(pert, orig)

    fxt_plants_model_hbvry.update_allometry()

    restored_Wf = [
        deepcopy(c.stem_allometry.foliage_mass)
        for c in fxt_plants_model_hbvry.communities.values()
    ]

    restored_tau_f = [
        deepcopy(c.cohorts.tau_f) for c in fxt_plants_model_hbvry.communities.values()
    ]

    # LAI effects on foliage mass should now have been removed
    for orig, pert in zip(original_Wf, restored_Wf):
        assert_allclose(orig, pert)

    # And tau_f should be restored
    for orig, pert in zip(original_tau_f, restored_tau_f):
        assert_allclose(pert, orig)


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_estimate_gpp(fxt_plants_model, tricky_plant_cohorts):
    """Test the estimate_gpp method."""

    # Set the canopy and absorbed irradiance
    fxt_plants_model.set_canopy_top_radiation(time_index=0)
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.subcanopy.set_light_capture(
        below_canopy_light_fraction=fxt_plants_model.below_canopy_light_fraction
    )
    fxt_plants_model.set_shortwave_absorption()

    # Calculate GPP
    fxt_plants_model.reset_update_vars()
    fxt_plants_model.calculate_light_use_efficiency()
    fxt_plants_model.estimate_gpp(time_index=0)

    # TODO - Validation below uses benchmark values to detect changing code behaviour
    #        rather than some kind of a priori expectation.
    #      - Could mock input values to get a simple logical test, but lots of moving
    #        parts to mock. We could simple overwrite the calculated GPP to generate
    #        easier test values?

    # Check stem_gpp and stem_transpiration structure
    exp_stem_struct = {
        cid: len(cmty.cohorts) for cid, cmty in fxt_plants_model.communities.items()
    }

    # Are the stem properties dictionaries of arrays with the right length
    assert exp_stem_struct == {
        cid: len(vals) for cid, vals in fxt_plants_model.per_stem_gpp.items()
    }

    # Benchmark values to detect code behaviour change
    stem_gpp_bench = {
        0: np.array([8.66977499e00, 4.90401433e-02, 5.76835050e-04]),
        1: np.array([11.03114354, 0.11715303]),
        2: np.array([1.46823658e01, 3.29419691e-03]),
        3: np.array([2.05994772e01, 6.69298558e-01, 7.06723817e-03]),
    }

    assert {
        assert_allclose(fxt_plants_model.per_stem_gpp[cid], stem_gpp_bench[cid])
        for cid in stem_gpp_bench
    }

    # Are the stem properties dictionaries of arrays with the right length
    assert exp_stem_struct == {
        cid: len(vals) for cid, vals in fxt_plants_model.per_stem_transpiration.items()
    }

    # Benchmark values to detect code behaviour change
    stem_transpiration_bench = {
        0: np.array([1.21441867e-03, 6.86929773e-06, 8.08001656e-08]),
        1: np.array([1.54518735e-03, 1.64102100e-05]),
        2: np.array([2.05663228e-03, 4.61434609e-07]),
        3: np.array([2.88547163e-03, 9.37519909e-05, 9.89943337e-07]),
    }

    assert {
        assert_allclose(
            fxt_plants_model.per_stem_transpiration[cid], stem_transpiration_bench[cid]
        )
        for cid in stem_gpp_bench
    }

    # Check the transpiration data array shape
    assert fxt_plants_model.data["transpiration"].shape == (
        fxt_plants_model.layer_structure.n_layers,
        fxt_plants_model.grid.n_cells,
    )

    transpiration_by_layer_benchmark = fxt_plants_model.layer_structure.from_template()

    # Benchmark values to detect code behaviour change
    transpiration_by_layer_benchmark[1:5] = [
        [2.92047294e-01, 2.92045517e-01, 2.92055938e-01, 2.98013627e-01],
        [1.22215429e-01, 1.22242819e-01, 1.19316662e-01, 7.72929761e-06],
        [5.11323840e-02, 5.09088906e-02, np.nan, np.nan],
        [2.10673712e-02, np.nan, np.nan, np.nan],
    ]

    assert_allclose(
        fxt_plants_model.data["transpiration"], transpiration_by_layer_benchmark
    )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_allocate_gpp(fxt_plants_model, tricky_plant_cohorts):
    """Test the allocate_gpp method."""

    # Populate the data variables required for update
    fxt_plants_model.reset_update_vars()

    # Provide GPP values
    fxt_plants_model.per_stem_gpp = {
        cell_id: np.array([55]) for cell_id in fxt_plants_model.communities.keys()
    }
    # Store previous dbh values
    prev_dbh_values = {
        cell_id: fxt_plants_model.communities[cell_id].cohorts.dbh_value.copy()
        for cell_id in fxt_plants_model.communities.keys()
    }

    # Allocate GPP
    fxt_plants_model.allocate_gpp()

    for cell_id in fxt_plants_model.communities.keys():
        # TODO: Eventually have tests with more meaningful values
        #       Pretty sure this is still wrong but no longer shrinking :-)

        # Check that dbh is >= previous dbh (plants should not shrink!)
        assert np.all(
            np.greater_equal(
                fxt_plants_model.communities[cell_id].cohorts.dbh_value,
                prev_dbh_values[cell_id],
            )
        )

    # Ensure that currently non PFT turnovers are > 0 ...
    assert np.all(np.greater(fxt_plants_model.data["root_turnover_cnp"], 0))
    # ... except for stem turnover which currently has no turnover
    # (NOTE - this could change if we add branchfall)
    assert np.allclose(fxt_plants_model.data["stem_turnover_cnp"], 0)

    # Check carbon supply to soil
    assert np.all(np.greater(fxt_plants_model.data["root_carbohydrate_exudation"], 0))
    assert np.all(np.greater(fxt_plants_model.data["plant_symbiote_carbon_supply"], 0))

    # Check the PFT structured arrays - These are trickier because values can and should
    # be zero if the PFT is not in a cell but that's a good feature of the test

    # Calculate a boolean mask that shows which cells are expected to be populated
    mask = fxt_plants_model.data_object_templates["cnp_pft"].copy().astype(bool)
    for cid in mask.cell_id.values:
        for pft in set(fxt_plants_model.communities[cid].cohorts.pft_name):
            mask.loc[dict(cell_id=cid, pft=pft)] = True
    default_out = np.ones_like(mask)

    for var in [
        "foliage_turnover_cnp",
        "fruit_turnover_cnp",
        "seed_turnover_cnp",
        "canopy_seed_cnp",
        "canopy_fruit_cnp",
        "canopy_foliage_cnp",
    ]:
        # Filled in where the pft is present
        assert np.all(
            np.greater(fxt_plants_model.data[var], 0, where=mask, out=default_out)
        )
        # Otherwise empty
        assert np.all(
            np.equal(fxt_plants_model.data[var], 0, where=~mask, out=default_out)
        )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_update(
    fxt_plants_model, fixture_canopy_layer_data, tricky_plant_cohorts
):
    """Test the update method."""

    # The update method runs both update_canopy_layers and set_shortwave_absorption so
    # should restore all of the layers below.
    # TODO - amend this as and when layer heights gets centralised

    wipe_canopy_layers(fxt_plants_model)

    # Set the mortality and recruitment to zero
    fxt_plants_model.per_update_interval_propagule_recruitment_probability = 0
    fxt_plants_model.per_update_interval_stem_mortality_probability = 0

    # Check reset
    fxt_plants_model.update(time_index=0)

    # Check the canopy has been initialised and updated
    data_validator(
        fxt_plants_model,
        fixture_canopy_layer_data,
        skip=[
            "layer_heights_full",
            "leaf_area_index_canopy",
            "layer_fapar_canopy",
        ],
    )

    # # Check the growth of the cohorts
    # for community in fxt_plants_model.communities.values():
    #     for cohort in community:
    #         # Original 0.1 + 0.03 cm from current arbitrary increment
    #         assert np.allclose(cohort.dbh, 0.13)


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_populate_lignin_proportions(fxt_plants_model):
    """Test the populate_lignin_proportions method of the plants model."""

    # Check reset
    fxt_plants_model.reset_update_vars()
    fxt_plants_model.populate_lignin_proportions()
    consts = fxt_plants_model.model_constants

    # Check that all expected variables are generated and have the correct value
    assert np.allclose(fxt_plants_model.data["stem_lignin"], consts.stem_lignin)
    assert np.allclose(
        fxt_plants_model.data["senesced_leaf_lignin"], consts.senesced_leaf_lignin
    )
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_lignin"],
        consts.plant_reproductive_tissue_lignin,
    )
    assert np.allclose(fxt_plants_model.data["root_lignin"], consts.root_lignin)
    assert np.allclose(
        fxt_plants_model.data["subcanopy_vegetation_litter_lignin"],
        consts.subcanopy_vegetation_lignin,
    )
    assert np.allclose(
        fxt_plants_model.data["subcanopy_seedbank_litter_lignin"],
        consts.subcanopy_seedbank_lignin,
    )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_calculate_nutrient_uptake(fxt_plants_model, tricky_plant_cohorts):
    """Test the calculate_nutrient_uptake method of the plants model."""

    # Provide transpiration values
    fxt_plants_model.per_stem_transpiration = {
        cell_id: np.array([10]) for cell_id in fxt_plants_model.communities.keys()
    }
    # Check reset
    fxt_plants_model.calculate_nutrient_uptake()

    expected_ammonium = (
        10 * fxt_plants_model.data["dissolved_ammonium"] * 1.8015e-11 * 1000
    )
    expected_nitrate = (
        10 * fxt_plants_model.data["dissolved_nitrate"] * 1.8015e-11 * 1000
    )
    expected_phosphorus = (
        10 * fxt_plants_model.data["dissolved_phosphorus"] * 1.8015e-11 * 1000
    )

    # Check the uptake values in the data variable
    assert np.allclose(
        fxt_plants_model.data["plant_ammonium_uptake"], expected_ammonium
    )
    assert np.allclose(fxt_plants_model.data["plant_nitrate_uptake"], expected_nitrate)
    assert np.allclose(
        fxt_plants_model.data["plant_phosphorus_uptake"], expected_phosphorus
    )

    # Check the values in the stoichiometry surplus
    assert np.allclose(
        fxt_plants_model.biomasses[0].element_surpluses[:, 1],
        expected_ammonium[0].item() + expected_nitrate[0].item(),
    )
    assert np.allclose(
        fxt_plants_model.biomasses[0].element_surpluses[:, 2],
        expected_phosphorus[0].item(),
    )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_apply_mortality(mocker, fxt_plants_model, tricky_plant_cohorts):
    """Test the apply_mortality method of the plants model."""

    # Patch the RNG in mortality to kill one of every cohort - easier calculation of
    # expected values and make sure there is actual mortality in all cohorts. Using
    # side_effect with an iterable returns each value in turn, so matches the mortality
    # to the number of cohorts in each community.
    mocker.patch(
        "numpy.random.binomial",
        side_effect=[
            np.array([1] * len(c.cohorts))
            for _, c in fxt_plants_model.communities.items()
        ],
    )

    # Record the original population sizes.
    original_population = {
        cell_id: fxt_plants_model.communities[cell_id].cohorts.n_individuals.copy()
        for cell_id in fxt_plants_model.communities.keys()
    }

    fxt_plants_model.reset_update_vars()

    # Check mortality
    fxt_plants_model.apply_mortality()

    for cell_id in fxt_plants_model.communities.keys():
        # All cohorts are one individual smaller
        assert_allclose(
            original_population[cell_id],
            fxt_plants_model.communities[cell_id].cohorts.n_individuals + 1,
        )

        # Check the turnovers are now equal to the sums of a single stem of each cohort
        for var in ["stem", "root"]:
            tissue = fxt_plants_model.biomasses[cell_id].get_tissue(var)
            assert_allclose(
                fxt_plants_model.data[f"{var}_turnover_cnp"][cell_id],
                tissue.elemental_masses.sum(axis=0),
            )

        # More complex for fruit and seed - need to calculate per PFT values so need to
        # sum across the columns in the tissue biomasses for each PFT
        for var in ["fruit", "foliage", "seed"]:
            tissue = fxt_plants_model.biomasses[cell_id].get_tissue(var)

            # Check tissue by pft
            for idx, pft in enumerate(fxt_plants_model.flora.pft_name):
                cohorts_this_pft = (
                    fxt_plants_model.communities[cell_id].cohorts.pft_name == pft
                )
                pft_biomass = tissue.elemental_masses[cohorts_this_pft, :].sum(axis=0)

                assert_allclose(
                    fxt_plants_model.data[f"{var}_turnover_cnp"][cell_id, idx, :],
                    pft_biomass,
                )


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_PlantsModel_apply_recruitment(fxt_plants_model, tricky_plant_cohorts):
    """Test the apply_recruitment method of the plants model."""

    original_n_cohorts = [
        len(cm.cohorts.pft_name) for cm in fxt_plants_model.communities.values()
    ]
    original_n_propagules = (
        fxt_plants_model.data["plant_pft_propagules"].to_numpy().copy()
    )

    # Increase the probability of recruitment to force changes
    fxt_plants_model.per_update_interval_propagule_recruitment_probability = 0.5

    # Apply recruitment
    fxt_plants_model.apply_recruitment()

    # Check there are fewer propagules after the recruitment
    assert np.all(
        np.greater(
            original_n_propagules,
            fxt_plants_model.data["plant_pft_propagules"].to_numpy(),
        )
    )

    # Check there are more cohorts after the recruitment
    new_n_cohorts = [
        len(cm.cohorts.pft_name) for cm in fxt_plants_model.communities.values()
    ]

    assert np.all(np.less(original_n_cohorts, new_n_cohorts))


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_convert_to_litter_units(fxt_plants_model, tricky_plant_cohorts):
    """Tests the helper function that converts to litter model units."""

    input_mass = np.array([1e5, 3.4e2, 123.7, 0.007])
    expected_input_density = [12.345679, 0.0419753, 0.0152716, 8.64198e-7]

    actual_input_density = fxt_plants_model.convert_to_litter_units(
        input_mass=input_mass
    )

    assert np.allclose(expected_input_density, actual_input_density)


@pytest.mark.parametrize(argnames="tricky_plant_cohorts", argvalues=[False])
def test_convert_to_soil_units(fxt_plants_model, tricky_plant_cohorts):
    """Tests the helper function that converts to soil model units."""

    print(fxt_plants_model.model_timing.update_interval_quantity)

    input_mass = np.array([1e6, 3.4e3, 1237.0, 0.07])
    expected_input_density = [0.008818342, 2.998236e-5, 1.090829e-5, 6.17284e-10]

    actual_input_density = fxt_plants_model.convert_to_soil_units(input_mass=input_mass)

    assert np.allclose(expected_input_density, actual_input_density)
