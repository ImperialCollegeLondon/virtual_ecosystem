"""Test module for soil.pools.py.

This module tests the functionality of the soil carbon module
"""

import numpy as np
import pytest

from virtual_ecosystem.models.soil.constants import SoilConsts


def test_calculate_all_pool_updates(dummy_carbon_data, fixture_core_components):
    """Test that the two pool update functions work correctly."""
    from virtual_ecosystem.models.soil.pools import SoilPools
    from virtual_ecosystem.models.soil.soil_model import SoilModel, make_slices

    # Find and store order of pools (this requires loads of steps because it needs to
    # work with the integrator)
    y0 = np.concatenate(
        [
            dummy_carbon_data[name].to_numpy()
            for name in map(str, dummy_carbon_data.data.keys())
            if name in SoilModel.vars_updated
        ]
    )
    delta_pools_ordered = {
        name: np.array([])
        for name in map(str, dummy_carbon_data.data.keys())
        if name in SoilModel.vars_updated
    }
    no_cells = 4
    slices = make_slices(no_cells, len(delta_pools_ordered))
    pools = {
        str(pool): y0[slc] for slc, pool in zip(slices, delta_pools_ordered.keys())
    }
    soil_pools = SoilPools(data=dummy_carbon_data, pools=pools, constants=SoilConsts)

    change_in_pools = {
        "soil_c_pool_lmwc": [0.0129365, 0.0060499, 0.03697928, 0.02425546],
        "soil_c_pool_maom": [0.038767651, 0.00829848, 0.05982197, 0.07277182],
        "soil_c_pool_microbe": [-0.05362396, -0.02020101, -0.11965575, -0.00719517],
        "soil_c_pool_pom": [0.00177803841, -0.007860960795, -0.012016245, 0.00545032],
        "soil_c_pool_necromass": [0.001137474, 0.009172067, 0.033573266, -0.08978050],
        "soil_enzyme_pom": [1.18e-8, 1.67e-8, 1.8e-9, -1.12e-8],
        "soil_enzyme_maom": [-0.00031009, -5.09593e-5, 0.0005990658, -3.72112e-5],
        "soil_n_pool_don": [0.00104884, 0.00419763, 0.00496839, 0.00251317],
        "soil_n_pool_particulate": [1.102338e-5, 6.422491e-5, 0.000131687, 1.461799e-5],
        "soil_n_pool_necromass": [0.00786114, -0.01209909, 0.00432363, -0.00891218],
        "soil_n_pool_maom": [0.00148604, 0.01179891, 0.01365197, 0.0077315],
    }

    # Make order of pools object
    pool_order = {}
    for pool in change_in_pools.keys():
        pool_order[pool] = np.array([])

    delta_pools = soil_pools.calculate_all_pool_updates(
        delta_pools_ordered=pool_order,
        top_soil_layer_index=fixture_core_components.layer_structure.index_topsoil_scalar,
    )

    # Check that the updates are correctly calculated. Using a loop here implicitly
    # checks that the output order matches the input order.
    for i, pool in enumerate(change_in_pools.keys()):
        assert np.allclose(delta_pools[i * 4 : (i + 1) * 4], change_in_pools[pool])


