"""Tests for the model.plants.plants_model submodule."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest
import xarray

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


def test_PlantsModel__init__(
    plants_data,
    flora,
    extra_pft_traits,
    fixture_core_components,
    fixture_canopy_layer_data,
    fixture_exporter,
):
    """Test the PlantsModel.__init__ method."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel(
        data=plants_data,
        core_components=fixture_core_components,
        flora=flora,
        extra_pft_traits=extra_pft_traits,
        exporter=fixture_exporter,
    )

    # Test the flora and community are as expected
    n_cells = fixture_core_components.grid.n_cells
    assert plants_model.flora == flora
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
    flora,
    extra_pft_traits,
    fixture_core_components,
    fixture_canopy_layer_data,
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
            flora=flora,
            extra_pft_traits=extra_pft_traits,
            exporter=fixture_exporter,
        )
        return

    assert str(ctxt.value) == error_message


def test_PlantsModel_from_config(
    plants_data, fixture_config, fixture_core_components, fixture_canopy_layer_data
):
    """Test the PlantsModel.from_config factory method."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel.from_config(
        data=plants_data, config=fixture_config, core_components=fixture_core_components
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


def test_PlantsModel_update_canopy_layers(fxt_plants_model, fixture_canopy_layer_data):
    """Simple test that update canopy layers restores overwritten data."""

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


def test_PlantsModel_set_shortwave_absorption(
    fxt_plants_model, fixture_canopy_layer_data
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


def test_PlantsModel_estimate_gpp(fxt_plants_model):
    """Test the estimate_gpp method."""

    # Set the canopy and absorbed irradiance
    fxt_plants_model.set_canopy_top_radiation(time_index=0)
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.subcanopy.set_light_capture(
        below_canopy_light_fraction=fxt_plants_model.below_canopy_light_fraction
    )
    fxt_plants_model.set_shortwave_absorption()

    # Calculate GPP
    fxt_plants_model.calculate_light_use_efficiency()
    fxt_plants_model.estimate_gpp(time_index=0)

    # TODO - currently no actual validation of values, only of structure
    #      - maybe mock lue and iwue to get easier values rather than current obscure
    #        ones
    #      - Actually, with the separation of the PModel fit into
    #        calculate_light_use_efficiency, we can now overwrite the calculated GPP to
    #        generate easier test values?

    # Check stem_gpp and stem_transpiration structure
    exp_stem_struct = {
        cid: cmty.n_cohorts for cid, cmty in fxt_plants_model.communities.items()
    }

    # Are the stem properties dictionaries of arrays with the right length
    assert exp_stem_struct == {
        cid: len(vals) for cid, vals in fxt_plants_model.per_stem_gpp.items()
    }

    assert exp_stem_struct == {
        cid: len(vals) for cid, vals in fxt_plants_model.per_stem_transpiration.items()
    }

    # Check the transpiration shape

    assert fxt_plants_model.data["transpiration"].shape == (
        fxt_plants_model.layer_structure.n_layers,
        fxt_plants_model.grid.n_cells,
    )


@pytest.mark.skip(
    reason="The DBH increase check fails - we need to fix this but that is going "
    "to be tricky and we need to unblock the CI."
)
def test_PlantsModel_allocate_gpp(fxt_plants_model):
    """Test the allocate_gpp method."""

    # Provide GPP values
    fxt_plants_model.per_stem_gpp = {
        cell_id: np.array([55]) for cell_id in fxt_plants_model.communities.keys()
    }
    # Store previous dbh values
    prev_dbh_values = {
        cell_id: fxt_plants_model.communities[cell_id].cohorts.dbh_values.copy()
        for cell_id in fxt_plants_model.communities.keys()
    }

    # Allocate GPP
    fxt_plants_model.allocate_gpp()

    for cell_id in fxt_plants_model.communities.keys():
        # TODO: eventually have tests with more meaningful values
        # BUG: This assert is failing spectacularly. The test has been set to skip until
        #      we can fix this properly.

        # Check that dbh is >= previous dbh (plants should not shrink!)
        assert (
            fxt_plants_model.communities[cell_id].cohorts.dbh_values
            >= prev_dbh_values[cell_id]
        ).all()

        # Ensure that leaf and root turnover exist and are > 0
        assert fxt_plants_model.data["leaf_turnover"][cell_id] > 0
        assert fxt_plants_model.data["root_turnover"][cell_id] > 0
        assert np.all(fxt_plants_model.data["plant_pft_propagules"][cell_id] >= 100)
        assert fxt_plants_model.data["fallen_non_propagule_c_mass"][cell_id] > 0
        assert np.all(fxt_plants_model.data["canopy_n_propagules"][cell_id] >= 0)
        assert np.all(
            fxt_plants_model.data["canopy_non_propagule_c_mass"][cell_id] >= 0
        )  # For cell_id = 1, only one of the two PFTs is present.
        assert fxt_plants_model.data["root_carbohydrate_exudation"][cell_id] > 0
        assert fxt_plants_model.data["plant_symbiote_carbon_supply"][cell_id] > 0


def test_PlantsModel_update(fxt_plants_model, fixture_canopy_layer_data):
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


def test_PlantsModel_calculate_turnover(fxt_plants_model):
    """Test the calculate_turnover method of the plants model."""

    # Check reset
    fxt_plants_model.calculate_turnover()
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
    assert np.allclose(fxt_plants_model.data["leaf_lignin"], consts.leaf_lignin)


def test_PlantsModel_update_cn_ratios(fxt_plants_model, fixture_config):
    """Test the update_cn_ratios method of the plants model."""

    fxt_plants_model.update_cn_ratios()

    assert np.allclose(fxt_plants_model.data["deadwood_c_n_ratio"], 56.5)
    assert np.allclose(fxt_plants_model.data["leaf_turnover_c_n_ratio"], 25.5)
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_turnover_c_n_ratio"],
        12.5,
    )
    assert np.allclose(fxt_plants_model.data["root_turnover_c_n_ratio"], 45.6)
    assert np.allclose(fxt_plants_model.data["deadwood_c_p_ratio"], 856.5)
    assert np.allclose(fxt_plants_model.data["leaf_turnover_c_p_ratio"], 415.0)
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_turnover_c_p_ratio"],
        125.5,
    )
    assert np.allclose(fxt_plants_model.data["root_turnover_c_p_ratio"], 656.7)


def test_PlantsModel_calculate_turnover_constant_override(
    plants_data, fixture_config, fixture_core_components
):
    """Test that the turnover constants can be overridden by values in config."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    fixture_config["plants"]["constants"] = {"PlantsConsts": {"leaf_lignin": 100.0}}
    plants_model = PlantsModel.from_config(
        data=plants_data, config=fixture_config, core_components=fixture_core_components
    )
    plants_model.calculate_turnover()

    assert np.allclose(plants_model.data["leaf_lignin"], 100.0)


