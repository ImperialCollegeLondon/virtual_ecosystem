"""Collection of fixtures to assist the testing of the soil model."""

import pytest


@pytest.fixture
def fixture_soil_config(microbial_groups_cfg):
    """Create a soil config with faster update interval."""
    from virtual_ecosystem.core.config import Config

    return Config(
        cfg_strings=[
            "[core]\n[core.timing]\nupdate_interval = '12 hours'",
            microbial_groups_cfg,
        ]
    )


@pytest.fixture
def fixture_soil_core_components(fixture_soil_config):
    """Create a core components from the fixture_soil_config."""
    from virtual_ecosystem.core.core_components import CoreComponents

    return CoreComponents(fixture_soil_config)


@pytest.fixture
def fixture_soil_model(
    dummy_carbon_data, fixture_soil_config, fixture_soil_core_components
):
    """Create a soil model fixture based on the dummy carbon data."""
    from tests.conftest import patch_bypass_setup, patch_run_update
    from virtual_ecosystem.models.soil.soil_model import SoilModel

    with (
        patch_run_update(SoilModel),
        patch_bypass_setup(SoilModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        return SoilModel.from_config(
            data=dummy_carbon_data,
            core_components=fixture_soil_core_components,
            config=fixture_soil_config,
        )


@pytest.fixture
def environmental_factors(dummy_carbon_data, fixture_core_components):
    """Environmental factors based on dummy carbon data."""
    from virtual_ecosystem.models.litter.env_factors import (
        average_water_potential_over_microbially_active_layers,
    )
    from virtual_ecosystem.models.soil.constants import SoilConsts
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
        constants=SoilConsts,
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
def necromass_breakdown(dummy_carbon_data):
    """Necromass breakdown rate based on dummy carbon data."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_necromass_breakdown

    return calculate_necromass_breakdown(
        soil_c_pool_necromass=dummy_carbon_data["soil_c_pool_necromass"],
        necromass_decay_rate=SoilConsts.necromass_decay_rate,
    )


@pytest.fixture
def necromass_sorption(dummy_carbon_data):
    """Necromass sorption rate based on dummy carbon data."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_sorption_to_maom

    return calculate_sorption_to_maom(
        soil_c_pool=dummy_carbon_data["soil_c_pool_necromass"],
        sorption_rate_constant=SoilConsts.necromass_sorption_rate,
    )


@pytest.fixture
def lmwc_sorption(dummy_carbon_data):
    """Low molecular weight carbon sorption rate based on dummy carbon data."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_sorption_to_maom

    return calculate_sorption_to_maom(
        soil_c_pool=dummy_carbon_data["soil_c_pool_lmwc"],
        sorption_rate_constant=SoilConsts.lmwc_sorption_rate,
    )


@pytest.fixture
def maom_desorption(dummy_carbon_data):
    """MAOM desorption rate based on dummy carbon data."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_maom_desorption

    return calculate_maom_desorption(
        soil_c_pool_maom=dummy_carbon_data["soil_c_pool_maom"],
        desorption_rate_constant=SoilConsts.maom_desorption_rate,
    )


@pytest.fixture
def functional_groups(fixture_config, enzyme_classes):
    """Set of functional groups based on the soil model constants."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_microbial_groups,
    )

    return make_full_set_of_microbial_groups(
        config=fixture_config, enzyme_classes=enzyme_classes
    )


@pytest.fixture
def enzyme_classes(fixture_config):
    """Set of functional groups based on the soil model constants."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzymes,
    )

    return make_full_set_of_enzymes(config=fixture_config)


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
    environmental_factors,
    functional_groups,
    soil_pool_data,
    dummy_carbon_data,
    fixture_core_components,
):
    """Fixture to store growth rates of all the microbial groups."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_nutrient_uptake_rates

    bacterial_growth, _ = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=soil_pool_data.soil_c_pool_lmwc,
        soil_n_pool_don=soil_pool_data.soil_n_pool_don,
        soil_n_pool_ammonium=soil_pool_data.soil_n_pool_ammonium,
        soil_n_pool_nitrate=soil_pool_data.soil_n_pool_nitrate,
        soil_p_pool_dop=soil_pool_data.soil_p_pool_dop,
        soil_p_pool_labile=soil_pool_data.soil_p_pool_labile,
        microbial_pool_size=soil_pool_data.soil_c_pool_bacteria,
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        constants=SoilConsts,
        functional_group=functional_groups["bacteria"],
    )
    fungal_growth, _ = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=soil_pool_data.soil_c_pool_lmwc,
        soil_n_pool_don=soil_pool_data.soil_n_pool_don,
        soil_n_pool_ammonium=soil_pool_data.soil_n_pool_ammonium,
        soil_n_pool_nitrate=soil_pool_data.soil_n_pool_nitrate,
        soil_p_pool_dop=soil_pool_data.soil_p_pool_dop,
        soil_p_pool_labile=soil_pool_data.soil_p_pool_labile,
        microbial_pool_size=soil_pool_data.soil_c_pool_saprotrophic_fungi,
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        constants=SoilConsts,
        functional_group=functional_groups["saprotrophic_fungi"],
    )

    return {"bacteria": bacterial_growth, "saprotrophic_fungi": fungal_growth}


@pytest.fixture
def enzyme_production(functional_groups, growth_rates):
    """Fixture to store the total production rates for each enzyme class."""
    from virtual_ecosystem.models.soil.pools import calculate_enzyme_production

    return calculate_enzyme_production(
        microbial_groups=functional_groups,
        growth_rates=growth_rates,
    )
