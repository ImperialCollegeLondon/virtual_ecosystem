"""Collection of fixtures to assist the testing of the litter model."""

import pytest


@pytest.fixture
def fixture_litter_model(dummy_litter_data):
    """Create a litter model fixture based on the dummy litter data."""
    from tests.conftest import patch_bypass_setup, patch_run_update
    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    # Build the config object
    cfg_strings = "[core]\n[core.timing]\nupdate_interval = '48 hours'\n[litter]\n"

    config_data = ConfigurationLoader(cfg_strings=cfg_strings)
    configuration = generate_configuration(config_data.data)

    core_components = CoreComponents(configuration.core)

    with (
        patch_run_update(LitterModel),
        patch_bypass_setup(LitterModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        return LitterModel.from_config(
            data=dummy_litter_data,
            configuration=configuration,
            core_components=core_components,
        )


@pytest.fixture
def decay_rates(dummy_litter_data, fixture_core_components, fixture_litter_constants):
    """Decay rates for the various litter pools."""

    from virtual_ecosystem.models.litter.carbon import calculate_decay_rates

    decay_rates = calculate_decay_rates(
        lignin_above_structural=dummy_litter_data["lignin_above_structural"].to_numpy(),
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        air_temperatures=dummy_litter_data["air_temperature"],
        soil_temperatures=dummy_litter_data["soil_temperature"],
        water_potentials=dummy_litter_data["matric_potential"],
        layer_structure=fixture_core_components.layer_structure,
        constants=fixture_litter_constants,
    )

    return decay_rates


@pytest.fixture
def litter_chemistry(dummy_litter_data):
    """LitterChemistry object to be use throughout testing."""
    from virtual_ecosystem.models.litter.chemistry import LitterChemistry

    litter_chemistry = LitterChemistry(dummy_litter_data)

    return litter_chemistry


@pytest.fixture
def input_chemistries(litter_inputs, fixture_litter_constants):
    """Chemistries of each input flow."""
    from virtual_ecosystem.models.litter.inputs import calculate_input_chemistries

    input_chemistries = calculate_input_chemistries(
        litter_inputs=litter_inputs,
        struct_to_meta_nitrogen_ratio=fixture_litter_constants.structural_to_metabolic_n_ratio,
        struct_to_meta_phosphorus_ratio=fixture_litter_constants.structural_to_metabolic_p_ratio,
    )

    return input_chemistries


@pytest.fixture
def metabolic_splits(total_litter_input, fixture_litter_constants):
    """Metabolic splits for the various plant inputs."""
    from virtual_ecosystem.models.litter.inputs import (
        calculate_metabolic_proportions_of_input,
    )

    metabolic_splits = calculate_metabolic_proportions_of_input(
        total_input=total_litter_input,
        constants=fixture_litter_constants,
    )

    return metabolic_splits


@pytest.fixture
def post_consumption_pools(dummy_litter_data):
    """Pool sizes after animal consumption for each litter pool."""
    from virtual_ecosystem.models.litter.carbon import calculate_post_consumption_pools

    post_consumption_pools = calculate_post_consumption_pools(
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic"].to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural"].to_numpy(),
        woody=dummy_litter_data["litter_pool_woody"].to_numpy(),
        below_metabolic=dummy_litter_data["litter_pool_below_metabolic"].to_numpy(),
        below_structural=dummy_litter_data["litter_pool_below_structural"].to_numpy(),
        consumption_above_metabolic=dummy_litter_data[
            "litter_consumption_above_metabolic"
        ].to_numpy(),
        consumption_above_structural=dummy_litter_data[
            "litter_consumption_above_structural"
        ].to_numpy(),
        consumption_woody=dummy_litter_data["litter_consumption_woody"].to_numpy(),
        consumption_below_metabolic=dummy_litter_data[
            "litter_consumption_below_metabolic"
        ].to_numpy(),
        consumption_below_structural=dummy_litter_data[
            "litter_consumption_below_structural"
        ].to_numpy(),
    )

    return post_consumption_pools


@pytest.fixture
def total_litter_input(dummy_litter_data):
    """Total input mass a chemistry for each plant biomass type."""
    from virtual_ecosystem.models.litter.inputs import combine_input_sources

    total_litter_input = combine_input_sources(dummy_litter_data, update_interval=2.0)

    return total_litter_input


@pytest.fixture
def updated_pools(decay_rates, post_consumption_pools, litter_inputs):
    """Updated carbon mass of each pool."""
    from virtual_ecosystem.models.litter.carbon import calculate_updated_pools

    updated_pools = calculate_updated_pools(
        post_consumption_pools=post_consumption_pools,
        decay_rates=decay_rates,
        litter_inputs=litter_inputs,
        update_interval=2.0,
    )

    return updated_pools


@pytest.fixture
def litter_inputs(dummy_litter_data, fixture_litter_constants):
    """Complete set of details for inputs to the litter model."""
    from virtual_ecosystem.models.litter.inputs import LitterInputs

    litter_inputs = LitterInputs.create_from_data(
        data=dummy_litter_data,
        constants=fixture_litter_constants,
        update_interval=2.0,
    )

    return litter_inputs


@pytest.fixture
def litter_losses(
    dummy_litter_data,
    fixture_core_constants,
    post_consumption_pools,
    updated_pools,
    litter_inputs,
    input_chemistries,
):
    """Complete set of losses from the litter pools."""
    from virtual_ecosystem.models.litter.losses import calculate_litter_losses

    return calculate_litter_losses(
        data=dummy_litter_data,
        original_pools=post_consumption_pools,
        final_pools=updated_pools,
        litter_inputs=litter_inputs,
        input_chemistries=input_chemistries,
        update_interval=2.0,
        active_microbe_depth=fixture_core_constants.max_depth_of_microbial_activity,
    )
