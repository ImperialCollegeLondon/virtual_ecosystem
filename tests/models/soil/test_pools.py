"""Test module for soil.pools.py.

This module tests the functionality of the soil carbon module
"""

import numpy as np
import pytest

from virtual_ecosystem.models.soil.constants import SoilConsts


def test_calculate_all_pool_updates(dummy_carbon_data, fixture_core_components):
    """Test that the two pool update functions work correctly."""
    from virtual_ecosystem.core.constants import CoreConsts
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
    soil_pools = SoilPools(
        data=dummy_carbon_data,
        pools=pools,
        constants=SoilConsts,
        max_depth_of_microbial_activity=CoreConsts.max_depth_of_microbial_activity,
    )

    change_in_pools = {
        "soil_c_pool_lmwc": [0.01498062, 0.01332954, 0.03697927, 0.02425546],
        "soil_c_pool_maom": [0.038767651, 0.00829848, 0.05982197, 0.07277182],
        "soil_c_pool_microbe": [-0.05435984, -0.02260329, -0.11965575, -0.00719517],
        "soil_c_pool_pom": [0.00177803841, -0.007860960795, -0.012016245, 0.00545032],
        "soil_c_pool_necromass": [0.001137474, 0.009172067, 0.033573266, -0.08978050],
        "soil_enzyme_pom": [1.18e-8, 1.67e-8, 1.8e-9, -1.12e-8],
        "soil_enzyme_maom": [-0.00031009, -5.09593e-5, 0.0005990658, -3.72112e-5],
        "soil_n_pool_don": [0.00119058, 0.00466305, 0.00497108, 0.00257023],
        "soil_n_pool_particulate": [1.102338e-5, 6.422491e-5, 0.000131687, 1.461799e-5],
        "soil_n_pool_necromass": [0.00786114, -0.01209909, 0.00432363, -0.00891218],
        "soil_n_pool_maom": [0.00148604, 0.01179891, 0.01365197, 0.0077315],
        "soil_n_pool_ammonium": [-1.496453e-9, -6.33797e-7, -2.271304e-7, -5.461249e-6],
        "soil_n_pool_nitrate": [-1.04116e-6, -1.12864e-5, -6.7987275e-6, -0.000276251],
        "soil_p_pool_dop": [1.94452573e-4, 7.10041449e-5, 1.86586343e-4, 1.01700974e-4],
        "soil_p_pool_particulate": [7.22218e-6, -1.13464e-6, 7.86083e-7, 5.85634364e-7],
        "soil_p_pool_necromass": [2.674836e-3, 1.333056e-3, 6.8090685e-3, 4.1429847e-5],
        "soil_p_pool_maom": [5.52086672e-4, 3.68566732e-5, 4.7566130e-4, 3.09257058e-4],
        "soil_p_pool_primary": [-4.473516e-10, -1.222973e-9, -6.33411e-10, -1.3674e-10],
        "soil_p_pool_secondary": [-5.050797e-7, -2.77311e-6, -7.40324e-7, -2.187697e-7],
        "soil_p_pool_labile": [-3.851076e-6, -1.965147e-5, -2.749871e-5, -1.591909e-7],
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

    expected_mic_changes = {
        "lmwc_uptake": [1.97060348e-4, 1.15388472e-3, 1.55610000e-3, 5.77363558e-5],
        "don_uptake": [1.36426394e-5, 7.32272994e-5, 8.9775e-5, 5.32950977e-6],
        "dop_uptake": [2.25200566e-8, 1.3187241e-6, 8.8919911e-7, 1.3196877e-6],
        "labile_p_change": [4.4113378e-6, 2.2480148e-5, 2.8287676e-5, 4.124029e-7],
        "microbe_change": [-0.05435984, -0.02260329, -0.11965575, -0.00719517],
        "pom_enzyme_change": [1.17571917e-8, 1.6744223e-8, 1.8331136e-9, -1.1167587e-8],
        "maom_enzyme_change": [-3.1009224e-4, -5.0959256e-5, 5.990658e-4, -3.721117e-5],
        "necromass_generation": [0.05474086, 0.02303502, 0.11952352, 0.00726011],
    }

    actual_mic_changes = calculate_microbial_changes(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
        soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        soil_enzyme_pom=dummy_carbon_data["soil_enzyme_pom"],
        soil_enzyme_maom=dummy_carbon_data["soil_enzyme_maom"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        constants=SoilConsts,
    )

    for attr in dir(actual_mic_changes):
        if not attr.startswith("_"):
            assert attr in expected_mic_changes.keys(), f"Attribute {attr} not tested"
            assert np.allclose(
                getattr(actual_mic_changes, attr), expected_mic_changes[attr]
            )


def test_calculate_enzyme_mediated_rates(
    dummy_carbon_data, environmental_factors, fixture_core_components
):
    """Check that calculation of enzyme mediated rates works as expected."""

    from virtual_ecosystem.models.soil.pools import calculate_enzyme_mediated_rates

    expected_rates = {
        "pom_to_lmwc": [3.39844565e-4, 8.91990315e-3, 1.25055119e-2, 4.14247999e-5],
        "maom_to_lmwc": [1.45988485e-3, 2.10172756e-3, 4.69571604e-3, 8.62951373e-6],
    }

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

    for attr in dir(actual_rates):
        if not attr.startswith("_"):
            assert attr in expected_rates.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_rates, attr), expected_rates[attr])


