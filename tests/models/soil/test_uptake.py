"""Test module for uptake.py."""

import numpy as np
import pytest


@pytest.mark.parametrize(
    argnames=[
        "external_carbon_supply",
        "expected_carbon_gain",
        "expected_consumption_rates",
    ],
    argvalues=[
        pytest.param(
            None,
            [5.553502e-5, 0.000294754, 0.001210096, 2.744012e-5],
            {
                "organic_nitrogen": [
                    1.20166636e-05,
                    9.80362438e-05,
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
                    1.18553131e-04,
                    6.49827224e-04,
                    2.75813479e-03,
                    5.19851062e-05,
                ],
                "inorganic_phosphorus": [
                    2.33501068e-06,
                    1.10547550e-05,
                    4.39607994e-05,
                    5.43927164e-07,
                ],
                "ammonium": [
                    -1.10704847e-06,
                    -3.67073319e-05,
                    1.33974784e-04,
                    -2.19384447e-05,
                ],
                "nitrate": [
                    -1.23005386e-07,
                    -4.07859243e-06,
                    2.00007773e-05,
                    -2.43760497e-06,
                ],
            },
            id="no_external_supply",
        ),
        pytest.param(
            True,
            [3.193781e-5, 0.001200533, 0.0026348, 0.001364071],
            {
                "organic_nitrogen": [
                    1.95987699e-06,
                    7.41565481e-05,
                    3.01293330e-05,
                    1.04608691e-04,
                ],
                "organic_phosphorus": [
                    9.48620026e-08,
                    4.33396110e-06,
                    1.20523238e-05,
                    4.47962952e-06,
                ],
                "carbon": [
                    7.02042081e-05,
                    2.72536234e-03,
                    6.18380045e-03,
                    2.66098202e-03,
                ],
                "inorganic_phosphorus": [
                    1.89216383e-07,
                    6.34446807e-06,
                    1.13835325e-05,
                    7.65342664e-06,
                ],
                "ammonium": [
                    -6.12858691e-08,
                    -2.74049413e-06,
                    1.09579690e-04,
                    -2.14292200e-05,
                ],
                "nitrate": [
                    -6.80954101e-09,
                    -3.04499348e-07,
                    1.63588918e-05,
                    -2.38102444e-06,
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
    external_carbon_supply,
    expected_carbon_gain,
    expected_consumption_rates,
):
    """Check microbial carbon uptake calculates correctly."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.uptake import (
        calculate_nutrient_uptake_rates,
    )

    if external_carbon_supply:
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
            constants=SoilConsts,
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
            external_carbon_supply=external_carbon_supply,
            water_factor=environmental_factors.water,
            pH_factor=environmental_factors.pH,
            soil_temp=averaged_soil_temp,
            constants=SoilConsts,
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


@pytest.mark.parametrize(
    argnames=[
        "external_carbon_supply",
        "expected_consumptions",
    ],
    argvalues=[
        pytest.param(
            None,
            {
                "carbon": [0.00011855313, 0.00064982722, 0.00275813479, 5.19851062e-5],
                "organic_nitrogen": [1.20167e-5, 9.80362e-5, 8.10623e-5, 2.97058e-5],
                "organic_phosphorus": [1.17064e-6, 7.5516e-6, 3.24265e-5, 1.18823e-6],
                "ammonium": [-1.107048e-6, -3.670733e-5, 0.0001339748, -2.193844e-5],
                "nitrate": [-1.230054e-7, -4.078592e-6, 2.0000777e-5, -2.437605e-6],
                "inorganic_phosphorus": [2.3350e-6, 1.1055e-5, 4.3961e-5, 5.4393e-7],
            },
            id="no_external_supply",
        ),
        pytest.param(
            True,
            {
                "carbon": [0.000866347, 0.004748733, 0.016637362, 0.000705839],
                "organic_nitrogen": [2.805418e-5, 0.00013301, 8.106225e-5, 2.317961e-5],
                "organic_phosphorus": [1.1706e-6, 7.5516e-6, 3.2426e-5, 1.1882e-6],
                "ammonium": [-4.237975e-6, -8.191263e-6, 0.0002948214, -1.572666e-6],
                "nitrate": [-4.708861e-7, -9.101403e-7, 4.401319e-5, -1.747406e-7],
                "inorganic_phosphorus": [2.335e-6, 1.10547e-5, 3.06271e-5, 2.03013e-6],
            },
            id="external_supply",
        ),
    ],
)
def test_find_net_nutrient_consumptions(
    external_carbon_supply,
    expected_consumptions,
    carbon_supply_from_plants,
    carbon_use_efficiency,
    functional_groups,
    max_uptake_rates,
):
    """Test that the function to find the net nutrient consumptions works correctly."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain,
        find_net_nutrient_consumptions,
    )

    if external_carbon_supply:
        actual_carbon_gain = calculate_actual_carbon_gain(
            max_uptake_rates=max_uptake_rates,
            external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
            carbon_use_efficiency=carbon_use_efficiency,
            functional_group=functional_groups["ectomycorrhiza"],
        )
        actual_consumptions = find_net_nutrient_consumptions(
            max_uptake_rates=max_uptake_rates,
            actual_carbon_gain=actual_carbon_gain,
            external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
            carbon_use_efficiency=carbon_use_efficiency,
            functional_group=functional_groups["ectomycorrhiza"],
            ammonium_mineralisation_proportion=SoilConsts.ammonium_mineralisation_proportion,
        )
    else:
        actual_carbon_gain = calculate_actual_carbon_gain(
            max_uptake_rates=max_uptake_rates,
            external_carbon_supply=external_carbon_supply,
            carbon_use_efficiency=carbon_use_efficiency,
            functional_group=functional_groups["bacteria"],
        )
        actual_consumptions = find_net_nutrient_consumptions(
            max_uptake_rates=max_uptake_rates,
            actual_carbon_gain=actual_carbon_gain,
            external_carbon_supply=external_carbon_supply,
            carbon_use_efficiency=carbon_use_efficiency,
            functional_group=functional_groups["bacteria"],
            ammonium_mineralisation_proportion=SoilConsts.ammonium_mineralisation_proportion,
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
        "external_carbon_supply",
        "expected_carbon_gain",
    ],
    argvalues=[
        pytest.param(
            None,
            [5.6090416e-5, 0.0002977016, 0.0012221888, 2.7714522e-5],
            id="no_external_supply",
        ),
        pytest.param(
            True,
            [0.0004098915, 0.0021755117, 0.0073724311, 0.0003762919],
            id="external_supply",
        ),
    ],
)
def test_calculate_actual_carbon_gain(
    max_uptake_rates,
    functional_groups,
    carbon_use_efficiency,
    carbon_supply_from_plants,
    external_carbon_supply,
    expected_carbon_gain,
):
    """Check that function to determine the most limiting nutrient works."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain,
    )

    if external_carbon_supply:
        actual_carbon_gain = calculate_actual_carbon_gain(
            max_uptake_rates=max_uptake_rates,
            external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
            carbon_use_efficiency=carbon_use_efficiency,
            functional_group=functional_groups["ectomycorrhiza"],
        )
    else:
        actual_carbon_gain = calculate_actual_carbon_gain(
            max_uptake_rates=max_uptake_rates,
            external_carbon_supply=external_carbon_supply,
            carbon_use_efficiency=carbon_use_efficiency,
            functional_group=functional_groups["bacteria"],
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
