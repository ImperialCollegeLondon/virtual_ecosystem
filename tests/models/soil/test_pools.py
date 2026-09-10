"""Test module for soil.pools.py.

This module tests the functionality of the soil carbon module
"""

import numpy as np
import pytest


def test_calculate_all_pool_updates(
    fixture_core_components, fixture_hydrology_constants, soil_pools_fixture
):
    """Test that the two pool update functions work correctly."""

    change_in_pools = {
        "soil_cnp_pool_lmwc_carbon": [0.15366916, 0.76762518, 0.26051393, 0.18554575],
        "soil_cnp_pool_maom_carbon": [0.03734787, 0.00340136, 0.05447554, 0.07275546],
        "soil_c_pool_bacteria": [-0.06022178, -0.02270868, -0.11951067, -0.00764474],
        "soil_c_pool_saprotrophic_fungi": [
            -0.00887423,
            -0.08242634,
            -0.02299858,
            -0.03353477,
        ],
        "soil_c_pool_arbuscular_mycorrhiza": [
            -0.0064004,
            -0.01380161,
            -0.03977501,
            -0.06270593,
        ],
        "soil_c_pool_ectomycorrhiza": [-0.005335, -0.0125084, -0.04348192, -0.02711331],
        "soil_cnp_pool_pom_carbon": [-0.00804411, -0.03779772, -0.0296999, -0.00199208],
        "soil_cnp_pool_necromass_carbon": [
            0.0219229,
            0.12325506,
            0.1460333,
            0.03583873,
        ],
        "soil_enzyme_pom_bacteria": [
            -5.43951037e-04,
            -2.27953510e-04,
            -1.19322945e-03,
            -7.21042991e-05,
        ],
        "soil_enzyme_maom_bacteria": [
            -0.00085406,
            -0.00027893,
            -0.00059417,
            -0.0001093,
        ],
        "soil_enzyme_pom_fungi": [
            -6.25004175e-04,
            -1.00853524e-04,
            -1.21044666e-04,
            -8.40801622e-05,
        ],
        "soil_enzyme_maom_fungi": [
            -2.07380175e-04,
            -1.26677524e-04,
            -5.73726662e-05,
            -3.01521622e-05,
        ],
        "soil_cnp_pool_lmwc_nitrogen": [0.00283278, 0.00606888, 0.0064082, 0.02589927],
        "soil_cnp_pool_pom_nitrogen": [
            -1.00607087e-04,
            4.89636674e-05,
            7.95982722e-05,
            4.67440633e-06,
        ],
        "soil_cnp_pool_necromass_nitrogen": [
            0.01006765,
            0.00272941,
            0.01323332,
            0.00132507,
        ],
        "soil_cnp_pool_maom_nitrogen": [0.00099458, 0.01041398, 0.01326356, 0.00772835],
        "soil_n_pool_ammonium": [0.00012935, 0.00627144, -0.00024005, -0.0001277],
        "soil_n_pool_nitrate": [-0.00563891, -0.0057786, -0.00204456, -0.00178871],
        "soil_cnp_pool_lmwc_phosphorus": [
            0.00099424,
            0.00058965,
            0.00026161,
            0.00816612,
        ],
        "soil_cnp_pool_pom_phosphorus": [
            6.75936879e-06,
            -7.30169672e-06,
            -1.32791192e-06,
            1.38770918e-07,
        ],
        "soil_cnp_pool_necromass_phosphorus": [
            0.00306012,
            0.00373769,
            0.00827202,
            0.00164524,
        ],
        "soil_cnp_pool_maom_phosphorus": [
            5.44660113e-04,
            -6.28584725e-05,
            4.52813305e-04,
            3.09131163e-04,
        ],
        "soil_p_pool_primary": [-4.473516e-10, -1.222973e-9, -6.33411e-10, -1.3674e-10],
        "soil_p_pool_secondary": [-5.050797e-7, -2.77311e-6, -7.40324e-7, -2.187697e-7],
        "soil_p_pool_labile": [
            -1.83486608e-05,
            -4.73259240e-04,
            -1.20248620e-04,
            -3.21100538e-05,
        ],
        "cnp_fungal_fruiting_body_production_carbon": [
            9.44491405e-06,
            5.54712673e-04,
            4.66767176e-04,
            3.99101273e-04,
        ],
        "cnp_fungal_fruiting_body_production_nitrogen": [
            7.61426696e-07,
            6.19111888e-05,
            3.21181525e-05,
            2.32742859e-05,
        ],
        "cnp_fungal_fruiting_body_production_phosphorus": [
            1.18845272e-07,
            9.89503562e-06,
            4.93876588e-06,
            3.51270361e-06,
        ],
        "new_amf_n_supply": [
            6.50771197e-07,
            2.01240329e-05,
            3.81308482e-05,
            4.30670470e-05,
        ],
        "new_amf_p_supply": [
            9.76156795e-08,
            3.01860493e-06,
            5.71962723e-06,
            6.46005705e-06,
        ],
        "new_emf_n_supply": [
            4.66997299e-07,
            1.79338346e-05,
            2.59375488e-05,
            1.78245904e-05,
        ],
        "new_emf_p_supply": [
            7.05836452e-08,
            2.71058402e-06,
            3.92029406e-06,
            2.69407247e-06,
        ],
    }

    # Make order of pools object
    pool_order = {}
    for pool in change_in_pools.keys():
        pool_order[pool] = np.array([])

    delta_pools = soil_pools_fixture.calculate_all_pool_updates(
        delta_pools_ordered=pool_order,
        layer_structure=fixture_core_components.layer_structure,
        soil_moisture_saturation=fixture_hydrology_constants.soil_moisture_saturation,
        soil_moisture_residual=fixture_hydrology_constants.soil_moisture_residual,
        top_soil_layer_thickness=fixture_core_components.layer_structure.soil_layer_thickness[
            0
        ],
    )

    # Check that the updates are correctly calculated. Using a loop here implicitly
    # checks that the output order matches the input order.
    for i, pool in enumerate(change_in_pools.keys()):
        assert np.allclose(delta_pools[i * 4 : (i + 1) * 4], change_in_pools[pool])


