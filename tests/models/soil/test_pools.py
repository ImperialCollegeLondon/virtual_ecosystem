"""Test module for soil.pools.py.

This module tests the functionality of the soil carbon module
"""

import numpy as np
import pytest

from virtual_ecosystem.models.soil.constants import SoilConsts


def test_calculate_all_pool_updates(
    dummy_carbon_data, fixture_core_components, functional_groups, enzyme_classes
):
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
        functional_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        max_depth_of_microbial_activity=CoreConsts.max_depth_of_microbial_activity,
    )

    change_in_pools = {
        "soil_c_pool_lmwc": [0.117290490, 6.96565834e-2, 0.247627966, 3.42642831e-2],
        "soil_c_pool_maom": [3.7894322e-2, 4.8705495e-3, 5.6793727e-2, 7.2757916e-2],
        "soil_c_pool_bacteria": [-4.24905e-2, -1.71527e-2, -8.74104e-2, -6.36844e-3],
        "soil_c_pool_saprotrophic_fungi": [
            -6.507313e-3,
            -6.211968e-2,
            -1.680347e-2,
            -2.891271e-2,
        ],
        "soil_c_pool_arbuscular_mycorrhiza": [
            -6.507313e-3,
            -6.211968e-2,
            -1.680347e-2,
            -2.891271e-2,
        ],
        "soil_c_pool_ectomycorrhiza": [
            -6.507313e-3,
            -6.211968e-2,
            -1.680347e-2,
            -2.891271e-2,
        ],
        "soil_c_pool_pom": [3.73447584e-4, -2.62977207e-2, -2.214249e-2, 5.219897e-3],
        "soil_c_pool_necromass": [-2.296284e-3, 6.9255912e-2, 2.2051989e-2, -6.1268e-2],
        "soil_enzyme_pom_bacteria": [-5.44018e-4, -2.2835e-4, -1.19517e-3, -7.21028e-5],
        "soil_enzyme_maom_bacteria": [-8.54122e-4, -2.79326e-4, -5.9611e-4, -1.0930e-4],
        "soil_enzyme_pom_fungi": [-6.25574e-4, -1.24304e-4, -1.52398e-4, -1.05217e-4],
        "soil_enzyme_maom_fungi": [-2.07949e-4, -1.50128e-4, -8.87255e-5, -5.12891e-5],
        "soil_n_pool_don": [1.60498e-3, 5.24092e-3, 5.31639e-3, 2.42007e-3],
        "soil_n_pool_particulate": [-8.93041e-5, 5.105645e-5, 9.035108e-5, 5.212779e-6],
        "soil_n_pool_necromass": [6.917627e-3, -3.050687e-3, 1.431913e-3, -4.551887e-3],
        "soil_n_pool_maom": [1.183733e-3, 1.082948e-2, 1.343197e-2, 7.72882e-3],
        "soil_n_pool_ammonium": [9.35035e-4, 2.72159e-2, 5.31626e-4, 1.83631e-4],
        "soil_n_pool_nitrate": [-3.053041e-3, -3.922566e-3, -1.050268e-3, -9.197065e-4],
        "soil_p_pool_dop": [1.99425697e-4, 1.39742546e-4, 1.99748943e-4, 9.68009312e-5],
        "soil_p_pool_particulate": [6.820884e-6, -6.40228e-6, -8.6718e-7, 2.094258e-7],
        "soil_p_pool_necromass": [2.184141e-3, 2.644765e-3, 5.429799e-3, 7.286432e-4],
        "soil_p_pool_maom": [5.47518e-4, -3.2943e-5, 4.6272e-4, 3.0915e-4],
        "soil_p_pool_primary": [-4.473516e-10, -1.222973e-9, -6.33411e-10, -1.3674e-10],
        "soil_p_pool_secondary": [-5.050797e-7, -2.77311e-6, -7.40324e-7, -2.187697e-7],
        "soil_p_pool_labile": [-1.54646e-5, -2.773006e-4, -9.46854e-5, -2.062198e-6],
    }

    # Make order of pools object
    pool_order = {}
    for pool in change_in_pools.keys():
        pool_order[pool] = np.array([])

    delta_pools = soil_pools.calculate_all_pool_updates(
        delta_pools_ordered=pool_order,
        layer_structure=fixture_core_components.layer_structure,
        soil_moisture_capacity=CoreConsts.soil_moisture_capacity,
        top_soil_layer_thickness=fixture_core_components.layer_structure.soil_layer_thickness[
            0
        ],
    )

    # Check that the updates are correctly calculated. Using a loop here implicitly
    # checks that the output order matches the input order.
    for i, pool in enumerate(change_in_pools.keys()):
        assert np.allclose(delta_pools[i * 4 : (i + 1) * 4], change_in_pools[pool])


