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
            [5.55350203e-5, 2.94754120e-4, 1.21009568e-3, 2.66568228e-5],
            {
                "organic_nitrogen": [
                    1.20269448e-05,
                    9.81292618e-05,
                    8.10622531e-05,
                    2.97057660e-05,
                ],
                "organic_phosphorus": [
                    1.17063748e-06,
                    7.55159888e-06,
                    3.24264901e-05,
                    1.18823064e-06,
                ],
                "carbon": [
                    1.19544043e-04,
                    6.51309245e-04,
                    2.74643627e-03,
                    5.19851062e-05,
                ],
                "inorganic_phosphorus": [
                    2.33501068e-06,
                    1.10547550e-05,
                    4.39607994e-05,
                    4.94481295e-07,
                ],
                "ammonium": [
                    -1.11630161e-06,
                    -3.67910480e-05,
                    1.33974784e-04,
                    -2.20753718e-05,
                ],
                "nitrate": [
                    -1.24033512e-07,
                    -4.08789423e-06,
                    2.00007773e-05,
                    -2.45281909e-06,
                ],
            },
            id="no_external_supply",
        ),
        pytest.param(
            True,
            [2.13058789e-5, 0.00080088219, 0.00174111524, 0.00090997921],
            {
                "carbon": [-0.00694823, -0.17300253, -0.00078973, -0.00128698],
                "organic_nitrogen": [0.0, 0.0, 3.0129333e-5, 0.0],
                "organic_phosphorus": [
                    9.48620026e-8,
                    4.33396110e-6,
                    6.87545767e-6,
                    4.47962952e-6,
                ],
                "ammonium": [
                    4.45402048e-7,
                    6.58564272e-5,
                    1.09579690e-4,
                    6.74509475e-5,
                ],
                "nitrate": [1.46438774e-6, 5.93205097e-6, 1.63588918e-5, 1.41166335e-5],
                "inorganic_phosphorus": [
                    1.89216383e-7,
                    6.34446807e-6,
                    1.63394122e-5,
                    7.65342664e-6,
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
            soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
            soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
            soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
            soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
            soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
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
            soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
            soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
            soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
            soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
            soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
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
        "carbon": [0.01024359, 0.006607655, 0.056746414, 5.198510e-5],
        "ammonium": [3.0678432e-5, 0.003038426, 0.000294822, 9.419319e-5],
        "nitrate": [0.00010086, 0.00027369, 4.40132e-5, 1.97134e-5],
        "inorganic_phosphorus": [2.335011e-6, 1.105475e-5, 4.39608e-5, 2.030086e-6],
        "organic_nitrogen": [0.00011707, 0.00047197, 8.10623e-5, 2.97058e-5],
        "organic_phosphorus": [1.17064e-6, 7.5516e-6, 3.2426e-5, 1.1882e-6],
    }

    actual_max_rates = calculate_maximum_uptake_rates(
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
        "carbon": [1.19544043e-4, 6.51309245e-4, 2.74643627e-3, 5.19851062e-5],
        "organic_nitrogen": [1.20269448e-5, 9.81292618e-5, 8.10622531e-5, 2.9705766e-5],
        "organic_phosphorus": [1.1706375e-6, 7.5515989e-6, 3.2426490e-5, 1.1882306e-6],
        "ammonium": [-1.116302e-6, -3.6791048e-5, 1.3397478e-4, -2.207537e-5],
        "nitrate": [-1.24033512e-7, -4.08789423e-6, 2.00007773e-5, -2.45281909e-6],
        "inorganic_phosphorus": [2.3350107e-6, 1.1054755e-5, 4.3960799e-5, 4.944813e-7],
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
        "carbon": [-0.006361186511710, -0.171519566205653, 0.0, -0.002758694701697],
        "organic_nitrogen": [0.0, 0.0, 0.0, 0.0],
        "organic_phosphorus": [1.17063748e-6, 7.55159888e-6, 0.0, 1.18823064e-6],
        "ammonium": [5.496450823e-6, 0.000114749835, 0.000159839234, 1.789149801e-5],
        "nitrate": [1.807116782e-5, 1.033614942e-5, 2.386201976e-5, 3.744465115e-6],
        "inorganic_phosphorus": [2.335011e-6, 1.105476e-5, 2.732529e-5, 2.030087e-6],
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
            [5.60903705e-5, 2.97701662e-4, 1.22219663e-3, 2.69233910e-05],
            False,
            id="free_living",
        ),
        pytest.param(
            "ectomycorrhiza",
            [0.00029973291768, 0.00159084325674, 0.0023363121075, 0.00027516612744],
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

    expected_uptake = [0.01024359, 0.006607655, 0.056746414, 5.198510e-5]

    actual_uptake = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=dummy_carbon_data["soil_c_pool_lmwc"],
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

    labile_carbon_data = dummy_carbon_data["soil_c_pool_lmwc"]
    labile_carbon_data[1] = -0.0001
    labile_carbon_data[3] = -3.7e-5

    expected_uptake = [0.01024359, 0.0, 0.056746414, 0.0]

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