def test_combine_direct_biomass_decays(soil_pools_fixture):
    """Test that the SoilPools.combine_direct_biomass_decays method works correctly."""

    from xarray import DataArray

    expected_decay = DataArray(
        data=np.stack(
            [
                [0.00143154, 0.00121389, 0.00068159, 0.036534],
                [0.000240483, 0.000258173, 4.16309e-5, 0.0057801],
                [0.0001910675, 0.000116613, 2.5626e-5, 0.002019229],
            ],
            axis=1,
        ),
        coords={
            "cell_id": soil_pools_fixture.data["cell_id"],
            "element": ["C", "N", "P"],
        },
    )

    assert np.allclose(
        soil_pools_fixture.combine_direct_biomass_decays(), expected_decay
    )


def test_to_per_volume(soil_pools_fixture):
    """Test that the SoilPools.to_per_volume method converts correctly."""

    # Test that it works for both floats and numpy arrays
    assert np.isclose(soil_pools_fixture.to_per_volume(10.0), 40.0)
    assert np.allclose(
        soil_pools_fixture.to_per_volume(np.array([10.0, 25.0, 99.0, 34.7])),
        [40.0, 100.0, 396.0, 138.8],
    )


def test_calculate_microbial_changes(
    fixture_soil_constants,
    averaged_soil_temp,
    soil_pool_data,
    environmental_factors,
    functional_groups,
    enzyme_classes,
    carbon_supply_from_plants,
):
    """Check that calculation of microbe related changes works correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_microbial_changes

    expected_mic_changes = {
        "lmwc_uptake": [
            -2.75392478e-02,
            -6.81640462e-01,
            -6.45117137e-04,
            -3.76380460e-03,
        ],
        "don_uptake": [2.00788176e-05, 1.21247615e-03, 1.69545683e-04, 1.82776752e-04],
        "ammonium_change": [
            -1.02274497e-06,
            -3.65016245e-04,
            4.94890661e-04,
            1.08111782e-04,
        ],
        "nitrate_change": [
            4.04583137e-06,
            -4.42879308e-05,
            7.39492679e-05,
            3.79870390e-05,
        ],
        "dop_uptake": [1.98755031e-06, 5.71593326e-05, 6.14064428e-05, 2.42162700e-05],
        "labile_p_change": [
            3.87689936e-06,
            8.28875086e-05,
            1.05190836e-04,
            2.63788145e-05,
        ],
        "bacteria_change": [-0.05436178, -0.02260998, -0.11852367, -0.00719574],
        "saprotrophic_fungi_change": [
            -0.00832823,
            -0.08227734,
            -0.02286358,
            -0.03267977,
        ],
        "arbuscular_mycorrhiza_change": [
            -0.0060574,
            -0.01337261,
            -0.03917501,
            -0.06247593,
        ],
        "ectomycorrhiza_change": [-0.004383, -0.0121244, -0.04310492, -0.02617031],
        "pom_enzyme_bacteria_change": [
            -5.43951037e-04,
            -2.27953510e-04,
            -1.19322945e-03,
            -7.21042991e-05,
        ],
        "maom_enzyme_bacteria_change": [
            -0.00085406,
            -0.00027893,
            -0.00059417,
            -0.0001093,
        ],
        "pom_enzyme_fungi_change": [
            -6.25004175e-04,
            -1.00853524e-04,
            -1.21044666e-04,
            -8.40801622e-05,
        ],
        "maom_enzyme_fungi_change": [
            -2.07380175e-04,
            -1.26677524e-04,
            -5.73726662e-05,
            -3.01521622e-05,
        ],
        "necromass_generation": [0.07552629, 0.137118, 0.23198355, 0.13287934],
        "necromass_n_flow": [0.01273361, 0.01925831, 0.03189497, 0.01163342],
        "necromass_p_flow": [0.00380658, 0.00384432, 0.00893318, 0.00205757],
        "fruiting_body_production_carbon": [
            9.44491405e-06,
            5.54712673e-04,
            4.66767176e-04,
            3.99101273e-04,
        ],
        "fruiting_body_production_nitrogen": [
            7.61426696e-07,
            6.19111888e-05,
            3.21181525e-05,
            2.32742859e-05,
        ],
        "fruiting_body_production_phosphorus": [
            1.18845272e-07,
            9.89503562e-06,
            4.93876588e-06,
            3.51270361e-06,
        ],
        "arbuscular_mycorrhiza_n_supply": [
            6.50771197e-07,
            2.01240329e-05,
            3.81308482e-05,
            4.30670470e-05,
        ],
        "arbuscular_mycorrhiza_p_supply": [
            9.76156795e-08,
            3.01860493e-06,
            5.71962723e-06,
            6.46005705e-06,
        ],
        "ectomycorrhiza_n_supply": [
            4.66997299e-07,
            1.79338346e-05,
            2.59375488e-05,
            1.78245904e-05,
        ],
        "ectomycorrhiza_p_supply": [
            7.05836452e-08,
            2.71058402e-06,
            3.92029406e-06,
            2.69407247e-06,
        ],
    }

    actual_mic_changes = calculate_microbial_changes(
        pools=soil_pool_data,
        soil_temp=averaged_soil_temp,
        env_factors=environmental_factors,
        constants=fixture_soil_constants,
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
        "bacteria": [0.05443078, 0.02298407, 0.12012258, 0.00722288],
        "saprotrophic_fungi": [0.00835231, 0.0854408, 0.023493, 0.03279189],
        "arbuscular_mycorrhiza": [0.0061, 0.01468982, 0.04167084, 0.06529486],
        "ectomycorrhiza": [0.00441077, 0.01319086, 0.04464733, 0.02723027],
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


def test_calculate_nutrient_removal_by_water(
    dummy_carbon_data, fixture_core_components, fixture_soil_constants
):
    """Check that the calculation of dissolved nutrient removal rates is correct."""
    from virtual_ecosystem.models.soil.pools import calculate_nutrient_removal_by_water

    expected_removal = {
        "lmwc": [1.0747349e-6, 2.5395235e-6, 9.9154571e-5, 5.2557152e-6],
        "don": [1.22826724e-8, 1.81394352e-7, 1.41642304e-7, 3.00326494e-6],
        "dop": [1.2282071e-10, 2.90230964e-9, 5.66596981e-8, 1.20130598e-7],
        "ammonium": [1.496453109e-9, 6.337967958e-7, 2.271304008e-7, 5.461249320e-6],
        "nitrate": [1.041160794e-6, 1.128640314e-5, 6.798727493e-6, 0.00027625126],
        "labile_P": [2.274653e-11, 4.130485e-10, 6.749199e-9, 2.045141e-8],
    }

    actual_removal = calculate_nutrient_removal_by_water(
        soil_c_pool_lmwc=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C"),
        soil_n_pool_don=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N"),
        soil_p_pool_dop=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P"),
        soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        vertical_flow_rates=dummy_carbon_data["vertical_flow"].to_numpy(),
        soil_moisture=dummy_carbon_data["soil_moisture"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        layer_structure=fixture_core_components.layer_structure,
        constants=fixture_soil_constants,
    )

    for attr in dir(actual_removal):
        if not attr.startswith("_"):
            assert attr in expected_removal.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_removal, attr), expected_removal[attr])


def test_negative_nutrient_removal_by_water(
    dummy_carbon_data, fixture_core_components, fixture_soil_constants
):
    """Test that negative rates of nutrient removal by water cannot occur."""
    from virtual_ecosystem.models.soil.pools import calculate_nutrient_removal_by_water

    # Add negative values to the inorganic nutrient pools
    ammonium_data = dummy_carbon_data["soil_n_pool_ammonium"]
    ammonium_data[1] = -6.9619638e-5
    nitrate_data = dummy_carbon_data["soil_n_pool_nitrate"]
    nitrate_data[0] = -0.0024219014
    labile_p_data = dummy_carbon_data["soil_p_pool_labile"]
    labile_p_data[3] = -1.0582393e-5
    lmwc_data = dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C")
    lmwc_data[2] = -2.05924e-5

    expected_removal = {
        "lmwc": [1.0747349e-6, 2.5395235e-6, 0.0, 5.2557152e-6],
        "don": [1.22826724e-8, 1.81394352e-7, 0.0, 3.00326494e-6],
        "dop": [1.2282071e-10, 2.90230964e-9, 0.0, 1.20130598e-7],
        "ammonium": [1.496453109e-9, 0.0, 2.271304008e-7, 5.461249320e-6],
        "nitrate": [0.0, 1.128640314e-5, 6.798727493e-6, 0.00027625126],
        "labile_P": [2.274653e-11, 4.130485e-10, 6.749199e-9, 0.0],
    }

    actual_removal = calculate_nutrient_removal_by_water(
        soil_c_pool_lmwc=lmwc_data,
        soil_n_pool_don=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N"),
        soil_p_pool_dop=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P"),
        soil_n_pool_ammonium=ammonium_data,
        soil_n_pool_nitrate=nitrate_data,
        soil_p_pool_labile=labile_p_data,
        vertical_flow_rates=dummy_carbon_data["vertical_flow"],
        soil_moisture=dummy_carbon_data["soil_moisture"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        layer_structure=fixture_core_components.layer_structure,
        constants=fixture_soil_constants,
    )

    for attr in dir(actual_removal):
        if not attr.startswith("_"):
            assert attr in expected_removal.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_removal, attr), expected_removal[attr])


def test_calculate_enzyme_changes(soil_pool_data, enzyme_production, enzyme_classes):
    """Check that the determination of enzyme pool changes works correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_enzyme_changes

    expected_enzyme_changes = {
        "net_change_pom_bacteria": [
            -5.43951037e-04,
            -2.27953510e-04,
            -1.19322945e-03,
            -7.21042991e-05,
        ],
        "net_change_maom_bacteria": [-0.00085406, -0.00027893, -0.00059417, -0.0001093],
        "net_change_pom_fungi": [
            -6.25004175e-04,
            -1.00853524e-04,
            -1.21044666e-04,
            -8.40801622e-05,
        ],
        "net_change_maom_fungi": [
            -2.07380175e-04,
            -1.26677524e-04,
            -5.73726662e-05,
            -3.01521622e-05,
        ],
        "denaturation_maom_bacteria": [0.0008544, 0.0002808, 0.00060216, 0.00010944],
        "denaturation_pom_bacteria": [
            5.442960e-4,
            2.298240e-4,
            1.201224e-3,
            7.224000e-5,
        ],
        "denaturation_maom_fungi": [2.08056e-4, 1.63824e-4, 9.13680e-5, 5.19120e-5],
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

    expected_net_change = [-5.4395104e-4, -2.2795351e-4, -1.1932295e-3, -7.2104299e-5]
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
        "bacteria_pom": [3.44963254e-7, 1.87049002e-6, 7.99454784e-6, 1.35700856e-7],
        "bacteria_maom": [3.44963254e-7, 1.87049002e-6, 7.99454784e-6, 1.35700856e-7],
        "fungi_pom": [6.75825255e-07, 3.71464758e-05, 3.39953338e-05, 2.17598378e-05],
        "fungi_maom": [6.75825255e-07, 3.71464758e-05, 3.39953338e-05, 2.17598378e-05],
    }

    actual_production = calculate_enzyme_production(
        microbial_groups=functional_groups, growth_rates=growth_rates
    )

    assert expected_production.keys() == actual_production.keys()

    for enzyme in actual_production.keys():
        assert np.allclose(actual_production[enzyme], expected_production[enzyme])


