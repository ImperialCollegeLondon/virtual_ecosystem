"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

import numpy as np
import pytest

from virtual_rainforest.models.soil.constants import SoilConsts


def test_calculate_soil_carbon_updates(dummy_carbon_data, top_soil_layer_index):
    """Test that the two pool update functions work correctly."""
    from virtual_rainforest.core.constants import CoreConsts
    from virtual_rainforest.models.soil.carbon import calculate_soil_carbon_updates

    change_in_pools = {
        "soil_c_pool_lmwc": [-0.00371115, 0.00278502, -0.01849181, 0.00089995],
        "soil_c_pool_maom": [-1.28996257e-3, 2.35822401e-3, 1.5570399e-3, 1.2082886e-5],
        "soil_c_pool_microbe": [-0.04978105, -0.02020101, -0.10280967, -0.00719517],
        "soil_c_pool_pom": [0.04809165, 0.01023544, 0.07853728, 0.01167564],
        "soil_enzyme_pom": [1.18e-8, 1.67e-8, 1.8e-9, -1.12e-8],
        "soil_enzyme_maom": [-0.00031009, -5.09593e-5, 0.0005990658, -3.72112e-5],
    }

    # Make order of pools object
    pool_order = {}
    for pool in change_in_pools.keys():
        pool_order[pool] = np.array([])

    delta_pools = calculate_soil_carbon_updates(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"].to_numpy(),
        soil_c_pool_maom=dummy_carbon_data["soil_c_pool_maom"].to_numpy(),
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"].to_numpy(),
        soil_c_pool_pom=dummy_carbon_data["soil_c_pool_pom"].to_numpy(),
        soil_enzyme_pom=dummy_carbon_data["soil_enzyme_pom"].to_numpy(),
        soil_enzyme_maom=dummy_carbon_data["soil_enzyme_maom"].to_numpy(),
        pH=dummy_carbon_data["pH"],
        bulk_density=dummy_carbon_data["bulk_density"],
        soil_moisture=dummy_carbon_data["soil_moisture"][
            top_soil_layer_index
        ].to_numpy(),
        soil_water_potential=dummy_carbon_data["matric_potential"][
            top_soil_layer_index
        ].to_numpy(),
        vertical_flow_rate=dummy_carbon_data["vertical_flow"],
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        clay_fraction=dummy_carbon_data["clay_fraction"],
        mineralisation_rate=dummy_carbon_data["litter_C_mineralisation_rate"],
        delta_pools_ordered=pool_order,
        model_constants=SoilConsts,
        core_constants=CoreConsts,
    )

    # Check that the updates are correctly calculated. Using a loop here implicitly
    # checks that the output order matches the input order.
    for i, pool in enumerate(change_in_pools.keys()):
        assert np.allclose(delta_pools[i * 4 : (i + 1) * 4], change_in_pools[pool])


def test_determine_microbial_biomass_losses(
    dummy_carbon_data, top_soil_layer_index, environmental_factors
):
    """Check that the determination of microbial biomass losses works correctly."""
    from virtual_rainforest.models.soil.carbon import determine_microbial_biomass_losses

    expected_maintenance = [0.05443078, 0.02298407, 0.12012258, 0.00722288]
    expected_pom_enzyme = [0.0005443078, 0.0002298407, 0.0012012258, 7.22288e-5]
    expected_maom_enzyme = [0.0005443078, 0.0002298407, 0.0012012258, 7.22288e-5]
    expected_decay_to_pom = [0.04631043, 0.01809481, 0.09055279, 0.00621707]
    expected_decay_to_lmwc = [0.007031729, 0.004429577, 0.027167343, 8.613595e-4]

    losses = determine_microbial_biomass_losses(
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        clay_factor_decay=environmental_factors["clay_decay"],
        constants=SoilConsts,
    )

    # Check that each rate matches expectation
    assert np.allclose(losses.maintenance_synthesis, expected_maintenance)
    assert np.allclose(losses.pom_enzyme_production, expected_pom_enzyme)
    assert np.allclose(losses.maom_enzyme_production, expected_maom_enzyme)
    assert np.allclose(losses.necromass_decay_to_lmwc, expected_decay_to_lmwc)
    assert np.allclose(losses.necromass_decay_to_pom, expected_decay_to_pom)

    # Then check that sum of other rates is the same as the overall
    # maintenance_synthesis rate
    assert np.allclose(
        losses.maintenance_synthesis,
        losses.pom_enzyme_production
        + losses.maom_enzyme_production
        + losses.necromass_decay_to_lmwc
        + losses.necromass_decay_to_pom,
    )


