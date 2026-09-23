"""Test module for uptake.py."""

import numpy as np
import pytest


@pytest.mark.parametrize(
    argnames=[
        "symbiotic",
        "expected_carbon_gain",
        "expected_consumption_rates",
    ],
    argvalues=[
        pytest.param(
            False,
            [6.89926508e-5, 3.74098005e-4, 1.59890957e-3, 2.71401712e-5],
            {
                "organic_nitrogen": [
                    1.53076713e-05,
                    1.39144498e-04,
                    1.09917740e-04,
                    3.29921934e-05,
                ],
                "organic_phosphorus": [
                    1.47602968e-06,
                    9.63830388e-06,
                    4.39692506e-05,
                    1.31968774e-06,
                ],
                "carbon": [
                    1.83540380e-04,
                    1.05843448e-03,
                    4.82169434e-03,
                    5.77363558e-05,
                ],
                "inorganic_phosphorus": [
                    2.87913141e-06,
                    1.39766327e-05,
                    5.69619158e-05,
                    3.93535572e-07,
                ],
                "ammonium": [
                    -1.71645807e-06,
                    -5.98348389e-05,
                    1.74556507e-04,
                    -2.49486634e-05,
                ],
                "nitrate": [
                    -1.90717563e-07,
                    -6.64831544e-06,
                    2.60831875e-05,
                    -2.77207371e-06,
                ],
            },
            id="no_external_supply",
        ),
        pytest.param(
            True,
            [2.77706145e-05, 1.06645929e-03, 1.54241078e-03, 1.05996294e-03],
            {
                "carbon": [-0.00691661, -0.1715943, -0.0, -0.00074486],
                "organic_nitrogen": [0.0, 0.0, 0.0, 0.0],
                "organic_phosphorus": [
                    1.19609301e-07,
                    5.53154831e-06,
                    0.0,
                    4.97522277e-06,
                ],
                "ammonium": [
                    5.37465413e-07,
                    8.22844013e-05,
                    1.12828320e-04,
                    7.33675457e-05,
                ],
                "nitrate": [
                    1.79752108e-06,
                    7.38477175e-06,
                    1.68594243e-05,
                    1.57554064e-05,
                ],
                "inorganic_phosphorus": [
                    2.33308924e-07,
                    8.02137180e-06,
                    1.96014703e-05,
                    8.49513956e-06,
                ],
            },
            id="external_supply",
        ),
    ],
)
def test_calculate_nutrient_uptake_rates(
    dummy_carbon_data,
    averaged_soil_temp,
    environmental_factors,
    functional_groups,
    carbon_supply_from_plants,
    symbiotic,
    expected_carbon_gain,
    expected_consumption_rates,
    fixture_soil_constants,
):
    """Check microbial uptake function calculates correctly."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_nutrient_uptake_rates,
    )

    if symbiotic:
        actual_carbon_gain, actual_consumption_rates = calculate_nutrient_uptake_rates(
            soil_c_pool_lmwc=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C"),
            soil_n_pool_don=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N"),
            soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
            soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
            soil_p_pool_dop=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P"),
            soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
            microbial_pool_size=dummy_carbon_data["soil_c_pool_ectomycorrhiza"],
            external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
            water_factor=environmental_factors.water,
            pH_factor=environmental_factors.pH,
            soil_temp=averaged_soil_temp,
            constants=fixture_soil_constants,
            functional_group=functional_groups["ectomycorrhiza"],
        )
    else:
        actual_carbon_gain, actual_consumption_rates = calculate_nutrient_uptake_rates(
            soil_c_pool_lmwc=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C"),
            soil_n_pool_don=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N"),
            soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
            soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
            soil_p_pool_dop=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P"),
            soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
            microbial_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
            external_carbon_supply=None,
            water_factor=environmental_factors.water,
            pH_factor=environmental_factors.pH,
            soil_temp=averaged_soil_temp,
            constants=fixture_soil_constants,
            functional_group=functional_groups["bacteria"],
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


def test_calculate_maximum_uptake_rates(
    dummy_carbon_data, environmental_factors, averaged_soil_temp, functional_groups
):
    """Test that calculate_maximum_uptake_rates returns the expected values."""
    from virtual_ecosystem.models.soil.uptake import calculate_maximum_uptake_rates

    expected_max_rates = {
        "carbon": [1.29159055e-2, 8.43352433e-3, 7.69462655e-2, 5.77363558e-5],
        "ammonium": [3.78443779e-5, 3.98219645e-3, 3.82514834e-4, 1.06879482e-4],
        "nitrate": [1.26568269e-4, 3.57389874e-4, 5.71574574e-5, 2.29519696e-5],
        "inorganic_phosphorus": [2.8791314e-6, 1.397663e-5, 5.6961916e-5, 2.2533527e-6],
        "organic_nitrogen": [1.47610201e-4, 6.0239399e-4, 1.0991774e-4, 3.29921934e-5],
        "organic_phosphorus": [1.4760297e-6, 9.6383039e-6, 4.3969251e-5, 1.3196877e-6],
    }

    actual_max_rates = calculate_maximum_uptake_rates(
        soil_c_pool_lmwc=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C"),
        soil_n_pool_don=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N"),
        soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        soil_p_pool_dop=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P"),
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        microbial_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        functional_group=functional_groups["bacteria"],
    )

    for attr in dir(actual_max_rates):
        if not attr.startswith("_"):
            assert attr in expected_max_rates.keys(), f"Attribute {attr} not tested"
            assert np.allclose(
                getattr(actual_max_rates, attr),
                expected_max_rates[attr],
            )


def test_calculate_maximum_uptake_rates_negative_values(
    dummy_carbon_data, environmental_factors, averaged_soil_temp, functional_groups
):
    """Test that calculate_maximum_uptake_rates handles negative values sensibly."""
    from virtual_ecosystem.models.soil.uptake import calculate_maximum_uptake_rates

    lmwc_values = dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C").to_numpy()
    don_values = dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="N").to_numpy()
    dop_values = dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="P").to_numpy()
    ammonium_values = dummy_carbon_data["soil_n_pool_ammonium"].to_numpy()
    # Replace values with negatives to check that they are handled correctly
    lmwc_values[0] = -3.3
    don_values[1] = -0.98
    dop_values[2] = -0.77
    ammonium_values[3] = -8.9

    expected_max_rates = {
        "carbon": [0.0, 8.43352433e-3, 7.69462655e-2, 5.77363558e-5],
        "ammonium": [3.78443779e-5, 3.98219645e-3, 3.82514834e-4, 0.0],
        "nitrate": [1.26568269e-4, 3.57389874e-4, 5.71574574e-5, 2.29519696e-5],
        "inorganic_phosphorus": [2.8791314e-6, 1.397663e-5, 5.6961916e-5, 2.2533527e-6],
        "organic_nitrogen": [0.0, 0.0, 1.0991774e-4, 3.29921934e-5],
        "organic_phosphorus": [0.0, 9.6383039e-6, 0.0, 1.3196877e-6],
    }

    actual_max_rates = calculate_maximum_uptake_rates(
        soil_c_pool_lmwc=lmwc_values,
        soil_n_pool_don=don_values,
        soil_n_pool_ammonium=ammonium_values,
        soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
        soil_p_pool_dop=dop_values,
        soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
        microbial_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        functional_group=functional_groups["bacteria"],
    )

    for attr in dir(actual_max_rates):
        if not attr.startswith("_"):
            assert attr in expected_max_rates.keys(), f"Attribute {attr} not tested"
            assert np.allclose(
                getattr(actual_max_rates, attr),
                expected_max_rates[attr],
            )


def test_find_net_nutrient_consumptions_free_living(
    carbon_use_efficiency, functional_groups, max_uptake_rates, fixture_soil_constants
):
    """Test that the function to find the net nutrient consumptions works correctly."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain,
        find_net_nutrient_consumptions_free_living,
    )

    expected_consumptions = {
        "carbon": [1.83540380e-4, 1.05843448e-3, 4.82169434e-3, 5.77363558e-5],
        "organic_nitrogen": [1.53076713e-5, 1.39144498e-4, 1.0991774e-4, 3.29921934e-5],
        "organic_phosphorus": [1.4760297e-6, 9.6383039e-6, 4.3969251e-5, 1.3196877e-6],
        "ammonium": [-1.71645807e-6, -5.98348389e-5, 1.74556507e-4, -2.49486634e-5],
        "nitrate": [-1.90717563e-7, -6.64831544e-6, 2.60831875e-5, -2.77207371e-6],
        "inorganic_phosphorus": [2.8791314e-6, 1.397663e-5, 5.6961916e-5, 3.9353557e-7],
    }

    actual_carbon_gain = calculate_actual_carbon_gain(
        max_uptake_rates=max_uptake_rates,
        external_carbon_supply=None,
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups["bacteria"],
    )
    actual_consumptions = find_net_nutrient_consumptions_free_living(
        max_uptake_rates=max_uptake_rates,
        actual_carbon_gain=actual_carbon_gain,
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups["bacteria"],
        ammonium_mineralisation_proportion=fixture_soil_constants.ammonium_mineralisation_proportion,
    )
    for attr in dir(actual_consumptions):
        if not attr.startswith("_"):
            assert attr in expected_consumptions.keys(), f"Attribute {attr} not tested"
            assert np.allclose(
                getattr(actual_consumptions, attr),
                expected_consumptions[attr],
            )