def test_calculate_fruiting_body_production(functional_groups, growth_rates):
    """Test that the calculation of total fruiting body production works as expected."""
    from virtual_ecosystem.models.soil.pools import calculate_fruiting_body_production

    expected_production_carbon = [
        9.44491405e-06,
        5.54712673e-04,
        4.66767176e-04,
        3.99101273e-04,
    ]
    expected_production_nitrogen = [
        7.61426696e-07,
        6.19111888e-05,
        3.21181525e-05,
        2.32742859e-05,
    ]
    expected_production_phosphorus = [
        1.18845272e-07,
        9.89503562e-06,
        4.93876588e-06,
        3.51270361e-06,
    ]

    actual_production = calculate_fruiting_body_production(
        microbial_groups=functional_groups, growth_rates=growth_rates
    )

    assert np.allclose(expected_production_carbon, actual_production["carbon"])
    assert np.allclose(expected_production_nitrogen, actual_production["nitrogen"])
    assert np.allclose(expected_production_phosphorus, actual_production["phosphorus"])


def test_calculate_maintenance_biomass_synthesis(
    dummy_carbon_data, averaged_soil_temp, functional_groups
):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_maintenance_biomass_synthesis,
    )

    expected_loss = [0.05443078, 0.02298407, 0.12012258, 0.00722288]

    actual_loss = calculate_maintenance_biomass_synthesis(
        microbe_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
        soil_temp=averaged_soil_temp,
        microbial_group=functional_groups["bacteria"],
    )

    assert np.allclose(actual_loss, expected_loss)


