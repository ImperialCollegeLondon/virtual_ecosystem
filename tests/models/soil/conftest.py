"""Collection of fixtures to assist the testing of the soil model."""

import numpy as np
import pytest


@pytest.fixture
def dummy_carbon_data(fixture_core_components):
    """Creates a dummy carbon data object for use in tests."""
    from xarray import DataArray

    from virtual_ecosystem.core.data import Data

    # Setup the data object with four cells.
    data = Data(fixture_core_components.grid)

    # The required data is now added. This includes the five carbon pools: mineral
    # associated organic matter, low molecular weight carbon, microbial biomass and
    # necromass carbon and particulate organic matter. It also includes various factors
    # of the physical environment: pH, bulk density, soil moisture, soil temperature,
    # percentage clay in soil.
    data_values = {
        "soil_c_pool_lmwc": [0.05, 0.02, 0.1, 0.005],
        "soil_c_pool_maom": [2.5, 1.7, 4.5, 0.5],
        "soil_c_pool_bacteria": [5.8, 2.3, 11.3, 1.0],
        "soil_c_pool_saprotrophic_fungi": [0.89, 8.55, 2.21, 4.54],
        "soil_c_pool_arbuscular_mycorrhiza": [0.65, 1.47, 3.92, 9.04],
        "soil_c_pool_ectomycorrhiza": [0.47, 1.32, 4.2, 3.77],
        "soil_c_pool_pom": [0.1, 1.0, 0.7, 0.35],
        "soil_c_pool_necromass": [0.058, 0.015, 0.093, 0.105],
        "soil_enzyme_pom_bacteria": [0.022679, 0.009576, 0.050051, 0.003010],
        "soil_enzyme_maom_bacteria": [0.0356, 0.0117, 0.02509, 0.00456],
        "soil_enzyme_pom_fungi": [0.02607, 0.00575, 0.00646, 0.00441],
        "soil_enzyme_maom_fungi": [0.008669, 0.006826, 0.003807, 0.002163],
        "soil_n_pool_don": [0.000571428, 0.00142857, 0.00014285, 0.002857142],
        "soil_n_pool_particulate": [0.00714285, 0.00071425, 0.00285714, 0.01428571],
        "soil_n_pool_necromass": [0.00288462, 0.01788462, 0.02019231, 0.01115385],
        "soil_n_pool_maom": [0.86538462, 0.48076923, 0.32692308, 0.09615385],
        "soil_n_pool_ammonium": [6.9619638e-5, 0.0049914624, 0.000229067, 0.0051955339],
        "soil_n_pool_nitrate": [0.0024219014, 0.0044442996, 0.0003428348, 0.0131405173],
        "soil_p_pool_dop": [5.714e-6, 2.2857120e-5, 5.7142800e-5, 1.1428568e-4],
        "soil_p_pool_particulate": [2.857e-5, 2.85714e-4, 1.142856e-4, 5.714284e-4],
        "soil_p_pool_necromass": [0.00080769, 0.00011538, 0.00071538, 0.00044615],
        "soil_p_pool_maom": [0.01307692, 0.03461538, 0.01923077, 0.00384615],
        "soil_p_pool_primary": [0.0019594, 0.00535662, 0.00277434, 0.00059892],
        "soil_p_pool_secondary": [0.00705668, 0.03816896, 0.01152589, 0.00733107],
        "soil_p_pool_labile": [1.0582393e-5, 3.252961e-5, 6.806745e-5, 1.945635e-4],
        "pH": [3.0, 7.5, 9.0, 5.7],
        "clay_fraction": [0.8, 0.3, 0.1, 0.9],
        "litter_C_mineralisation_rate": [0.00212106, 0.00106053, 0.00049000, 0.0055],
        "litter_N_mineralisation_rate": [3.5351e-5, 7.0702e-5, 0.000183, 1.63333e-5],
        "litter_P_mineralisation_rate": [7.32e-6, 1.41404e-6, 2.82808e-6, 6.53332e-7],
        "plant_symbiote_carbon_supply": [0.01, 0.25, 0.0075, 0.0047],
        "root_carbohydrate_exudation": [0.025, 0.01, 0.05, 0.0025],
        "plant_ammonium_uptake": [5.0e-5, 2.5e-5, 1.0e-5, 1.0e-4],
        "plant_nitrate_uptake": [7.5e-4, 1.0e-3, 2.5e-4, 1.0e-4],
        "plant_phosphorus_uptake": [3.0e-6, 5e-5, 2.0e-6, 1.0e-6],
        "plant_n_uptake_arbuscular": [2.07e-5, 3.12e-5, 3.57e-6, 6.98e-5],
        "plant_n_uptake_ecto": [3.07e-5, 4.20e-5, 4.02e-6, 2.98e-5],
        "plant_p_uptake_arbuscular": [1.57e-6, 5.07e-5, 2.13e-6, 1.81e-6],
        "plant_p_uptake_ecto": [1.78e-6, 5.64e-5, 1.07e-6, 9.90e-7],
        "subcanopy_ammonium_uptake": [4.35e-6, 1.64e-5, 9.48e-6, 2.75e-5],
        "subcanopy_nitrate_uptake": [6.51e-4, 4.74e-4, 2.35e-4, 4.51e-5],
        "subcanopy_phosphorus_uptake": [7.58e-7, 4.83e-5, 1.96e-6, 4.91e-7],
        "animal_pom_consumption_carbon": [8.26e-3, 8.61e-3, 4.94e-3, 7.20e-3],
        "animal_pom_consumption_nitrogen": [4.86e-8, 2.86e-8, 6.95e-8, 4.95e-8],
        "animal_pom_consumption_phosphorus": [1.65e-8, 7.37e-8, 3.34e-8, 5.11e-8],
        "animal_bacteria_consumption": [5.86e-3, 9.87e-5, 9.87e-4, 4.49e-4],
        "animal_saprotrophic_fungi_consumption": [5.46e-4, 1.49e-4, 1.35e-4, 8.55e-4],
        "animal_ectomycorrhiza_consumption": [9.52e-4, 3.84e-4, 3.77e-4, 9.43e-4],
        "animal_arbuscular_mycorrhiza_consumption": [3.43e-4, 4.29e-4, 6.0e-4, 2.30e-4],
        "decay_of_fungal_fruiting_bodies": [2.2499e-4, 5.8168e-4, 3.2185e-4, 2.5871e-3],
        "new_fungal_fruiting_body_production": [0.0, 0.0, 0.0, 0.0],
        "mean_annual_temperature": [20.0, 20.0, 20.0, 20.0],
    }

    for var_name, var_values in data_values.items():
        data[var_name] = DataArray(var_values, dims=["cell_id"])

    # The layer dependent data has to be handled separately - at present all of these
    # are defined only for the topsoil layer
    lyr_str = fixture_core_components.layer_structure

    data["soil_moisture"] = lyr_str.from_template()
    data["soil_moisture"][lyr_str.index_all_soil] = np.array(
        [
            [232.61550125, 196.88733175, 126.065797, 75.63195175],
            [66.248474, 194.91137, 121.29988, 52.04422],
        ]
    )

    data["matric_potential"] = lyr_str.from_template()
    data["matric_potential"][lyr_str.index_all_soil] = np.array(
        [[-3.0, -10.0, -250.0, -10000.0], [-2.8625, -8.978, -137.8, -8553.25]]
    )

    data["soil_temperature"] = lyr_str.from_template()
    data["soil_temperature"][lyr_str.index_all_soil] = np.array(
        [[35.0, 37.5, 40.0, 25.0], [22.5, 22.5, 22.5, 22.5]]
    )

    data["vertical_flow"] = lyr_str.from_template()
    data["vertical_flow"][lyr_str.index_all_soil] = np.array(
        [[0.1, 0.5, 2.5, 1.59], [0.15, 0.75, 2.75, 1.33]]
    )

    data["air_temperature"] = lyr_str.from_template()
    data["air_temperature"][lyr_str.index_filled_atmosphere] = np.array(
        [30.0, 29.844995, 28.87117, 27.206405, 16.145945]
    )[:, None]

    data["decomposed_excrement_cnp"] = DataArray(
        data=[
            [4.214e-5, 1.939e-6, 3.174e-6],
            [0.000388, 9.895e-5, 5.681e-6],
            [0.000555, 8.199e-7, 6.278e-6],
            [0.003313, 0.0002465, 3.846e-5],
        ],
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    data["decomposed_carcasses_cnp"] = DataArray(
        data=[
            [0.0002844, 1.544e-6, 8.935e-7],
            [0.00011089, 7.520e-5, 1.932e-6],
            [2.459e-5, 1.433e-5, 4.928e-6],
            [0.003891, 0.0002582, 3.769e-6],
        ],
        coords={"cell_id": data["cell_id"], "element": ["C", "N", "P"]},
    )

    return data


@pytest.fixture
def fixture_soil_configuration(microbial_groups_cfg):
    """Create a soil config with faster update interval."""
    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )

    config_data = ConfigurationLoader(
        cfg_strings=[
            "[core]\n[core.timing]\nupdate_interval = '12 hours'",
            "[hydrology]",
            microbial_groups_cfg,
        ]
    )
    return generate_configuration(config_data.data)