def test_find_net_nutrient_consumptions_symbiotic(
    carbon_supply_from_plants,
    carbon_use_efficiency,
    functional_groups,
    max_uptake_rates,
):
    """Test that the function to find the net nutrient consumptions works correctly."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain,
        find_net_nutrient_consumptions_symbiotic,
    )

    expected_consumptions = {
        "carbon": [-0.00597097, -0.16906583, -0.0, -0.0026149],
        "organic_nitrogen": [0.0, 0.0, 0.0, 0.0],
        "organic_phosphorus": [1.47602968e-6, 9.63830388e-6, 0.0, 1.31968774e-6],
        "ammonium": [6.63255190e-6, 1.43374336e-4, 1.12828320e-4, 1.94608875e-5],
        "nitrate": [2.21821751e-5, 1.28674053e-5, 1.68594243e-5, 4.17915289e-6],
        "inorganic_phosphorus": [2.8791314e-6, 1.3976633e-5, 1.960147e-5, 2.2533527e-6],
    }

    actual_carbon_gain = calculate_actual_carbon_gain(
        max_uptake_rates=max_uptake_rates,
        external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups["ectomycorrhiza"],
    )
    actual_consumptions = find_net_nutrient_consumptions_symbiotic(
        max_uptake_rates=max_uptake_rates,
        actual_carbon_gain=actual_carbon_gain,
        external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups["ectomycorrhiza"],
    )

    for attr in dir(actual_consumptions):
        if not attr.startswith("_"):
            assert attr in expected_consumptions.keys(), f"Attribute {attr} not tested"
            assert np.allclose(
                getattr(actual_consumptions, attr),
                expected_consumptions[attr],
            )


@pytest.mark.parametrize(
    argnames=[
        "group_name",
        "expected_carbon_gain",
        "symbiotic",
    ],
    argvalues=[
        pytest.param(
            "bacteria",
            [6.96825774e-5, 3.77838985e-4, 1.61489866e-3, 2.74115729e-5],
            False,
            id="free_living",
        ),
        pytest.param(
            "ectomycorrhiza",
            [0.00039068, 0.00211838, 0.00175835, 0.00032052],
            True,
            id="symbiotic",
        ),
    ],
)
def test_calculate_actual_carbon_gain(
    group_name,
    expected_carbon_gain,
    symbiotic,
    max_uptake_rates,
    functional_groups,
    carbon_use_efficiency,
    carbon_supply_from_plants,
):
    """Check that function to determine the most limiting nutrient works."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain,
    )

    if symbiotic:
        external_carbon_supply = carbon_supply_from_plants.ectomycorrhiza
    else:
        external_carbon_supply = None

    actual_carbon_gain = calculate_actual_carbon_gain(
        max_uptake_rates=max_uptake_rates,
        external_carbon_supply=external_carbon_supply,
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups[group_name],
    )

    assert np.allclose(actual_carbon_gain, expected_carbon_gain)