def test_calculate_maintenance_biomass_synthesis_negative(
    dummy_carbon_data, averaged_soil_temp, functional_groups
):
    """Check maintenance biomass synthesis handles negative populations correctly."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_maintenance_biomass_synthesis,
    )

    # Replace two values with negative biomasses to check that negatives are handled
    microbe_pool_size = dummy_carbon_data["soil_c_pool_bacteria"]
    microbe_pool_size[1] = -0.456
    microbe_pool_size[3] = -1.33e-3

    expected_loss = [0.05443078, 0.0, 0.12012258, 0.0]

    actual_loss = calculate_maintenance_biomass_synthesis(
        microbe_pool_size=microbe_pool_size,
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


def test_calculate_enzyme_turnover_negatives(dummy_carbon_data):
    """Check that enzyme turnover rates handle negative values."""
    from virtual_ecosystem.models.soil.pools import calculate_enzyme_turnover

    expected_decay = [0.000544296, 0.000229824, 0.0, 7.224e-5]

    # Add negative enzyme pool in
    enzyme_pool_sizes = dummy_carbon_data["soil_enzyme_pom_bacteria"]
    enzyme_pool_sizes[2] = -3.4e-2

    actual_decay = calculate_enzyme_turnover(
        enzyme_pool=enzyme_pool_sizes,
        turnover_rate=2.4e-2,
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
        soil_c_pool=dummy_carbon_data["soil_cnp_pool_pom"].sel(element="C"),
        soil_enzyme=dummy_carbon_data["soil_enzyme_pom_bacteria"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        enzyme_class=enzyme_classes["bacteria_pom"],
    )

    assert np.allclose(actual_decomp, expected_decomp)


def test_calculate_enzyme_mediated_decomposition_negatives(
    dummy_carbon_data, fixture_core_components, environmental_factors, enzyme_classes
):
    """Check that particulate organic matter decomposition handles negatives."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_enzyme_mediated_decomposition,
    )

    soil_c_pool = dummy_carbon_data["soil_cnp_pool_pom"].sel(element="C")
    soil_enzyme = dummy_carbon_data["soil_enzyme_pom_bacteria"]
    soil_c_pool[0] = -3.45e-5
    soil_enzyme[3] = -1.23e-3

    expected_decomp = [0.0, 8.91990315e-3, 1.66740158e-2, 0.0]

    actual_decomp = calculate_enzyme_mediated_decomposition(
        soil_c_pool=soil_c_pool,
        soil_enzyme=soil_enzyme,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        enzyme_class=enzyme_classes["bacteria_pom"],
    )

    assert np.allclose(actual_decomp, expected_decomp)