def test_calculate_microbial_changes(
    dummy_carbon_data, fixture_core_components, environmental_factors
):
    """Check that calculation of microbe related changes works correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_microbial_changes

    expected_lmwc_uptake = [2.241176e-3, 8.433524e-3, 1.556094e-3, 5.7736357e-5]
    expected_don_uptake = [1.5515837e-4, 5.3520443e-4, 8.97746776e-5, 5.3295099e-6]
    expected_microbe = [-0.05362396, -0.02020101, -0.11965575, -0.00719517]
    expected_pom_enzyme = [1.17571917e-8, 1.67442231e-8, 1.83311362e-9, -1.11675865e-8]
    expected_maom_enzyme = [-3.1009224e-4, -5.0959256e-5, 5.9906583e-4, -3.7211168e-5]
    expected_necromass = [0.05474086, 0.02303502, 0.11952352, 0.00726011]

    mic_changes = calculate_microbial_changes(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        soil_enzyme_pom=dummy_carbon_data["soil_enzyme_pom"],
        soil_enzyme_maom=dummy_carbon_data["soil_enzyme_maom"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        constants=SoilConsts,
    )

    # Check that each rate matches expectation
    assert np.allclose(mic_changes.lmwc_uptake, expected_lmwc_uptake)
    assert np.allclose(mic_changes.don_uptake, expected_don_uptake)
    assert np.allclose(mic_changes.microbe_change, expected_microbe)
    assert np.allclose(mic_changes.pom_enzyme_change, expected_pom_enzyme)
    assert np.allclose(mic_changes.maom_enzyme_change, expected_maom_enzyme)
    assert np.allclose(mic_changes.necromass_generation, expected_necromass)


def test_calculate_enzyme_mediated_rates(
    dummy_carbon_data, environmental_factors, fixture_core_components
):
    """Check that calculation of enzyme mediated rates works as expected."""

    from virtual_ecosystem.models.soil.pools import calculate_enzyme_mediated_rates

    expected_pom_to_lmwc = [3.39844565e-4, 8.91990315e-3, 1.25055119e-2, 4.14247999e-5]
    expected_maom_to_lmwc = [1.45988485e-3, 2.10172756e-3, 4.69571604e-3, 8.62951373e-6]

    actual_rates = calculate_enzyme_mediated_rates(
        soil_enzyme_pom=dummy_carbon_data["soil_enzyme_pom"],
        soil_enzyme_maom=dummy_carbon_data["soil_enzyme_maom"],
        soil_c_pool_pom=dummy_carbon_data["soil_c_pool_pom"],
        soil_c_pool_maom=dummy_carbon_data["soil_c_pool_maom"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        constants=SoilConsts,
    )

    assert np.allclose(actual_rates.pom_to_lmwc, expected_pom_to_lmwc)
    assert np.allclose(actual_rates.maom_to_lmwc, expected_maom_to_lmwc)


def test_calculate_enzyme_changes(dummy_carbon_data):
    """Check that the determination of enzyme pool changes works correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_enzyme_changes

    biomass_loss = np.array([0.05443078, 0.02298407, 0.12012258, 0.00722288])

    expected_pom = [1.17571917e-8, 1.67442231e-8, 1.83311362e-9, -1.11675865e-8]
    expected_maom = [-3.10092243e-4, -5.09592558e-5, 5.99065833e-4, -3.72111676e-5]
    expected_denat = [0.0013987, 0.00051062, 0.00180338, 0.00018168]

    actual_pom, actual_maom, actual_denat = calculate_enzyme_changes(
        soil_enzyme_pom=dummy_carbon_data["soil_enzyme_pom"],
        soil_enzyme_maom=dummy_carbon_data["soil_enzyme_maom"],
        biomass_loss=biomass_loss,
        constants=SoilConsts,
    )

    assert np.allclose(actual_pom, expected_pom)
    assert np.allclose(actual_maom, expected_maom)
    assert np.allclose(actual_denat, expected_denat)


def test_calculate_maintenance_biomass_synthesis(
    dummy_carbon_data, fixture_core_components
):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_maintenance_biomass_synthesis,
    )

    expected_loss = [0.05443078, 0.02298407, 0.12012258, 0.00722288]

    actual_loss = calculate_maintenance_biomass_synthesis(
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        constants=SoilConsts,
    )

    assert np.allclose(actual_loss, expected_loss)