@pytest.fixture
def fixture_soil_core_components(fixture_soil_configuration):
    """Create a core components from the fixture_soil_config."""
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.core.model_config import CoreConfiguration

    core_cfg = fixture_soil_configuration.get_subconfiguration(
        "core", CoreConfiguration
    )
    return CoreComponents(config=core_cfg)


@pytest.fixture
def fixture_soil_model(
    dummy_carbon_data,
    fixture_soil_configuration,
    fixture_soil_core_components,
):
    """Create a soil model fixture based on the dummy carbon data."""
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    return SoilModel.from_config(
        data=dummy_carbon_data,
        configuration=fixture_soil_configuration,
        core_components=fixture_soil_core_components,
    )


@pytest.fixture
def environmental_factors(
    dummy_carbon_data, fixture_soil_constants, fixture_core_components
):
    """Environmental factors based on dummy carbon data."""
    from virtual_ecosystem.models.litter.env_factors import (
        average_water_potential_over_microbially_active_layers,
    )
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_environmental_effect_factors,
    )

    return calculate_environmental_effect_factors(
        soil_water_potential=average_water_potential_over_microbially_active_layers(
            water_potentials=dummy_carbon_data["matric_potential"],
            layer_structure=fixture_core_components.layer_structure,
        ),
        pH=dummy_carbon_data["pH"].to_numpy(),
        clay_fraction=dummy_carbon_data["clay_fraction"].to_numpy(),
        constants=fixture_soil_constants,
    )