def test_calculate_maom_desorption(dummy_carbon_data, fixture_soil_constants):
    """Check that mineral associated matter desorption is calculated correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_maom_desorption

    expected_desorption = [2.5e-5, 1.7e-5, 4.5e-5, 5.0e-6]

    actual_desorption = calculate_maom_desorption(
        soil_c_pool_maom=dummy_carbon_data["soil_cnp_pool_maom"].sel(element="C"),
        desorption_rate_constant=fixture_soil_constants.maom_desorption_rate,
    )

    assert np.allclose(actual_desorption, expected_desorption)


def test_calculate_maom_desorption_negatives(dummy_carbon_data, fixture_soil_constants):
    """Check that mineral associated matter desorption handles negative values."""

    from virtual_ecosystem.models.soil.pools import calculate_maom_desorption

    soil_c_pool_maom = dummy_carbon_data["soil_cnp_pool_maom"].sel(element="C")
    # Add negative value
    soil_c_pool_maom[3] = -3.33e-3

    expected_desorption = [2.5e-5, 1.7e-5, 4.5e-5, 0.0]

    actual_desorption = calculate_maom_desorption(
        soil_c_pool_maom=soil_c_pool_maom,
        desorption_rate_constant=fixture_soil_constants.maom_desorption_rate,
    )

    assert np.allclose(actual_desorption, expected_desorption)


@pytest.mark.parametrize(
    "pool_name,sorption_rate_constant,expected_sorption",
    [
        (
            "soil_cnp_pool_lmwc",
            "lmwc_sorption_rate",
            [5.0e-5, 2.0e-5, 0.0001, 5.0e-6],
        ),
        (
            "soil_cnp_pool_necromass",
            "necromass_sorption_rate",
            [0.04020253647, 0.01039720771, 0.06446268779, 0.07278045396],
        ),
    ],
)
def test_calculate_sorption_to_maom(
    dummy_carbon_data,
    fixture_soil_constants,
    pool_name,
    sorption_rate_constant,
    expected_sorption,
):
    """Check that sorption to mineral associated matter is calculated correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_sorption_to_maom

    actual_sorption = calculate_sorption_to_maom(
        soil_c_pool=dummy_carbon_data[pool_name].sel(element="C"),
        sorption_rate_constant=getattr(fixture_soil_constants, sorption_rate_constant),
    )

    assert np.allclose(actual_sorption, expected_sorption)