def test_calculate_highest_achievable_nutrient_uptake(
    dummy_carbon_data, environmental_factors, averaged_soil_temp, functional_groups
):
    """Check function to calculate maximum possible uptake rates works as intended."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_highest_achievable_nutrient_uptake,
    )

    expected_uptake = [1.29159055e-2, 8.43352433e-3, 7.69462655e-2, 5.77363558e-5]

    actual_uptake = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C"),
        microbial_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        max_uptake_rate=functional_groups["bacteria"].max_uptake_rate_labile_C,
        activation_energy_uptake=functional_groups[
            "bacteria"
        ].activation_energy_uptake_rate,
        half_saturation_constant=functional_groups["bacteria"].half_sat_labile_C_uptake,
        activation_energy_uptake_saturation=functional_groups[
            "bacteria"
        ].activation_energy_uptake_saturation,
        reference_temperature=functional_groups["bacteria"].reference_temperature,
    )

    assert np.allclose(actual_uptake, expected_uptake)


def test_negative_highest_achievable_nutrient_uptake_are_impossible(
    dummy_carbon_data, environmental_factors, averaged_soil_temp, functional_groups
):
    """Test to check that negative maximum uptake rates cannot be returned."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_highest_achievable_nutrient_uptake,
    )

    labile_carbon_data = dummy_carbon_data["soil_cnp_pool_lmwc"].sel(element="C")
    labile_carbon_data[1] = -0.0001
    labile_carbon_data[3] = -1e3  # Larger than saturation constant

    expected_uptake = [1.29159055e-2, 0.0, 7.69462655e-2, 0.0]

    actual_uptake = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=labile_carbon_data,
        microbial_pool_size=dummy_carbon_data["soil_c_pool_bacteria"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=averaged_soil_temp,
        max_uptake_rate=functional_groups["bacteria"].max_uptake_rate_labile_C,
        activation_energy_uptake=functional_groups[
            "bacteria"
        ].activation_energy_uptake_rate,
        half_saturation_constant=functional_groups["bacteria"].half_sat_labile_C_uptake,
        activation_energy_uptake_saturation=functional_groups[
            "bacteria"
        ].activation_energy_uptake_saturation,
        reference_temperature=functional_groups["bacteria"].reference_temperature,
    )

    assert np.allclose(actual_uptake, expected_uptake)