def test_to_per_volume(
    dummy_carbon_data, fixture_core_components, functional_groups, enzyme_classes
):
    """Test that the SoilPools.to_per_volume method converts correctly."""
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
        functional_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        max_depth_of_microbial_activity=CoreConsts.max_depth_of_microbial_activity,
    )

    # Test that it works for both floats and numpy arrays
    assert np.isclose(soil_pools.to_per_volume(10.0), 40.0)
    assert np.allclose(
        soil_pools.to_per_volume(np.array([10.0, 25.0, 99.0, 34.7])),
        [40.0, 100.0, 396.0, 138.8],
    )


def test_calculate_microbial_changes(
    dummy_carbon_data,
    fixture_core_components,
    soil_pool_data,
    environmental_factors,
    functional_groups,
    enzyme_classes,
    carbon_supply_from_plants,
):
    """Check that calculation of microbe related changes works correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_microbial_changes

    expected_mic_changes = {
        "lmwc_uptake": [0.0002678173772, 0.01178568902, 0.00771186303, 0.0003198594108],
        "don_uptake": [3.060766962e-6, 0.0008418340883, 1.10163963e-5, 0.0001827767514],
        "ammonium_change": [3.32661813e-6, -0.0002060563, 0.00035411364, -0.0001422814],
        "nitrate_change": [1.11256765e-5, -2.2895145e-5, 5.29135951e-5, -1.5809046e-5],
        "dop_uptake": [3.060616979e-8, 1.346934537e-5, 4.40677447e-6, 7.31107003e-6],
        "labile_p_change": [4.99284714e-6, 9.79315564e-5, 1.13990898e-4, -2.4335027e-6],
        "bacteria_change": [-0.0543618, -0.0226100, -0.1185237, -0.0071954],
        "fungi_change": [-0.00832584, -0.08196413, -0.02280126, -0.03266732],
        "pom_enzyme_bacteria_change": [-5.4395e-4, -2.2795e-4, -1.19323e-3, -7.2103e-5],
        "maom_enzyme_bacteria_change": [-8.5406e-4, -2.7893e-4, -5.9417e-4, -1.093e-4],
        "pom_enzyme_fungi_change": [-0.00062555, -0.00012062, -0.00015158, -0.00010522],
        "maom_enzyme_fungi_change": [-2.07924e-4, -1.46441e-4, -8.79093e-5, -5.1289e-5],
        "necromass_generation": [0.065015522, 0.109237318, 0.145665372, 0.040354202],
        "necromass_n_flow": [0.01214967, 0.01770938, 0.02709952, 0.00649313],
        "necromass_p_flow": [0.00371899, 0.00361198, 0.00821386, 0.00128653],
    }

    actual_mic_changes = calculate_microbial_changes(
        pools=soil_pool_data,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        constants=SoilConsts,
        microbial_groups=functional_groups,
        enzyme_classes=enzyme_classes,
        carbon_supply=carbon_supply_from_plants,
    )

    for attr in dir(actual_mic_changes):
        if not attr.startswith("_"):
            assert attr in expected_mic_changes.keys(), f"Attribute {attr} not tested"
            assert np.allclose(
                getattr(actual_mic_changes, attr), expected_mic_changes[attr]
            )


def test_calculate_biomass_losses(
    soil_pool_data, functional_groups, averaged_soil_temp
):
    """Check that the calculation of biomass losses works as expected."""
    from virtual_ecosystem.models.soil.pools import calculate_biomass_losses

    expected_losses = {
        "bacteria": [0.04254605, 0.01744744, 0.08862048, 0.00639588],
        "saprotrophic_fungi": [0.00652862, 0.06485897, 0.01733197, 0.02903729],
        "arbuscular_mycorrhiza": [0.00476809, 0.01115119, 0.03074268, 0.05781874],
        "ectomycorrhiza": [0.0034477, 0.01001331, 0.03293859, 0.02411246],
    }

    actual_losses = calculate_biomass_losses(
        pools=soil_pool_data,
        microbial_groups=functional_groups,
        soil_temp=averaged_soil_temp,
    )

    for attr in dir(actual_losses):
        if not attr.startswith("_"):
            assert attr in expected_losses.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_losses, attr), expected_losses[attr])


def test_calculate_enzyme_mediated_rates(
    dummy_carbon_data,
    soil_pool_data,
    environmental_factors,
    fixture_core_components,
    enzyme_classes,
):
    """Check that calculation of enzyme mediated rates works as expected."""

    from virtual_ecosystem.models.soil.pools import calculate_enzyme_mediated_rates

    expected_rates = {
        "pom_to_lmwc": [0.001901992, 0.030246664, 0.0252492, 0.00028383],
        "maom_to_lmwc": [0.00287967, 0.00699885, 0.0100421, 2.49959e-5],
    }

    actual_rates = calculate_enzyme_mediated_rates(
        pools=soil_pool_data,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        enzyme_classes=enzyme_classes,
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


def test_negative_nutrient_leaching(dummy_carbon_data, fixture_core_components):
    """Test that negative leaching rates cannot occur."""
    from virtual_ecosystem.models.soil.pools import calculate_nutrient_leaching

    # Add negative values to the inorganic nutrient pools
    ammonium_data = dummy_carbon_data["soil_n_pool_ammonium"]
    ammonium_data[1] = -6.9619638e-5
    nitrate_data = dummy_carbon_data["soil_n_pool_nitrate"]
    nitrate_data[0] = -0.0024219014
    labile_p_data = dummy_carbon_data["soil_p_pool_labile"]
    labile_p_data[3] = -1.0582393e-5

    expected_ammonium = [1.496453109e-9, 0.0, 2.271304008e-7, 5.461249320e-6]
    expected_nitrate = [0.0, 1.128640314e-5, 6.798727493e-6, 0.00027625126]
    expected_labile_P = [2.274653e-11, 4.130485e-10, 6.749199e-9, 0.0]

    actual_leaching = calculate_nutrient_leaching(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
        soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
        soil_n_pool_ammonium=ammonium_data,
        soil_n_pool_nitrate=nitrate_data,
        soil_p_pool_labile=labile_p_data,
        vertical_flow_rate=dummy_carbon_data["vertical_flow"].to_numpy(),
        soil_moisture=dummy_carbon_data["soil_moisture"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        constants=SoilConsts,
    )

    assert np.allclose(actual_leaching.ammonium, expected_ammonium)
    assert np.allclose(actual_leaching.nitrate, expected_nitrate)
    assert np.allclose(actual_leaching.labile_P, expected_labile_P)


def test_calculate_enzyme_changes(soil_pool_data, enzyme_production, enzyme_classes):
    """Check that the determination of enzyme pool changes works correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_enzyme_changes

    expected_enzyme_changes = {
        "net_change_pom_bacteria": [-0.00054395, -0.00022795, -0.00119323, -7.21028e-5],
        "net_change_maom_bacteria": [-0.00085406, -0.00027893, -0.00059417, -0.0001093],
        "net_change_pom_fungi": [-0.00062555, -0.00012062, -0.00015158, -0.00010522],
        "net_change_maom_fungi": [-0.00020792, -0.00014644, -8.79093e-5, -5.12891e-5],
        "denaturation_maom_bacteria": [0.0008544, 0.0002808, 0.00060216, 0.00010944],
        "denaturation_pom_bacteria": [0.000544296, 0.000229824, 0.001201224, 7.224e-5],
        "denaturation_maom_fungi": [0.000208056, 0.000163824, 9.1368e-5, 5.1912e-5],
        "denaturation_pom_fungi": [0.00062568, 0.000138, 0.00015504, 0.00010584],
    }

    actual_enzyme_changes = calculate_enzyme_changes(
        pools=soil_pool_data,
        enzyme_production=enzyme_production,
        enzyme_classes=enzyme_classes,
    )

    for attr in dir(actual_enzyme_changes):
        if not attr.startswith("_"):
            assert attr in expected_enzyme_changes.keys(), (
                f"Attribute {attr} not tested"
            )
            assert np.allclose(
                getattr(actual_enzyme_changes, attr), expected_enzyme_changes[attr]
            )