def test_calculate_sorption_to_maom_negative_values(fixture_soil_constants):
    """Check that sorption to mineral associated matter handles negatives correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_sorption_to_maom

    lmwc_values = np.array([0.05, -0.02, 0.1, -0.005])
    expected_sorption = [5.0e-5, 0.0, 0.0001, 0.0]

    actual_sorption = calculate_sorption_to_maom(
        soil_c_pool=lmwc_values,
        sorption_rate_constant=fixture_soil_constants.lmwc_sorption_rate,
    )

    assert np.allclose(actual_sorption, expected_sorption)


def test_calculate_necromass_breakdown(dummy_carbon_data, fixture_soil_constants):
    """Check that necromass breakdown to lmwc is calculated correctly."""

    from virtual_ecosystem.models.soil.pools import calculate_necromass_breakdown

    expected_breakdown = [0.0134008455, 0.0034657359, 0.0214875626, 0.0242601513]

    actual_breakdown = calculate_necromass_breakdown(
        soil_c_pool_necromass=dummy_carbon_data["soil_cnp_pool_necromass"].sel(
            element="C"
        ),
        necromass_decay_rate=fixture_soil_constants.necromass_decay_rate,
    )

    assert np.allclose(actual_breakdown, expected_breakdown)


def test_calculate_necromass_breakdown_negative(
    dummy_carbon_data, fixture_soil_constants
):
    """Check that necromass breakdown to lmwc handles negative values."""

    from virtual_ecosystem.models.soil.pools import calculate_necromass_breakdown

    expected_breakdown = [0.0134008455, 0.0, 0.0214875626, 0.0242601513]

    # Add negative necromass value in
    necromasses = dummy_carbon_data["soil_cnp_pool_necromass"].sel(element="C")
    necromasses[1] = -5.5e-3

    actual_breakdown = calculate_necromass_breakdown(
        soil_c_pool_necromass=necromasses,
        necromass_decay_rate=fixture_soil_constants.necromass_decay_rate,
    )

    assert np.allclose(actual_breakdown, expected_breakdown)


def test_calculate_litter_mineralisation_fluxes(
    dummy_carbon_data, fixture_soil_constants
):
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
        litter_mineralisation_rates=dummy_carbon_data["litter_mineralisation_rate_cnp"],
        constants=fixture_soil_constants,
    )

    # Check all (non-private) dataclass attributes against the dictionary
    for attr in dir(actual_fluxes):
        if not attr.startswith("_"):
            assert attr in expected_fluxes.keys(), f"Attribute {attr} not tested"
            assert np.allclose(getattr(actual_fluxes, attr), expected_fluxes[attr])


def test_calculate_litter_mineralisation_split(
    dummy_carbon_data, fixture_soil_constants
):
    """Test that the calculation of the mineralisation split works as expected."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_litter_mineralisation_split,
    )

    expected_dissolved = [3.18159e-6, 1.590795e-6, 7.35e-7, 8.25e-6]
    expected_particulate = [0.00211787841, 0.001058939205, 0.000489265, 0.00549175]

    actual_particulate, expected_dissolved = calculate_litter_mineralisation_split(
        mineralisation_rate=dummy_carbon_data["litter_mineralisation_rate_cnp"]
        .sel(element="C")
        .to_numpy(),
        litter_leaching_coefficient=fixture_soil_constants.litter_leaching_fraction_carbon,
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
        pool_carbon=dummy_carbon_data["soil_cnp_pool_pom"].sel(element="C"),
        pool_nutrient=dummy_carbon_data["soil_cnp_pool_pom"].sel(element="N"),
        breakdown_rate=enzyme_mediated_rates.pom_to_lmwc,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_calculate_soil_nutrient_mineralisation_negatives(
    dummy_carbon_data, enzyme_mediated_rates
):
    """Test soil nutrient mineralisation calculation handles negative values."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_soil_nutrient_mineralisation,
    )

    pool_carbon = dummy_carbon_data["soil_cnp_pool_pom"].sel(element="C")
    pool_nutrient = dummy_carbon_data["soil_cnp_pool_pom"].sel(element="N")
    # Add negative values in
    pool_carbon[2] = -1.11
    pool_nutrient[1] = -0.99

    expected_rate = [0.00013585646, 0.0, 0.0, 1.15848952e-5]

    actual_rate = calculate_soil_nutrient_mineralisation(
        pool_carbon=pool_carbon,
        pool_nutrient=pool_nutrient,
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

    expected_n_flow_to_necromass = [0.01273361, 0.01925831, 0.03189497, 0.01163342]
    expected_p_flow_to_necromass = [0.00380658, 0.00384432, 0.00893318, 0.00205757]

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
        necromass_carbon=dummy_carbon_data["soil_cnp_pool_necromass"].sel(element="C"),
        necromass_nitrogen=dummy_carbon_data["soil_cnp_pool_necromass"].sel(
            element="N"
        ),
        necromass_phosphorus=dummy_carbon_data["soil_cnp_pool_necromass"].sel(
            element="P"
        ),
        necromass_decay=necromass_breakdown,
        necromass_sorption=necromass_sorption,
    )

    assert set(expected_rates.keys()) == set(actual_rates.keys())

    for key in expected_rates.keys():
        assert np.allclose(expected_rates[key], actual_rates[key])


def test_find_necromass_nutrient_outflows_negatives(
    dummy_carbon_data, necromass_breakdown, necromass_sorption
):
    """Test that function to find necromass nutrient losses handles negative values."""
    from virtual_ecosystem.models.soil.pools import find_necromass_nutrient_outflows

    necromass_carbon = dummy_carbon_data["soil_cnp_pool_necromass"].sel(element="C")
    necromass_nitrogen = dummy_carbon_data["soil_cnp_pool_necromass"].sel(element="N")
    necromass_phosphorus = dummy_carbon_data["soil_cnp_pool_necromass"].sel(element="P")
    # Add negative values in
    necromass_carbon[0] = -0.98
    necromass_nitrogen[3] = -0.33
    necromass_phosphorus[1] = -0.01

    expected_rates = {
        "decay_nitrogen": [0.0, 0.00413222, 0.00466541, 0.0],
        "sorption_nitrogen": [0.0, 0.01239667, 0.01399624, 0.0],
        "decay_phosphorus": [0.0, 0.0, 1.65287877e-4, 1.03082538e-4],
        "sorption_phosphorus": [0.0, 0.0, 4.958636e-4, 3.0924762e-4],
    }

    actual_rates = find_necromass_nutrient_outflows(
        necromass_carbon=necromass_carbon,
        necromass_nitrogen=necromass_nitrogen,
        necromass_phosphorus=necromass_phosphorus,
        necromass_decay=necromass_breakdown,
        necromass_sorption=necromass_sorption,
    )

    assert set(expected_rates.keys()) == set(actual_rates.keys())

    for key in expected_rates.keys():
        assert np.allclose(expected_rates[key], actual_rates[key])


def test_calculate_net_nutrient_transfers_from_maom_to_lmwc(
    dummy_carbon_data, enzyme_mediated_rates, lmwc_sorption, maom_desorption
):
    """Test function to calculate net nutrient exchange between maom and lmwc."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_net_nutrient_transfers_from_maom_to_lmwc,
    )

    expected_transfers = {
        "nitrogen": [0.00100489, 0.00198269, 0.00073268, 2.91129e-6],
        "phosphorus": [1.51879334e-5, 0.00014283379, 4.3050325e-5, 1.16451482e-7],
    }

    actual_transfers = calculate_net_nutrient_transfers_from_maom_to_lmwc(
        lmwc_carbon=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C"),
        lmwc_nitrogen=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N"),
        lmwc_phosphorus=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P"),
        maom_carbon=dummy_carbon_data["soil_cnp_pool_maom"].sel(element="C"),
        maom_nitrogen=dummy_carbon_data["soil_cnp_pool_maom"].sel(element="N"),
        maom_phosphorus=dummy_carbon_data["soil_cnp_pool_maom"].sel(element="P"),
        maom_breakdown=enzyme_mediated_rates.maom_to_lmwc,
        maom_desorption=maom_desorption,
        lmwc_sorption=lmwc_sorption,
    )

    assert set(expected_transfers.keys()) == set(actual_transfers.keys())

    for key in expected_transfers.keys():
        assert np.allclose(expected_transfers[key], actual_transfers[key])