def test_calculate_carbon_use_efficiency(dummy_carbon_data, fixture_core_components):
    """Check carbon use efficiency calculates correctly."""
    from virtual_ecosystem.models.soil.pools import calculate_carbon_use_efficiency

    expected_cues = [0.36, 0.33, 0.3, 0.48]

    actual_cues = calculate_carbon_use_efficiency(
        dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
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
    from virtual_ecosystem.models.soil.pools import calculate_enzyme_turnover

    actual_decay = calculate_enzyme_turnover(
        enzyme_pool=dummy_carbon_data["soil_enzyme_pom"], turnover_rate=turnover
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_nutrient_uptake_rates(
    dummy_carbon_data, fixture_core_components, environmental_factors
):
    """Check microbial carbon uptake calculates correctly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_nutrient_uptake_rates,
    )

    expected_carbon_gain = [8.06823526e-4, 2.78306304e-3, 4.66828324e-4, 2.77134516e-5]
    expected_nitrogen_gain = [1.5515837e-4, 5.3520443e-4, 8.97746776e-5, 5.3295099e-6]
    expected_carbon_consumption = [2.241176e-3, 8.433524e-3, 1.556094e-3, 5.7736357e-5]

    actual_carbon_gain, actual_carbon_consumption, actual_nitrogen_gain = (
        calculate_nutrient_uptake_rates(
            soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
            soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
            soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
            water_factor=environmental_factors.water,
            pH_factor=environmental_factors.pH,
            soil_temp=dummy_carbon_data["soil_temperature"][
                fixture_core_components.layer_structure.index_topsoil_scalar
            ].to_numpy(),
            constants=SoilConsts,
        )
    )

    assert np.allclose(actual_carbon_gain, expected_carbon_gain)
    assert np.allclose(actual_nitrogen_gain, expected_nitrogen_gain)
    assert np.allclose(actual_carbon_consumption, expected_carbon_consumption)


def test_calculate_highest_achievable_nutrient_uptake(
    dummy_carbon_data, fixture_core_components, environmental_factors
):
    """Check function to calculate maximum possible uptake rates works as intended."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_highest_achievable_nutrient_uptake,
    )

    expected_uptake = [1.29159055e-2, 8.43352433e-3, 5.77096991e-2, 5.77363558e-5]

    actual_uptake = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        max_uptake_rate=SoilConsts.max_uptake_rate_labile_C,
        half_saturation_constant=SoilConsts.half_sat_labile_C_uptake,
        constants=SoilConsts,
    )

    assert np.allclose(actual_uptake, expected_uptake)


def test_calculate_enzyme_mediated_decomposition(
    dummy_carbon_data, fixture_core_components, environmental_factors
):
    """Check that particulate organic matter decomposition is calculated correctly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_enzyme_mediated_decomposition,
    )

    expected_decomp = [3.39844565e-4, 8.91990315e-3, 1.25055119e-2, 4.14247999e-5]

    actual_decomp = calculate_enzyme_mediated_decomposition(
        soil_c_pool=dummy_carbon_data["soil_c_pool_pom"],
        soil_enzyme=dummy_carbon_data["soil_enzyme_pom"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        reference_temp=SoilConsts.arrhenius_reference_temp,
        max_decomp_rate=SoilConsts.max_decomp_rate_pom,
        activation_energy_rate=SoilConsts.activation_energy_pom_decomp_rate,
        half_saturation=SoilConsts.half_sat_pom_decomposition,
        activation_energy_sat=SoilConsts.activation_energy_pom_decomp_saturation,
    )

    assert np.allclose(actual_decomp, expected_decomp)


def test_calculate_maom_desorption(dummy_carbon_data):
    """Check that mineral associated matter desorption is calculated correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_maom_desorption

    expected_desorption = [2.5e-5, 1.7e-5, 4.5e-5, 5.0e-6]

    actual_desorption = calculate_maom_desorption(
        soil_c_pool_maom=dummy_carbon_data["soil_c_pool_maom"],
        desorption_rate_constant=SoilConsts.maom_desorption_rate,
    )

    assert np.allclose(actual_desorption, expected_desorption)


@pytest.mark.parametrize(
    "pool_name,sorption_rate_constant,expected_sorption",
    [
        (
            "soil_c_pool_lmwc",
            SoilConsts.lmwc_sorption_rate,
            [5.0e-5, 2.0e-5, 0.0001, 5.0e-6],
        ),
        (
            "soil_c_pool_necromass",
            SoilConsts.necromass_sorption_rate,
            [0.04020253647, 0.01039720771, 0.06446268779, 0.07278045396],
        ),
    ],
)
def test_calculate_sorption_to_maom(
    dummy_carbon_data, pool_name, sorption_rate_constant, expected_sorption
):
    """Check that sorption to mineral associated matter is calculated correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_sorption_to_maom

    actual_sorption = calculate_sorption_to_maom(
        soil_c_pool=dummy_carbon_data[pool_name],
        sorption_rate_constant=sorption_rate_constant,
    )

    assert np.allclose(actual_sorption, expected_sorption)


def test_calculate_necromass_breakdown(dummy_carbon_data):
    """Check that necromass breakdown to lmwc is calculated correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_necromass_breakdown

    expected_breakdown = [0.0134008455, 0.0034657359, 0.0214875626, 0.0242601513]

    actual_breakdown = calculate_necromass_breakdown(
        soil_c_pool_necromass=dummy_carbon_data["soil_c_pool_necromass"],
        necromass_decay_rate=SoilConsts.necromass_decay_rate,
    )

    assert np.allclose(actual_breakdown, expected_breakdown)