def test_calculate_net_enzyme_change(
    dummy_carbon_data, enzyme_production, enzyme_classes
):
    """Check that the determination of net enzyme pool change works correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_net_enzyme_change

    expected_net_change = [-5.4395104e-4, -2.2795351e-4, -1.1932295e-3, -7.2102805e-5]
    expected_denat = [0.000544296, 0.000229824, 0.001201224, 7.224e-5]

    actual_net_change, actual_denat = calculate_net_enzyme_change(
        enzyme_pool_size=dummy_carbon_data["soil_enzyme_pom_bacteria"],
        enzyme_production=enzyme_production["bacteria_pom"],
        enzyme_turnover_rate=enzyme_classes["bacteria_pom"].turnover_rate,
    )

    assert np.allclose(actual_net_change, expected_net_change)
    assert np.allclose(actual_denat, expected_denat)


def test_calculate_enzyme_production(functional_groups, growth_rates):
    """Test that the calculation of total enzyme production works as expected."""
    from virtual_ecosystem.models.soil.pools import calculate_enzyme_production

    expected_production = {
        "bacteria_maom": [3.44963254e-7, 1.870490025e-6, 7.99454785e-6, 1.37195301e-7],
        "bacteria_pom": [3.44963254e-7, 1.870490025e-6, 7.99454785e-6, 1.37195301e-7],
        "fungi_maom": [1.323350415e-7, 1.738335842e-5, 3.4587141e-6, 6.22866665e-7],
        "fungi_pom": [1.323350415e-7, 1.738335842e-5, 3.4587141e-6, 6.22866665e-7],
    }

    actual_production = calculate_enzyme_production(
        microbial_groups=functional_groups, growth_rates=growth_rates
    )

    assert expected_production.keys() == actual_production.keys()

    for enzyme in actual_production.keys():
        assert np.allclose(actual_production[enzyme], expected_production[enzyme])


def test_calculate_maintenance_biomass_synthesis(
    dummy_carbon_data, averaged_soil_temp, functional_groups
):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_maintenance_biomass_synthesis,
    )

    expected_loss = [0.04254605, 0.01744744, 0.08862048, 0.00639588]

    actual_loss = calculate_maintenance_biomass_synthesis(
        microbe_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
        soil_temp=averaged_soil_temp,
        microbial_group=functional_groups["bacteria"],
    )

    assert np.allclose(actual_loss, expected_loss)


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
        enzyme_pool=dummy_carbon_data["soil_enzyme_pom_bacteria"],
        turnover_rate=turnover,
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_enzyme_mediated_decomposition(
    dummy_carbon_data, fixture_core_components, environmental_factors, enzyme_classes
):
    """Check that particulate organic matter decomposition is calculated correctly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_enzyme_mediated_decomposition,
    )

    expected_decomp = [3.39844565e-4, 8.91990315e-3, 1.66740158e-2, 4.14247999e-5]

    actual_decomp = calculate_enzyme_mediated_decomposition(
        soil_c_pool=dummy_carbon_data["soil_c_pool_pom"],
        soil_enzyme=dummy_carbon_data["soil_enzyme_pom_bacteria"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        enzyme_class=enzyme_classes["bacteria_pom"],
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

    expected_rate = [0.00013585646, 2.16036801e-5, 1.030577177e-4, 1.15848952e-5]

    actual_rate = calculate_soil_nutrient_mineralisation(
        pool_carbon=dummy_carbon_data["soil_c_pool_pom"],
        pool_nutrient=dummy_carbon_data["soil_n_pool_particulate"],
        breakdown_rate=enzyme_mediated_rates.pom_to_lmwc,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_calculate_nutrient_flows_to_necromass(
    functional_groups, enzyme_changes, enzyme_classes, biomass_losses
):
    """Test that the function to calculate nutrient flows to necromass works."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_nutrient_flows_to_necromass,
    )

    expected_n_flow_to_necromass = [0.00958358, 0.01347821, 0.02009357, 0.00575646]
    expected_p_flow_to_necromass = [0.00293061, 0.0027514, 0.00609095, 0.00114097]

    actual_n_flow_to_necromass, actual_p_flow_to_necromass = (
        calculate_nutrient_flows_to_necromass(
            biomass_losses=biomass_losses,
            enzyme_changes=enzyme_changes,
            microbial_groups=functional_groups,
            enzyme_classes=enzyme_classes,
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
        "nitrogen": [0.00100489, 0.00198269, 0.00073268, 2.91129e-6],
        "phosphorus": [1.51879334e-5, 0.00014283379, 4.3050325e-5, 1.16451482e-7],
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


def test_calculate_rate_of_nitrification(dummy_carbon_data, fixture_core_components):
    """Test that calculation of the rate of nitrification is correct."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_rate_of_nitrification

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * CoreConsts.soil_moisture_capacity
    )

    expected_rate = [5.71719748e-6, 0.000423915, 1.557907e-5, 0.000114643]

    actual_rate = calculate_rate_of_nitrification(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        effective_saturation=effective_saturation,
        soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
        constants=SoilConsts,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_negative_nitrification_rate_impossible(
    dummy_carbon_data, fixture_core_components
):
    """Test that negative nitrification rates can't occur."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_rate_of_nitrification

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * CoreConsts.soil_moisture_capacity
    )
    ammonium_data = dummy_carbon_data["soil_n_pool_ammonium"]
    ammonium_data[0] = -0.0001
    ammonium_data[3] = -3e-4

    expected_rate = [0.0, 0.000423915, 1.557907e-5, 0.0]

    actual_rate = calculate_rate_of_nitrification(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        effective_saturation=effective_saturation,
        soil_n_pool_ammonium=ammonium_data,
        constants=SoilConsts,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_calculate_rate_of_denitrification(dummy_carbon_data, fixture_core_components):
    """Test that calculation of the rate of denitrification is correct."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_rate_of_denitrification

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * CoreConsts.soil_moisture_capacity
    )

    expected_rate = [2.89449367e-04, 4.26467934e-04, 1.50161251e-05, 9.71117584e-05]

    actual_rate = calculate_rate_of_denitrification(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        effective_saturation=effective_saturation,
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        constants=SoilConsts,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_negative_denitrification_rate_impossible(
    dummy_carbon_data, fixture_core_components
):
    """Test that negative denitrification rates can't occur."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import calculate_rate_of_denitrification

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * CoreConsts.soil_moisture_capacity
    )
    nitrate_data = dummy_carbon_data["soil_n_pool_nitrate"]
    nitrate_data[1] = -0.0001
    nitrate_data[2] = -7e-4

    expected_rate = [2.89449367e-4, 0.0, 0.0, 9.71117584e-5]

    actual_rate = calculate_rate_of_denitrification(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        effective_saturation=effective_saturation,
        soil_n_pool_nitrate=nitrate_data,
        constants=SoilConsts,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_calculate_symbiotic_nitrogen_fixation(
    carbon_supply_from_plants, averaged_soil_temp
):
    """Check calculation of the rate of symbiotic nitrogen fixation is correct."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import (
        calculate_symbiotic_nitrogen_fixation,
    )

    expected_fixation = [0.0003324566937, 0.00823450715, 0.00024225401, 0.00014608985]

    actual_fixation = calculate_symbiotic_nitrogen_fixation(
        carbon_supply=carbon_supply_from_plants.nitrogen_fixers,
        soil_temp=averaged_soil_temp,
        constants=SoilConsts,
    )

    assert np.allclose(actual_fixation, expected_fixation)


def test_calculate_symbiotic_nitrogen_fixation_negative_temps(
    carbon_supply_from_plants, averaged_soil_temp
):
    """Check symbiotic nitrogen fixation functions handles negative temperatures."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import (
        calculate_symbiotic_nitrogen_fixation,
    )

    # Modify some of the soil temps to be below the minimum
    soil_temp = averaged_soil_temp
    soil_temp[1] = -23.3
    soil_temp[3] = -200.0

    expected_fixation = [0.0003324566937, 0.0, 0.00024225401, 0.0]

    actual_fixation = calculate_symbiotic_nitrogen_fixation(
        carbon_supply=carbon_supply_from_plants.nitrogen_fixers,
        soil_temp=soil_temp,
        constants=SoilConsts,
    )

    assert np.allclose(actual_fixation, expected_fixation)


def test_calculate_free_living_nitrogen_fixation(
    dummy_carbon_data, fixture_core_components
):
    """Check calculation of the rate of free-living nitrogen fixation is correct."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.pools import (
        calculate_free_living_nitrogen_fixation,
    )

    expected_fixation = [8.535774e-5, 0.0001123371, 0.0001478439, 2.845258e-5]

    actual_fixation = calculate_free_living_nitrogen_fixation(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        fixation_at_reference=SoilConsts.free_living_N_fixation_reference_rate,
        reference_temperature=SoilConsts.free_living_N_fixation_reference_temp,
        q10_nitrogen_fixation=SoilConsts.free_living_N_fixation_q10_coefficent,
        active_depth=CoreConsts.max_depth_of_microbial_activity,
    )

    assert np.allclose(actual_fixation, expected_fixation)


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