@pytest.fixture
def carbon_supply_from_plants(
    dummy_carbon_data, fixture_core_constants, fixture_soil_constants
):
    """Carbon supply from plants split between the different symbiotic groups."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        calculate_symbiotic_carbon_supply,
    )

    return calculate_symbiotic_carbon_supply(
        total_plant_supply=dummy_carbon_data["plant_symbiote_carbon_supply"]
        / fixture_core_constants.max_depth_of_microbial_activity,
        nitrogen_fixer_fraction=fixture_soil_constants.nitrogen_fixer_supply_fraction,
        ectomycorrhiza_fraction=fixture_soil_constants.ectomycorrhiza_supply_fraction,
    )


@pytest.fixture
def averaged_soil_temp(dummy_carbon_data, fixture_core_components):
    """Soil temperature averaged over the microbially active layers."""
    from virtual_ecosystem.models.litter.env_factors import (
        average_temperature_over_microbially_active_layers,
    )

    return average_temperature_over_microbially_active_layers(
        soil_temperatures=dummy_carbon_data["soil_temperature"],
        surface_temperature=dummy_carbon_data["air_temperature"][
            fixture_core_components.layer_structure.index_surface_scalar
        ].to_numpy(),
        layer_structure=fixture_core_components.layer_structure,
    )


@pytest.fixture
def soil_pool_data(dummy_carbon_data):
    """Fixture containing the soil data for all the pools that change."""
    from virtual_ecosystem.models.soil.pools import PoolData
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    pools = {
        var: pool
        for var, pool in dummy_carbon_data.data.items()
        if var in SoilModel.vars_updated
        or var in ["new_fungal_fruiting_body_production"]
    }

    return PoolData(**pools)


@pytest.fixture
def enzyme_mediated_rates(
    dummy_carbon_data,
    soil_pool_data,
    fixture_core_components,
    environmental_factors,
    enzyme_classes,
):
    """Enzyme mediated rates based on dummy carbon data."""
    from virtual_ecosystem.models.soil.pools import calculate_enzyme_mediated_rates

    return calculate_enzyme_mediated_rates(
        pools=soil_pool_data,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        enzyme_classes=enzyme_classes,
    )


@pytest.fixture
def necromass_breakdown(dummy_carbon_data, fixture_soil_constants):
    """Necromass breakdown rate based on dummy carbon data."""
    from virtual_ecosystem.models.soil.pools import calculate_necromass_breakdown

    return calculate_necromass_breakdown(
        soil_c_pool_necromass=dummy_carbon_data["soil_c_pool_necromass"],
        necromass_decay_rate=fixture_soil_constants.necromass_decay_rate,
    )


@pytest.fixture
def necromass_sorption(dummy_carbon_data, fixture_soil_constants):
    """Necromass sorption rate based on dummy carbon data."""
    from virtual_ecosystem.models.soil.pools import calculate_sorption_to_maom

    return calculate_sorption_to_maom(
        soil_c_pool=dummy_carbon_data["soil_c_pool_necromass"],
        sorption_rate_constant=fixture_soil_constants.necromass_sorption_rate,
    )


@pytest.fixture
def lmwc_sorption(dummy_carbon_data, fixture_soil_constants):
    """Low molecular weight carbon sorption rate based on dummy carbon data."""
    from virtual_ecosystem.models.soil.pools import calculate_sorption_to_maom

    return calculate_sorption_to_maom(
        soil_c_pool=dummy_carbon_data["soil_c_pool_lmwc"],
        sorption_rate_constant=fixture_soil_constants.lmwc_sorption_rate,
    )


@pytest.fixture
def maom_desorption(dummy_carbon_data, fixture_soil_constants):
    """MAOM desorption rate based on dummy carbon data."""
    from virtual_ecosystem.models.soil.pools import calculate_maom_desorption

    return calculate_maom_desorption(
        soil_c_pool_maom=dummy_carbon_data["soil_c_pool_maom"],
        desorption_rate_constant=fixture_soil_constants.maom_desorption_rate,
    )


@pytest.fixture
def functional_groups(fixture_configuration, enzyme_classes, fixture_core_constants):
    """Set of functional groups based on the soil model constants."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_microbial_groups,
    )

    return make_full_set_of_microbial_groups(
        config=fixture_configuration.soil,
        enzyme_classes=enzyme_classes,
        core_constants=fixture_core_constants,
    )