def test_calculate_nutrient_leaching(dummy_carbon_data, fixture_core_components):
    """Check that the calculation of dissolved nutrient leaching rates is correct."""
    from virtual_ecosystem.models.soil.pools import calculate_nutrient_leaching

    expected_leaching = {
        "lmwc": [1.0747349e-6, 2.5395235e-6, 9.9154571e-5, 5.2557152e-6],
        "don": [1.22826724e-8, 1.81394352e-7, 1.41642304e-7, 3.00326494e-6],
        "dop": [1.2282071e-10, 2.90230964e-9, 5.66596981e-8, 1.20130598e-7],
        "ammonium": [1.496453109e-9, 6.337967958e-7, 2.271304008e-7, 5.461249320e-6],
        "nitrate": [1.041160794e-6, 1.128640314e-5, 6.798727493e-6, 0.00027625126],
        "labile_P": [2.274653e-11, 4.130485e-10, 6.749199e-9, 2.045141e-8],
    }

    actual_leaching = calculate_nutrient_leaching(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
        soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
        soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        vertical_flow_rate=dummy_carbon_data["vertical_flow"].to_numpy(),
        soil_moisture=dummy_carbon_data["soil_moisture"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        constants=SoilConsts,
    )

    for attr in dir(actual_leaching):
        if not attr.startswith("_"):
            assert attr in expected_leaching.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_leaching, attr), expected_leaching[attr])


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

    expected_carbon_gain = [7.09417251e-5, 3.80781957e-4, 0.00046683, 2.77134508e-5]
    expected_consumption_rates = {
        "organic_nitrogen": [1.36426394e-5, 7.32272994e-5, 8.9775e-5, 5.32950977e-6],
        "organic_phosphorus": [2.25200566e-8, 1.3187241e-6, 8.8919911e-7, 1.3196877e-6],
        "carbon": [1.97060348e-4, 1.15388472e-3, 1.55610000e-3, 5.77363558e-5],
        "inorganic_phosphorus": [4.4113378e-6, 2.2480148e-5, 2.8287676e-5, 4.124029e-7],
    }

    actual_carbon_gain, actual_consumption_rates = calculate_nutrient_uptake_rates(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
        soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        constants=SoilConsts,
    )

    assert np.allclose(actual_carbon_gain, expected_carbon_gain)

    for attr in dir(actual_consumption_rates):
        if not attr.startswith("_"):
            assert attr in expected_consumption_rates.keys(), (
                f"Attribute {attr} not tested"
            )
            assert np.allclose(
                getattr(actual_consumption_rates, attr),
                expected_consumption_rates[attr],
            )


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


def test_calculate_litter_mineralisation_fluxes(dummy_carbon_data):
    """Test that calculation of litter mineralisation fluxes works correctly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_litter_mineralisation_fluxes,
    )

    expected_fluxes = {
        "lmwc": [3.181590e-6, 1.590795e-6, 7.350000e-7, 8.250000e-6],
        "pom": [0.00211788, 0.00105894, 0.00048927, 0.00549175],
        "don": [5.302650e-8, 1.060530e-7, 2.745000e-7, 2.449995e-8],
        "ammonium": [0.0, 0.0, 0.0, 0.0],
        "particulate_n": [3.52979735e-5, 7.05959470e-5, 1.82725500e-4, 1.63088001e-5],
        "dop": [7.32000e-10, 1.41404e-10, 2.82808e-10, 6.53332e-11],
        "particulate_p": [7.31926800e-6, 1.41389860e-6, 2.82779719e-6, 6.53266667e-7],
        "labile_p": [0.0, 0.0, 0.0, 0.0],
    }

    actual_fluxes = calculate_litter_mineralisation_fluxes(
        litter_C_mineralisation_rate=dummy_carbon_data[
            "litter_C_mineralisation_rate"
        ].to_numpy(),
        litter_N_mineralisation_rate=dummy_carbon_data[
            "litter_N_mineralisation_rate"
        ].to_numpy(),
        litter_P_mineralisation_rate=dummy_carbon_data[
            "litter_P_mineralisation_rate"
        ].to_numpy(),
        constants=SoilConsts,
    )

    # Check all (non-private) dataclass attributes against the dictionary
    for attr in dir(actual_fluxes):
        if not attr.startswith("_"):
            assert attr in expected_fluxes.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_fluxes, attr), expected_fluxes[attr])


def test_calculate_litter_mineralisation_split(dummy_carbon_data):
    """Test that the calculation of the mineralisation split works as expected."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_litter_mineralisation_split,
    )

    expected_dissolved = [3.18159e-6, 1.590795e-6, 7.35e-7, 8.25e-6]
    expected_particulate = [0.00211787841, 0.001058939205, 0.000489265, 0.00549175]

    actual_particulate, expected_dissolved = calculate_litter_mineralisation_split(
        mineralisation_rate=dummy_carbon_data["litter_C_mineralisation_rate"],
        litter_leaching_coefficient=SoilConsts.litter_leaching_fraction_carbon,
    )

    assert np.allclose(actual_particulate, expected_particulate)
    assert np.allclose(expected_dissolved, expected_dissolved)


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
    expected_p_flow_to_necromass = [0.0034213, 0.00143969, 0.00747022, 0.00045376]

    actual_n_flow_to_necromass, actual_p_flow_to_necromass = (
        calculate_nutrient_flows_to_necromass(
            microbial_changes=microbial_changes, constants=SoilConsts
        )
    )

    assert np.allclose(actual_n_flow_to_necromass, expected_n_flow_to_necromass)
    assert np.allclose(actual_p_flow_to_necromass, expected_p_flow_to_necromass)