def test_calculate_litter_mineralisation_split(dummy_carbon_data):
    """Test that the calculation of the mineralisation split works as expected."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_litter_mineralisation_split,
    )

    expected_split = {
        "dissolved": [3.18159e-6, 1.590795e-6, 7.35e-7, 8.25e-6],
        "particulate": [0.00211787841, 0.001058939205, 0.000489265, 0.00549175],
    }

    actual_split = calculate_litter_mineralisation_split(
        mineralisation_rate=dummy_carbon_data["litter_C_mineralisation_rate"],
        litter_leaching_coefficient=SoilConsts.litter_leaching_fraction_carbon,
    )

    assert set(expected_split.keys()) == set(actual_split.keys())

    for key in actual_split.keys():
        assert np.allclose(actual_split[key], expected_split[key])


def test_calculate_soil_nutrient_mineralisation(
    dummy_carbon_data, enzyme_mediated_rates
):
    """Test that function to calculate soil nutrient mineralisation works properly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_soil_nutrient_mineralisation,
    )

    expected_rate = [2.42745875e-5, 6.371041e-6, 5.104285e-5, 1.690808e-6]

    actual_rate = calculate_soil_nutrient_mineralisation(
        pool_carbon=dummy_carbon_data["soil_c_pool_pom"],
        pool_nutrient=dummy_carbon_data["soil_n_pool_particulate"],
        breakdown_rate=enzyme_mediated_rates.pom_to_lmwc,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_calculate_nutrient_flows_to_necromass(microbial_changes):
    """Test that the function to calculate nutrient flows to necromass works."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_nutrient_flows_to_necromass,
    )

    expected_n_flow_to_necromass = [0.01052709, 0.00442981, 0.02298529, 0.00139617]

    actual_n_flow_to_necromass = calculate_nutrient_flows_to_necromass(
        microbial_changes=microbial_changes, constants=SoilConsts
    )

    assert np.allclose(actual_n_flow_to_necromass, expected_n_flow_to_necromass)


def test_find_necromass_nitrogen_outflows(
    dummy_carbon_data, necromass_breakdown, necromass_sorption
):
    """Test that function to find necromass nitrogen losses works correctly."""
    from virtual_ecosystem.models.soil.pools import find_necromass_nitrogen_outflows

    expected_decay = [0.00066649, 0.00413222, 0.00466541, 0.00257709]
    expected_sorption = [0.00199947, 0.01239667, 0.01399624, 0.00773126]

    actual_decay, actual_sorption = find_necromass_nitrogen_outflows(
        necromass_carbon=dummy_carbon_data["soil_c_pool_necromass"],
        necromass_nitrogen=dummy_carbon_data["soil_n_pool_necromass"],
        necromass_decay=necromass_breakdown,
        necromass_sorption=necromass_sorption,
    )

    assert np.allclose(actual_decay, expected_decay)
    assert np.allclose(actual_sorption, expected_sorption)


def test_calculate_net_nitrogen_transfer_from_maom_to_don(
    dummy_carbon_data, enzyme_mediated_rates, lmwc_sorption, maom_desorption
):
    """Test function to find net exchange of nitrogen between maom and don."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_net_nitrogen_transfer_from_maom_to_don,
    )

    expected_transfer = [5.13427177e-4, 5.97759087e-4, 3.44268148e-4, -2.36081562e-7]

    actual_transfer = calculate_net_nitrogen_transfer_from_maom_to_don(
        lmwc_carbon=dummy_carbon_data["soil_c_pool_lmwc"],
        lmwc_nitrogen=dummy_carbon_data["soil_n_pool_don"],
        maom_carbon=dummy_carbon_data["soil_c_pool_maom"],
        maom_nitrogen=dummy_carbon_data["soil_n_pool_maom"],
        maom_breakdown=enzyme_mediated_rates.maom_to_lmwc,
        maom_desorption=maom_desorption,
        lmwc_sorption=lmwc_sorption,
    )

    assert np.allclose(actual_transfer, expected_transfer)