@pytest.fixture
def enzyme_classes(fixture_configuration):
    """Set of functional groups based on the soil model constants."""

    return {
        f"{e.source}_{e.substrate}": e
        for e in fixture_configuration.soil.enzyme_class_definition
    }


@pytest.fixture
def enzyme_changes(soil_pool_data, enzyme_production, enzyme_classes):
    """Changes for each each enzyme class."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_enzyme_changes,
    )

    return calculate_enzyme_changes(
        pools=soil_pool_data,
        enzyme_production=enzyme_production,
        enzyme_classes=enzyme_classes,
    )


@pytest.fixture
def biomass_losses(soil_pool_data, functional_groups, averaged_soil_temp):
    """Rates of biomass loss from each microbial pool."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_biomass_losses,
    )

    return calculate_biomass_losses(
        pools=soil_pool_data,
        microbial_groups=functional_groups,
        soil_temp=averaged_soil_temp,
    )


@pytest.fixture
def growth_rates(
    dummy_carbon_data,
    fixture_soil_constants,
    environmental_factors,
    functional_groups,
    soil_pool_data,
    averaged_soil_temp,
    carbon_supply_from_plants,
):
    """Fixture to store growth rates of all the microbial groups."""

    from virtual_ecosystem.models.soil.pools import calculate_nutrient_uptake_rates

    bacterial_growth, _ = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=soil_pool_data.soil_c_pool_lmwc,
        soil_n_pool_don=soil_pool_data.soil_n_pool_don,
        soil_n_pool_ammonium=soil_pool_data.soil_n_pool_ammonium,
        soil_n_pool_nitrate=soil_pool_data.soil_n_pool_nitrate,
        soil_p_pool_dop=soil_pool_data.soil_p_pool_dop,
        soil_p_pool_labile=soil_pool_data.soil_p_pool_labile,
        microbial_pool_size=soil_pool_data.soil_c_pool_bacteria,
        external_carbon_supply=None,
        nitrogen_exchange=None,
        phosphorus_exchange=None,
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        constants=fixture_soil_constants,
        functional_group=functional_groups["bacteria"],
    )
    saprotrophic_fungal_growth, _ = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=soil_pool_data.soil_c_pool_lmwc,
        soil_n_pool_don=soil_pool_data.soil_n_pool_don,
        soil_n_pool_ammonium=soil_pool_data.soil_n_pool_ammonium,
        soil_n_pool_nitrate=soil_pool_data.soil_n_pool_nitrate,
        soil_p_pool_dop=soil_pool_data.soil_p_pool_dop,
        soil_p_pool_labile=soil_pool_data.soil_p_pool_labile,
        microbial_pool_size=soil_pool_data.soil_c_pool_saprotrophic_fungi,
        external_carbon_supply=None,
        nitrogen_exchange=None,
        phosphorus_exchange=None,
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        constants=fixture_soil_constants,
        functional_group=functional_groups["saprotrophic_fungi"],
    )
    arbuscular_mycorrhizal_growth, _ = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=soil_pool_data.soil_c_pool_lmwc,
        soil_n_pool_don=soil_pool_data.soil_n_pool_don,
        soil_n_pool_ammonium=soil_pool_data.soil_n_pool_ammonium,
        soil_n_pool_nitrate=soil_pool_data.soil_n_pool_nitrate,
        soil_p_pool_dop=soil_pool_data.soil_p_pool_dop,
        soil_p_pool_labile=soil_pool_data.soil_p_pool_labile,
        microbial_pool_size=soil_pool_data.soil_c_pool_arbuscular_mycorrhiza,
        external_carbon_supply=carbon_supply_from_plants.arbuscular_mycorrhiza,
        nitrogen_exchange=dummy_carbon_data["plant_n_uptake_arbuscular"],
        phosphorus_exchange=dummy_carbon_data["plant_p_uptake_arbuscular"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        constants=fixture_soil_constants,
        functional_group=functional_groups["arbuscular_mycorrhiza"],
    )
    ectomycorrhizal_growth, _ = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=soil_pool_data.soil_c_pool_lmwc,
        soil_n_pool_don=soil_pool_data.soil_n_pool_don,
        soil_n_pool_ammonium=soil_pool_data.soil_n_pool_ammonium,
        soil_n_pool_nitrate=soil_pool_data.soil_n_pool_nitrate,
        soil_p_pool_dop=soil_pool_data.soil_p_pool_dop,
        soil_p_pool_labile=soil_pool_data.soil_p_pool_labile,
        microbial_pool_size=soil_pool_data.soil_c_pool_ectomycorrhiza,
        external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
        nitrogen_exchange=dummy_carbon_data["plant_n_uptake_ecto"],
        phosphorus_exchange=dummy_carbon_data["plant_p_uptake_ecto"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        constants=fixture_soil_constants,
        functional_group=functional_groups["ectomycorrhiza"],
    )

    return {
        "bacteria": bacterial_growth,
        "saprotrophic_fungi": saprotrophic_fungal_growth,
        "arbuscular_mycorrhiza": arbuscular_mycorrhizal_growth,
        "ectomycorrhiza": ectomycorrhizal_growth,
    }


@pytest.fixture
def enzyme_production(functional_groups, growth_rates):
    """Fixture to store the total production rates for each enzyme class."""
    from virtual_ecosystem.models.soil.pools import calculate_enzyme_production

    return calculate_enzyme_production(
        microbial_groups=functional_groups,
        growth_rates=growth_rates,
    )


@pytest.fixture
def carbon_use_efficiency(averaged_soil_temp, fixture_soil_constants):
    """Fixture to store the carbon use efficiency."""
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_carbon_use_efficiency,
    )

    return calculate_carbon_use_efficiency(
        soil_temp=averaged_soil_temp,
        reference_cue_logit=fixture_soil_constants.reference_cue_logit,
        cue_reference_temp=fixture_soil_constants.cue_reference_temp,
        logit_cue_with_temp=fixture_soil_constants.logit_cue_with_temperature,
    )


@pytest.fixture
def max_uptake_rates(
    dummy_carbon_data, environmental_factors, averaged_soil_temp, functional_groups
):
    """Fixture containing the maximum uptake rates for each nutrient."""
    from virtual_ecosystem.models.soil.uptake import calculate_maximum_uptake_rates

    return calculate_maximum_uptake_rates(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
        soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        microbial_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        functional_group=functional_groups["bacteria"],
    )