def test_find_necromass_nutrient_outflows(
    dummy_carbon_data, necromass_breakdown, necromass_sorption
):
    """Test that function to find necromass nutrient losses works correctly."""
    from virtual_ecosystem.models.soil.pools import find_necromass_nutrient_outflows

    expected_rates = {
        "decay_nitrogen": [0.00066649, 0.00413222, 0.00466541, 0.00257709],
        "sorption_nitrogen": [0.00199947, 0.01239667, 0.01399624, 0.00773126],
        "decay_phosphorus": [1.86616016e-4, 2.6658441e-5, 1.65287877e-4, 1.03082538e-4],
        "sorption_phosphorus": [5.5984805e-4, 7.9975322e-5, 4.958636e-4, 3.0924762e-4],
    }

    actual_rates = find_necromass_nutrient_outflows(
        necromass_carbon=dummy_carbon_data["soil_c_pool_necromass"],
        necromass_nitrogen=dummy_carbon_data["soil_n_pool_necromass"],
        necromass_phosphorus=dummy_carbon_data["soil_p_pool_necromass"],
        necromass_decay=necromass_breakdown,
        necromass_sorption=necromass_sorption,
    )

    assert set(expected_rates.keys()) == set(actual_rates.keys())

    for key in expected_rates.keys():
        assert np.allclose(expected_rates[key], actual_rates[key])


def test_calculate_net_nutrient_transfers_from_maom_to_lmwc(
    dummy_carbon_data, enzyme_mediated_rates, lmwc_sorption, maom_desorption
):
    """Test function to find net exchange of nitrogen between maom and don."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_net_nutrient_transfers_from_maom_to_lmwc,
    )

    expected_transfers = {
        "nitrogen": [5.13427177e-4, 5.97759087e-4, 3.44268148e-4, -2.36081562e-7],
        "phosphorus": [7.76137416e-6, 4.31186485e-5, 2.02023283e-5, -9.44337153e-9],
    }

    actual_transfers = calculate_net_nutrient_transfers_from_maom_to_lmwc(
        lmwc_carbon=dummy_carbon_data["soil_c_pool_lmwc"],
        lmwc_nitrogen=dummy_carbon_data["soil_n_pool_don"],
        lmwc_phosphorus=dummy_carbon_data["soil_p_pool_dop"],
        maom_carbon=dummy_carbon_data["soil_c_pool_maom"],
        maom_nitrogen=dummy_carbon_data["soil_n_pool_maom"],
        maom_phosphorus=dummy_carbon_data["soil_p_pool_maom"],
        maom_breakdown=enzyme_mediated_rates.maom_to_lmwc,
        maom_desorption=maom_desorption,
        lmwc_sorption=lmwc_sorption,
    )

    assert set(expected_transfers.keys()) == set(actual_transfers.keys())

    for key in expected_transfers.keys():
        assert np.allclose(expected_transfers[key], actual_transfers[key])


def test_calculate_net_formation_of_secondary_P(dummy_carbon_data):
    """Test that calculation of the net formation of secondary P is correct."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_net_formation_of_secondary_P,
    )

    expected_formation = [-5.05079715e-7, -2.77311435e-6, -7.4032388e-7, -2.18769722e-7]

    actual_formation = calculate_net_formation_of_secondary_P(
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        soil_p_pool_secondary=dummy_carbon_data["soil_p_pool_secondary"],
        secondary_p_breakdown_rate=SoilConsts.secondary_phosphorus_breakdown_rate,
        labile_p_sorption_rate=SoilConsts.labile_phosphorus_sorption_rate,
    )

    assert np.allclose(actual_formation, expected_formation)