def test_calculate_net_nutrient_transfers_from_maom_to_lmwc_negatives(
    dummy_carbon_data, enzyme_mediated_rates, lmwc_sorption, maom_desorption
):
    """Check net nutrient exchange between maom and lmwc handles negatives."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_net_nutrient_transfers_from_maom_to_lmwc,
    )

    lmwc_carbon = dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C")
    lmwc_nitrogen = dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N")
    lmwc_phosphorus = dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P")
    maom_carbon = dummy_carbon_data["soil_cnp_pool_maom"].sel(element="C")
    maom_nitrogen = dummy_carbon_data["soil_cnp_pool_maom"].sel(element="N")
    maom_phosphorus = dummy_carbon_data["soil_cnp_pool_maom"].sel(element="P")
    # Add negative values
    lmwc_carbon[0] = -1.23
    maom_carbon[0] = -3.45
    lmwc_nitrogen[1] = -2.3
    maom_nitrogen[1] = -4.6
    lmwc_phosphorus[2] = -0.23
    maom_phosphorus[2] = -0.46
    lmwc_nitrogen[3] = -0.99
    maom_phosphorus[3] = -0.11

    expected_transfers = {
        "nitrogen": [0.0, 0.0, 0.00073268, 5.76843536e-6],
        "phosphorus": [0.0, 0.00014283379, 0.0, -1.1428568e-7],
    }

    actual_transfers = calculate_net_nutrient_transfers_from_maom_to_lmwc(
        lmwc_carbon=lmwc_carbon,
        lmwc_nitrogen=lmwc_nitrogen,
        lmwc_phosphorus=lmwc_phosphorus,
        maom_carbon=maom_carbon,
        maom_nitrogen=maom_nitrogen,
        maom_phosphorus=maom_phosphorus,
        maom_breakdown=enzyme_mediated_rates.maom_to_lmwc,
        maom_desorption=maom_desorption,
        lmwc_sorption=lmwc_sorption,
    )

    assert set(expected_transfers.keys()) == set(actual_transfers.keys())

    for key in expected_transfers.keys():
        assert np.allclose(expected_transfers[key], actual_transfers[key])


def test_calculate_rate_of_nitrification(
    dummy_carbon_data,
    fixture_core_components,
    fixture_soil_constants,
    fixture_hydrology_constants,
):
    """Test that calculation of the rate of nitrification is correct."""
    from virtual_ecosystem.models.soil.pools import calculate_rate_of_nitrification

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * fixture_hydrology_constants.soil_moisture_saturation
    )

    expected_rate = [1.83335539e-06, 3.03095957e-04, 1.93106767e-05, 1.71056181e-04]

    actual_rate = calculate_rate_of_nitrification(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        effective_saturation=effective_saturation,
        soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
        constants=fixture_soil_constants,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_negative_nitrification_rate_impossible(
    dummy_carbon_data,
    fixture_core_components,
    fixture_soil_constants,
    fixture_hydrology_constants,
):
    """Test that negative nitrification rates can't occur."""
    from virtual_ecosystem.models.soil.pools import calculate_rate_of_nitrification

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * fixture_hydrology_constants.soil_moisture_saturation
    )
    ammonium_data = dummy_carbon_data["soil_n_pool_ammonium"]
    ammonium_data[0] = -0.0001
    ammonium_data[3] = -3e-4

    expected_rate = [0.0, 3.03095957e-04, 1.93106767e-05, 0.0]

    actual_rate = calculate_rate_of_nitrification(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        effective_saturation=effective_saturation,
        soil_n_pool_ammonium=ammonium_data,
        constants=fixture_soil_constants,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_calculate_rate_of_denitrification(
    dummy_carbon_data,
    fixture_core_components,
    fixture_soil_constants,
    fixture_hydrology_constants,
):
    """Test that calculation of the rate of denitrification is correct."""

    from virtual_ecosystem.models.soil.pools import calculate_rate_of_denitrification

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * fixture_hydrology_constants.soil_moisture_saturation
    )

    expected_rate = [9.01399413e-04, 1.32810083e-03, 4.67630194e-05, 3.02424161e-04]

    actual_rate = calculate_rate_of_denitrification(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        effective_saturation=effective_saturation,
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        constants=fixture_soil_constants,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_negative_denitrification_rate_impossible(
    dummy_carbon_data,
    fixture_core_components,
    fixture_soil_constants,
    fixture_hydrology_constants,
):
    """Test that negative denitrification rates can't occur."""

    from virtual_ecosystem.models.soil.pools import calculate_rate_of_denitrification

    effective_saturation = dummy_carbon_data["soil_moisture"][
        fixture_core_components.layer_structure.index_topsoil_scalar
    ] / (
        fixture_core_components.layer_structure.soil_layer_thickness[0]
        * 1e3
        * fixture_hydrology_constants.soil_moisture_saturation
    )
    nitrate_data = dummy_carbon_data["soil_n_pool_nitrate"]
    nitrate_data[1] = -0.0001
    nitrate_data[2] = -7e-4

    expected_rate = [0.0009014, 0.0, 0.0, 0.00030242]

    actual_rate = calculate_rate_of_denitrification(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        effective_saturation=effective_saturation,
        soil_n_pool_nitrate=nitrate_data,
        constants=fixture_soil_constants,
    )

    assert np.allclose(actual_rate, expected_rate)


def test_calculate_symbiotic_nitrogen_fixation(
    carbon_supply_from_plants, averaged_soil_temp, fixture_soil_constants
):
    """Check calculation of the rate of symbiotic nitrogen fixation is correct."""

    from virtual_ecosystem.models.soil.pools import (
        calculate_symbiotic_nitrogen_fixation,
    )

    expected_fixation = [0.00026199, 0.00606494, 0.00017081, 0.00015635]

    actual_fixation = calculate_symbiotic_nitrogen_fixation(
        carbon_supply=carbon_supply_from_plants.nitrogen_fixers,
        soil_temp=averaged_soil_temp,
        constants=fixture_soil_constants,
    )

    assert np.allclose(actual_fixation, expected_fixation)


def test_calculate_symbiotic_nitrogen_fixation_negative_temps(
    carbon_supply_from_plants, averaged_soil_temp, fixture_soil_constants
):
    """Check symbiotic nitrogen fixation functions handles negative temperatures."""

    from virtual_ecosystem.models.soil.pools import (
        calculate_symbiotic_nitrogen_fixation,
    )

    # Modify some of the soil temps to be below the minimum
    soil_temp = averaged_soil_temp
    soil_temp[1] = -23.3
    soil_temp[3] = -200.0

    expected_fixation = [0.00026199, 0.0, 0.00017081, 0.0]

    actual_fixation = calculate_symbiotic_nitrogen_fixation(
        carbon_supply=carbon_supply_from_plants.nitrogen_fixers,
        soil_temp=soil_temp,
        constants=fixture_soil_constants,
    )

    assert np.allclose(actual_fixation, expected_fixation)


def test_calculate_free_living_nitrogen_fixation(
    dummy_carbon_data,
    fixture_core_components,
    fixture_soil_constants,
    fixture_core_constants,
):
    """Check calculation of the rate of free-living nitrogen fixation is correct."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_free_living_nitrogen_fixation,
    )

    expected_fixation = [8.535774e-5, 0.0001123371, 0.0001478439, 2.845258e-5]

    actual_fixation = calculate_free_living_nitrogen_fixation(
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        fixation_at_reference=fixture_soil_constants.free_living_N_fixation_reference_rate,
        reference_temperature=fixture_soil_constants.free_living_N_fixation_reference_temp,
        q10_nitrogen_fixation=fixture_soil_constants.free_living_N_fixation_q10_coefficent,
        microbial_simulation_depth=fixture_core_constants.microbial_simulation_depth,
    )

    assert np.allclose(actual_fixation, expected_fixation)


def test_calculate_net_formation_of_secondary_P(
    dummy_carbon_data, fixture_soil_constants
):
    """Test that calculation of the net formation of secondary P is correct."""
    from virtual_ecosystem.models.soil.pools import (
        calculate_net_formation_of_secondary_P,
    )

    expected_formation = [-5.05079715e-7, -2.77311435e-6, -7.4032388e-7, -2.18769722e-7]

    actual_formation = calculate_net_formation_of_secondary_P(
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        soil_p_pool_secondary=dummy_carbon_data["soil_p_pool_secondary"],
        secondary_p_breakdown_rate=fixture_soil_constants.secondary_phosphorus_breakdown_rate,
        labile_p_sorption_rate=fixture_soil_constants.labile_phosphorus_sorption_rate,
    )

    assert np.allclose(actual_formation, expected_formation)
