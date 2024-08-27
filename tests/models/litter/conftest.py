"""Collection of fixtures to assist the testing of the litter model."""

import numpy as np
import pytest
from xarray import DataArray

from virtual_ecosystem.models.litter.constants import LitterConsts


@pytest.fixture
def fixture_litter_model(dummy_litter_data, fixture_core_components):
    """Create a litter model fixture based on the dummy litter data."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.litter.litter_model import LitterModel

    # Build the config object
    config = Config(
        cfg_strings="[core]\n[core.timing]\nupdate_interval = '24 hours'\n[litter]\n"
    )
    core_components = CoreComponents(config)

    return LitterModel.from_config(
        data=dummy_litter_data, core_components=core_components, config=config
    )


@pytest.fixture
def dummy_litter_data(fixture_core_components):
    """Creates a dummy litter data object for use in tests."""

    from virtual_ecosystem.core.data import Data

    lyr_strct = fixture_core_components.layer_structure

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # These values are taken from SAFE Project data, albeit in a very unsystematic
    # manner. The repeated fourth value is simply to adapt three hand validated examples
    # to the shared fixture core components grid
    pool_values = {
        "litter_pool_above_metabolic": [0.3, 0.15, 0.07, 0.07],
        "litter_pool_above_structural": [0.5, 0.25, 0.09, 0.09],
        "litter_pool_woody": [4.7, 11.8, 7.3, 7.3],
        "litter_pool_below_metabolic": [0.4, 0.37, 0.07, 0.07],
        "litter_pool_below_structural": [0.6, 0.31, 0.02, 0.02],
        "lignin_above_structural": [0.5, 0.1, 0.7, 0.7],
        "lignin_woody": [0.5, 0.8, 0.35, 0.35],
        "lignin_below_structural": [0.5, 0.25, 0.75, 0.75],
        "c_n_ratio_above_metabolic": [7.3, 8.7, 10.1, 9.8],
        "c_n_ratio_above_structural": [37.5, 43.2, 45.8, 50.2],
        "c_n_ratio_woody": [55.5, 63.3, 47.3, 59.1],
        "c_n_ratio_below_metabolic": [10.7, 11.3, 15.2, 12.4],
        "c_n_ratio_below_structural": [50.5, 55.6, 73.1, 61.2],
        "c_p_ratio_above_metabolic": [57.3, 68.7, 100.1, 95.8],
        "c_p_ratio_above_structural": [337.5, 473.2, 415.8, 570.2],
        "c_p_ratio_woody": [555.5, 763.3, 847.3, 599.1],
        "c_p_ratio_below_metabolic": [310.7, 411.3, 315.2, 412.4],
        "c_p_ratio_below_structural": [550.5, 595.6, 773.1, 651.2],
        "decomposed_excrement": [8e-07, 8.42857e-07, 3.28571e-05, 3.28571e-05],
        "decomposed_carcasses": [1.0714e-4, 4.8571e-4, 1.15714e-3, 1.15714e-3],
        "deadwood_production": [0.075, 0.099, 0.063, 0.033],
        "leaf_turnover": [0.027, 0.0003, 0.021, 0.0285],
        "plant_reproductive_tissue_turnover": [0.003, 0.0075, 0.00255, 0.00375],
        "root_turnover": [0.027, 0.021, 0.0003, 0.0249],
        "deadwood_lignin": [0.233, 0.545, 0.612, 0.378],
        "leaf_turnover_lignin": [0.05, 0.25, 0.3, 0.57],
        "plant_reproductive_tissue_turnover_lignin": [0.01, 0.03, 0.04, 0.02],
        "root_turnover_lignin": [0.2, 0.35, 0.27, 0.4],
        "deadwood_c_n_ratio": [60.7, 57.9, 73.1, 55.1],
        "leaf_turnover_c_n_ratio": [15.0, 25.5, 43.1, 57.4],
        "plant_reproductive_tissue_turnover_c_n_ratio": [12.5, 23.8, 15.7, 18.2],
        "root_turnover_c_n_ratio": [30.3, 45.6, 43.3, 37.1],
        "deadwood_c_p_ratio": [856.5, 675.4, 933.2, 888.8],
        "leaf_turnover_c_p_ratio": [415.0, 327.4, 554.5, 380.9],
        "plant_reproductive_tissue_turnover_c_p_ratio": [125.5, 105.0, 145.0, 189.2],
        "root_turnover_c_p_ratio": [656.7, 450.6, 437.3, 371.9],
    }

    for var, vals in pool_values.items():
        data[var] = DataArray(vals, dims=["cell_id"])

    # Vertically structured variables
    data["soil_temperature"] = lyr_strct.from_template()
    data["soil_temperature"][lyr_strct.index_topsoil] = 20
    data["soil_temperature"][lyr_strct.index_subsoil] = [19.5, 18.7, 18.7, 17.6]

    # At present the soil model only uses the top soil layer, so this is the
    # only one with real test values in
    data["matric_potential"] = lyr_strct.from_template()
    data["matric_potential"][lyr_strct.index_topsoil] = [-10.0, -25.0, -100.0, -100.0]
    data["matric_potential"][lyr_strct.index_subsoil] = [-11.0, -29.5, -123.0, -154.1]

    data["air_temperature"] = lyr_strct.from_template()
    data["air_temperature"][lyr_strct.index_filled_atmosphere] = np.array(
        [30.0, 29.844995, 28.87117, 27.206405, 16.145945]
    )[:, None]

    return data


@pytest.fixture
def decay_rates(dummy_litter_data, fixture_core_components):
    """Decay rates for the various litter pools."""

    from virtual_ecosystem.models.litter.carbon import calculate_decay_rates

    decay_rates = calculate_decay_rates(
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic"].to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural"].to_numpy(),
        woody=dummy_litter_data["litter_pool_woody"].to_numpy(),
        below_metabolic=dummy_litter_data["litter_pool_below_metabolic"].to_numpy(),
        below_structural=dummy_litter_data["litter_pool_below_structural"].to_numpy(),
        lignin_above_structural=dummy_litter_data["lignin_above_structural"].to_numpy(),
        lignin_woody=dummy_litter_data["lignin_woody"].to_numpy(),
        lignin_below_structural=dummy_litter_data["lignin_below_structural"].to_numpy(),
        air_temperatures=dummy_litter_data["air_temperature"],
        soil_temperatures=dummy_litter_data["soil_temperature"],
        water_potentials=dummy_litter_data["matric_potential"],
        layer_structure=fixture_core_components.layer_structure,
        constants=LitterConsts,
    )

    return decay_rates


@pytest.fixture
def metabolic_splits(dummy_litter_data):
    """Metabolic splits for the various plant inputs."""

    from virtual_ecosystem.models.litter.input_partition import (
        calculate_metabolic_proportions_of_input,
    )

    metabolic_splits = calculate_metabolic_proportions_of_input(
        leaf_turnover_lignin_proportion=dummy_litter_data[
            "leaf_turnover_lignin"
        ].to_numpy(),
        reproduct_turnover_lignin_proportion=dummy_litter_data[
            "plant_reproductive_tissue_turnover_lignin"
        ].to_numpy(),
        root_turnover_lignin_proportion=dummy_litter_data[
            "root_turnover_lignin"
        ].to_numpy(),
        leaf_turnover_c_n_ratio=dummy_litter_data["leaf_turnover_c_n_ratio"].to_numpy(),
        reproduct_turnover_c_n_ratio=dummy_litter_data[
            "plant_reproductive_tissue_turnover_c_n_ratio"
        ].to_numpy(),
        root_turnover_c_n_ratio=dummy_litter_data["root_turnover_c_n_ratio"].to_numpy(),
        leaf_turnover_c_p_ratio=dummy_litter_data["leaf_turnover_c_p_ratio"].to_numpy(),
        reproduct_turnover_c_p_ratio=dummy_litter_data[
            "plant_reproductive_tissue_turnover_c_p_ratio"
        ].to_numpy(),
        root_turnover_c_p_ratio=dummy_litter_data["root_turnover_c_p_ratio"].to_numpy(),
        constants=LitterConsts,
    )

    return metabolic_splits


@pytest.fixture
def plant_inputs(dummy_litter_data, metabolic_splits):
    """Plant inputs to each of the litter pools."""

    from virtual_ecosystem.models.litter.input_partition import (
        partion_plant_inputs_between_pools,
    )

    plant_inputs = partion_plant_inputs_between_pools(
        deadwood_production=dummy_litter_data["deadwood_production"],
        leaf_turnover=dummy_litter_data["leaf_turnover"],
        reproduct_turnover=dummy_litter_data["plant_reproductive_tissue_turnover"],
        root_turnover=dummy_litter_data["root_turnover"],
        metabolic_splits=metabolic_splits,
    )

    return plant_inputs


@pytest.fixture
def litter_chemistry(dummy_litter_data):
    """LitterChemistry object to be use throughout testing."""
    from virtual_ecosystem.models.litter.chemistry import LitterChemistry

    litter_chemistry = LitterChemistry(dummy_litter_data, constants=LitterConsts)

    return litter_chemistry


@pytest.fixture
def input_lignin(dummy_litter_data, plant_inputs, litter_chemistry):
    """Lignin proportion of the relevant input flows."""

    input_lignin = litter_chemistry.calculate_litter_input_lignin_concentrations(
        plant_input_below_struct=plant_inputs["below_ground_structural"],
        plant_input_above_struct=plant_inputs["above_ground_structural"],
    )

    return input_lignin


@pytest.fixture
def input_c_n_ratios(dummy_litter_data, metabolic_splits, litter_chemistry):
    """Carbon:nitrogen ratio of each input flow."""

    input_c_n_ratios = litter_chemistry.calculate_litter_input_nitrogen_ratios(
        metabolic_splits=metabolic_splits,
        struct_to_meta_nitrogen_ratio=LitterConsts.structural_to_metabolic_n_ratio,
    )

    return input_c_n_ratios


@pytest.fixture
def input_c_p_ratios(dummy_litter_data, metabolic_splits, litter_chemistry):
    """Carbon:nitrogen ratio of each input flow."""

    input_c_p_ratios = litter_chemistry.calculate_litter_input_phosphorus_ratios(
        metabolic_splits=metabolic_splits,
        struct_to_meta_phosphorus_ratio=LitterConsts.structural_to_metabolic_p_ratio,
    )

    return input_c_p_ratios


@pytest.fixture
def updated_pools(dummy_litter_data, decay_rates, plant_inputs):
    """Updated carbon mass of each pool."""
    from virtual_ecosystem.models.litter.carbon import calculate_updated_pools

    updated_pools = calculate_updated_pools(
        above_metabolic=dummy_litter_data["litter_pool_above_metabolic"].to_numpy(),
        above_structural=dummy_litter_data["litter_pool_above_structural"].to_numpy(),
        woody=dummy_litter_data["litter_pool_woody"].to_numpy(),
        below_metabolic=dummy_litter_data["litter_pool_below_metabolic"].to_numpy(),
        below_structural=dummy_litter_data["litter_pool_below_structural"].to_numpy(),
        decomposed_excrement=dummy_litter_data["decomposed_excrement"].to_numpy(),
        decomposed_carcasses=dummy_litter_data["decomposed_carcasses"].to_numpy(),
        decay_rates=decay_rates,
        plant_inputs=plant_inputs,
        update_interval=2.0,
    )

    return updated_pools
