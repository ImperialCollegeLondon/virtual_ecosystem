"""Collection of fixtures to assist the testing of the soil model."""

import pytest

from virtual_ecosystem.models.soil.env_factors import EnvironmentalEffectFactors


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
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.env_factors import (
        calculate_clay_impact_on_enzyme_saturation,
        calculate_pH_suitability,
        calculate_water_potential_impact_on_microbes,
    )

    soil_constants = SoilConsts()

    water_factors = calculate_water_potential_impact_on_microbes(
        water_potential=dummy_carbon_data["matric_potential"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        water_potential_halt=soil_constants.soil_microbe_water_potential_halt,
        water_potential_opt=soil_constants.soil_microbe_water_potential_optimum,
        response_curvature=soil_constants.microbial_water_response_curvature,
    )

    pH_factors = calculate_pH_suitability(
        soil_pH=dummy_carbon_data["pH"].to_numpy(),
        maximum_pH=soil_constants.max_pH_microbes,
        minimum_pH=soil_constants.min_pH_microbes,
        lower_optimum_pH=soil_constants.lowest_optimal_pH_microbes,
        upper_optimum_pH=soil_constants.highest_optimal_pH_microbes,
    )

    clay_saturation_factors = calculate_clay_impact_on_enzyme_saturation(
        clay_fraction=dummy_carbon_data["clay_fraction"].to_numpy(),
        base_protection=soil_constants.base_soil_protection,
        protection_with_clay=soil_constants.soil_protection_with_clay,
    )

    return EnvironmentalEffectFactors(
        water=water_factors, pH=pH_factors, clay_saturation=clay_saturation_factors
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
def microbial_changes(
    dummy_carbon_data, fixture_core_components, soil_pool_data, environmental_factors
):
    """Set of microbial changes based on dummy carbon data."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_microbial_changes

    return calculate_microbial_changes(
        pools=soil_pool_data,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        constants=SoilConsts,
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
def functional_groups(fixture_config):
    """Set of functional groups based on the soil model constants."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_microbial_groups,
    )

    return make_full_set_of_microbial_groups(config=fixture_config)


@pytest.fixture
def enzyme_classes(fixture_config):
    """Set of functional groups based on the soil model constants."""
    from virtual_ecosystem.models.soil.microbial_groups import (
        make_full_set_of_enzymes,
    )

    return make_full_set_of_enzymes(config=fixture_config)


@pytest.fixture
def biomass_losses(dummy_carbon_data, functional_groups, fixture_core_components):
    """Rates of biomass loss from each microbial pool."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_maintenance_biomass_synthesis,
    )

    bacterial_biomass_loss = calculate_maintenance_biomass_synthesis(
        microbe_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        microbial_group=functional_groups["bacteria"],
    )

    fungal_biomass_loss = calculate_maintenance_biomass_synthesis(
        microbe_pool_size=dummy_carbon_data["soil_c_pool_fungi"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        microbial_group=functional_groups["fungi"],
    )

    return {"bacteria": bacterial_biomass_loss, "fungi": fungal_biomass_loss}