def test_calculate_maintenance_biomass_synthesis(
    dummy_carbon_data, top_soil_layer_index
):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_rainforest.models.soil.carbon import (
        calculate_maintenance_biomass_synthesis,
    )

    expected_loss = [0.05443078, 0.02298407, 0.12012258, 0.00722288]

    actual_loss = calculate_maintenance_biomass_synthesis(
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        constants=SoilConsts,
    )

    assert np.allclose(actual_loss, expected_loss)


def test_calculate_carbon_use_efficiency(dummy_carbon_data, top_soil_layer_index):
    """Check carbon use efficiency calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_carbon_use_efficiency

    expected_cues = [0.36, 0.33, 0.3, 0.48]

    actual_cues = calculate_carbon_use_efficiency(
        dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        SoilConsts.reference_cue,
        SoilConsts.cue_reference_temp,
        SoilConsts.cue_with_temperature,
    )

    assert np.allclose(actual_cues, expected_cues)


@pytest.mark.parametrize(
    "turnover,expected_decay",
    [
        (
            2.4e-2,
            [0.000544296, 0.000229824, 0.001201224, 7.224e-5],
        ),
        (
            6.5e-2,
            [0.001474135, 0.00062244, 0.003253315, 0.00019565],
        ),
        (
            2.4e-3,
            [5.44296e-5, 2.29824e-5, 0.0001201224, 7.224e-6],
        ),
    ],
)
def test_calculate_enzyme_turnover(dummy_carbon_data, turnover, expected_decay):
    """Check that enzyme turnover rates are calculated correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_enzyme_turnover

    actual_decay = calculate_enzyme_turnover(
        enzyme_pool=dummy_carbon_data["soil_enzyme_pom"], turnover_rate=turnover
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_microbial_carbon_uptake(
    dummy_carbon_data, top_soil_layer_index, environmental_factors
):
    """Check microbial carbon uptake calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_microbial_carbon_uptake

    expected_uptake = [1.29159055e-2, 8.43352433e-3, 5.77096991e-2, 5.77363558e-5]
    expected_assimilation = [4.64972597e-3, 2.78306303e-3, 1.73129097e-2, 2.77134508e-5]

    actual_uptake, actual_assimilation = calculate_microbial_carbon_uptake(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        water_factor=environmental_factors["water"],
        pH_factor=environmental_factors["pH"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            top_soil_layer_index
        ].to_numpy(),
        constants=SoilConsts,
    )

    assert np.allclose(actual_uptake, expected_uptake)
    assert np.allclose(actual_assimilation, expected_assimilation)


def test_calculate_enzyme_mediated_decomposition(
    dummy_carbon_data, top_soil_layer_index, environmental_factors
):
    """Check that particulate organic matter decomposition is calculated correctly."""
    from virtual_rainforest.models.soil.carbon import (
        calculate_enzyme_mediated_decomposition,
    )

    expected_decomp = [3.39844565e-4, 8.91990315e-3, 1.25055119e-2, 4.14247999e-5]

    actual_decomp = calculate_enzyme_mediated_decomposition(
        soil_c_pool=dummy_carbon_data["soil_c_pool_pom"],
        soil_enzyme=dummy_carbon_data["soil_enzyme_pom"],
        water_factor=environmental_factors["water"],
        pH_factor=environmental_factors["pH"],
        clay_factor_saturation=environmental_factors["clay_saturation"],
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        reference_temp=SoilConsts.arrhenius_reference_temp,
        max_decomp_rate=SoilConsts.max_decomp_rate_pom,
        activation_energy_rate=SoilConsts.activation_energy_pom_decomp_rate,
        half_saturation=SoilConsts.half_sat_pom_decomposition,
        activation_energy_sat=SoilConsts.activation_energy_pom_decomp_saturation,
    )

    assert np.allclose(actual_decomp, expected_decomp)