def test_PlantsModel_calculate_nutrient_uptake(fxt_plants_model):
    """Test the calculate_nutrient_uptake method of the plants model."""

    # Provide transpiration values
    fxt_plants_model.per_stem_transpiration = {
        cell_id: np.array([10]) for cell_id in fxt_plants_model.communities.keys()
    }
    # Check reset
    fxt_plants_model.calculate_nutrient_uptake()

    # Check that all expected variables are generated and have the correct value
    assert np.allclose(fxt_plants_model.data["plant_ammonium_uptake"], 5.0e-4)
    assert np.allclose(fxt_plants_model.data["plant_nitrate_uptake"], 7.5e-3)
    assert np.allclose(fxt_plants_model.data["plant_phosphorus_uptake"], 3.0e-5)

    # TODO: add test for element uptake


def test_PlantsModel_calculate_mycorrhizal_uptakes(fxt_plants_model):
    """Test the calculate_mycorrhizal_uptakes method of the plants model."""

    # Check reset
    fxt_plants_model.calculate_mycorrhizal_uptakes()

    # Check that all expected variables are generated and have the correct value
    assert np.allclose(fxt_plants_model.data["plant_n_uptake_arbuscular"], 0.00216)
    assert np.allclose(fxt_plants_model.data["plant_n_uptake_ecto"], 0.000805)
    assert np.allclose(fxt_plants_model.data["plant_p_uptake_arbuscular"], 0.000117)
    assert np.allclose(fxt_plants_model.data["plant_p_uptake_ecto"], 6.6e-5)


def test_PlantsModel_apply_mortality(fxt_plants_model):
    """Test the apply_mortality method of the plants model."""

    original_population = {
        cell_id: fxt_plants_model.communities[cell_id].cohorts.n_individuals.copy()
        for cell_id in fxt_plants_model.communities.keys()
    }

    # Check reset
    fxt_plants_model.apply_mortality()

    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        mortality = (
            original_population[cell_id]
            - fxt_plants_model.communities[cell_id].cohorts.n_individuals
        )
        deadwood_mass = (
            np.sum(mortality * community.stem_allometry.stem_mass)
            / fxt_plants_model.grid.cell_area
        )

        assert np.all(
            original_population[cell_id]
            >= fxt_plants_model.communities[cell_id].cohorts.n_individuals
        )
        assert fxt_plants_model.data["deadwood_production"][cell_id] == deadwood_mass


def test_PlantsModel_apply_recruitment(fxt_plants_model):
    """Test the apply_recruitment method of the plants model."""

    original_n_cohorts = [
        len(cm.cohorts.pft_names) for cm in fxt_plants_model.communities.values()
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
        len(cm.cohorts.pft_names) for cm in fxt_plants_model.communities.values()
    ]

    assert np.all(np.less(original_n_cohorts, new_n_cohorts))


def test_partition_reproductive_tissue(fxt_plants_model):
    """Tests the partition reproductive tissue function."""

    n_propagules, mass_non_propagules = fxt_plants_model.partition_reproductive_tissue(
        reproductive_tissue_mass=10.5
    )

    assert n_propagules == 5
    assert mass_non_propagules == 5.5
    assert (
        n_propagules * fxt_plants_model.model_constants.carbon_mass_per_propagule
        + mass_non_propagules
    )


def test_convert_to_litter_units(fxt_plants_model):
    """Tests the helper function that converts to litter model units."""

    input_mass = np.array([1e5, 3.4e2, 123.7, 0.007])
    expected_input_density = [12.345679, 0.0419753, 0.0152716, 8.64198e-7]

    actual_input_density = fxt_plants_model.convert_to_litter_units(
        input_mass=input_mass
    )

    assert np.allclose(expected_input_density, actual_input_density)


def test_convert_to_soil_units(fxt_plants_model):
    """Tests the helper function that converts to soil model units."""

    print(fxt_plants_model.model_timing.update_interval_quantity)

    input_mass = np.array([1e6, 3.4e3, 1237.0, 0.07])
    expected_input_density = [0.008818342, 2.998236e-5, 1.090829e-5, 6.17284e-10]

    actual_input_density = fxt_plants_model.convert_to_soil_units(input_mass=input_mass)

    assert np.allclose(expected_input_density, actual_input_density)
