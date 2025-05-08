"""Test module for uptake.py."""

from logging import CRITICAL

import numpy as np
import pytest

from tests.conftest import log_check


@pytest.mark.parametrize(
    argnames=[
        "symbiotic",
        "expected_carbon_gain",
        "expected_consumption_rates",
    ],
    argvalues=[
        pytest.param(
            False,
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
            [-0.00018997, -0.00548659, 0.00256693269, 0.00125276923],
            {
                "organic_nitrogen": [
                    9.48666511e-06,
                    -2.62810472e-04,
                    3.01293330e-05,
                    1.09603625e-04,
                ],
                "organic_phosphorus": [
                    9.48620026e-08,
                    4.33396110e-06,
                    1.20523238e-05,
                    4.47962952e-06,
                ],
                "carbon": [-0.00018997, -0.00548659, 0.00077452, -0.00084614],
                "inorganic_phosphorus": [
                    1.02061074e-07,
                    6.34446807e-06,
                    1.18498714e-05,
                    7.65342664e-06,
                ],
                "ammonium": [2.48601084e-06, 0.0, 1.09579690e-04, -5.03815505e-06],
                "nitrate": [8.17347789e-6, 0.0, 1.63588918e-05, -5.59795005e-07],
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
):
    """Check microbial uptake function calculates correctly."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
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
            nitrogen_exchange=dummy_carbon_data["plant_n_uptake_ecto"],
            phosphorus_exchange=dummy_carbon_data["plant_p_uptake_ecto"],
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
            external_carbon_supply=None,
            nitrogen_exchange=None,
            phosphorus_exchange=None,
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


def test_calculate_nutrient_uptake_rates_errors(
    caplog,
    dummy_carbon_data,
    averaged_soil_temp,
    environmental_factors,
    functional_groups,
    carbon_supply_from_plants,
):
    """Check microbial uptake function returns sensible errors for bad input."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.uptake import (
        calculate_nutrient_uptake_rates,
    )

    expected_log = (
        (
            CRITICAL,
            "External carbon supply is provided, but nitrogen and phosphorus exchange "
            "demands are not!",
        ),
    )

    with pytest.raises(ValueError):
        _, _ = calculate_nutrient_uptake_rates(
            soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
            soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"],
            soil_n_pool_ammonium=dummy_carbon_data["soil_n_pool_ammonium"],
            soil_n_pool_nitrate=dummy_carbon_data["soil_n_pool_nitrate"],
            soil_p_pool_dop=dummy_carbon_data["soil_p_pool_dop"],
            soil_p_pool_labile=dummy_carbon_data["soil_p_pool_labile"],
            microbial_pool_size=dummy_carbon_data["soil_c_pool_ectomycorrhiza"],
            external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
            nitrogen_exchange=None,
            phosphorus_exchange=None,
            water_factor=environmental_factors.water,
            pH_factor=environmental_factors.pH,
            soil_temp=averaged_soil_temp,
            constants=SoilConsts,
            functional_group=functional_groups["ectomycorrhiza"],
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log)


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
    carbon_use_efficiency,
    functional_groups,
    max_uptake_rates,
):
    """Test that the function to find the net nutrient consumptions works correctly."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain_free_living,
        find_net_nutrient_consumptions_free_living,
    )

    expected_consumptions = {
        "carbon": [0.00011855313, 0.00064982722, 0.00275813479, 5.19851062e-5],
        "organic_nitrogen": [1.20167e-5, 9.80362e-5, 8.10623e-5, 2.97058e-5],
        "organic_phosphorus": [1.17064e-6, 7.5516e-6, 3.24265e-5, 1.18823e-6],
        "ammonium": [-1.107048e-6, -3.670733e-5, 0.0001339748, -2.193844e-5],
        "nitrate": [-1.230054e-7, -4.078592e-6, 2.0000777e-5, -2.437605e-6],
        "inorganic_phosphorus": [2.3350e-6, 1.1055e-5, 4.3961e-5, 5.4393e-7],
    }

    actual_carbon_gain = calculate_actual_carbon_gain_free_living(
        max_uptake_rates=max_uptake_rates,
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups["bacteria"],
    )
    actual_consumptions = find_net_nutrient_consumptions_free_living(
        max_uptake_rates=max_uptake_rates,
        actual_carbon_gain=actual_carbon_gain,
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


def test_find_net_nutrient_consumptions_symbiotic(
    dummy_carbon_data,
    carbon_supply_from_plants,
    carbon_use_efficiency,
    functional_groups,
    max_uptake_rates,
):
    """Test that the function to find the net nutrient consumptions works correctly."""
    from virtual_ecosystem.models.soil.constants import SoilConsts
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain_symbiotic,
        find_net_nutrient_consumptions_symbiotic,
    )

    expected_consumptions = {
        "carbon": [-0.006573537, -0.00453524, 0.01122808, -0.00280130],
        "organic_nitrogen": [4.4043556e-5, -2.0995764e-4, 8.1062253e-5, 2.9705766e-5],
        "organic_phosphorus": [1.1706375e-6, 7.5515989e-6, 3.2426490e-5, 1.1882306e-6],
        "ammonium": [-1.66665186e-6, 0.0, 2.94821547e-4, 1.23489350e-5],
        "nitrate": [-1.85183540e-7, 0.0, 4.40132088e-5, 2.58447651e-6],
        "inorganic_phosphorus": [2.33501e-6, 1.10548e-5, 3.10935e-5, 2.03009e-6],
    }

    actual_carbon_gain = calculate_actual_carbon_gain_symbiotic(
        max_uptake_rates=max_uptake_rates,
        external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
        carbon_use_efficiency=carbon_use_efficiency,
        nitrogen_exchange=dummy_carbon_data["plant_n_uptake_ecto"],
        phosphorus_exchange=dummy_carbon_data["plant_p_uptake_ecto"],
        functional_group=functional_groups["ectomycorrhiza"],
    )
    actual_consumptions = find_net_nutrient_consumptions_symbiotic(
        max_uptake_rates=max_uptake_rates,
        actual_carbon_gain=actual_carbon_gain,
        external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
        nitrogen_exchange=dummy_carbon_data["plant_n_uptake_ecto"],
        phosphorus_exchange=dummy_carbon_data["plant_p_uptake_ecto"],
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups["ectomycorrhiza"],
        ammonium_mineralisation_proportion=SoilConsts.ammonium_mineralisation_proportion,
    )

    for attr in dir(actual_consumptions):
        if not attr.startswith("_"):
            assert attr in expected_consumptions.keys(), f"Attribute {attr} not tested"
            assert np.allclose(
                getattr(actual_consumptions, attr),
                expected_consumptions[attr],
            )


def test_calculate_actual_carbon_gain_free_living(
    max_uptake_rates, functional_groups, carbon_use_efficiency
):
    """Check that function to determine the most limiting nutrient works."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain_free_living,
    )

    expected_carbon_gain = [5.6090416e-5, 0.0002977016, 0.0012221888, 2.7714522e-5]

    actual_carbon_gain = calculate_actual_carbon_gain_free_living(
        max_uptake_rates=max_uptake_rates,
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups["bacteria"],
    )

    assert np.allclose(actual_carbon_gain, expected_carbon_gain)


def test_calculate_actual_carbon_gain_symbiotic(
    dummy_carbon_data,
    max_uptake_rates,
    functional_groups,
    carbon_use_efficiency,
    carbon_supply_from_plants,
):
    """Check that function to determine the most limiting nutrient works."""
    from virtual_ecosystem.models.soil.uptake import (
        calculate_actual_carbon_gain_symbiotic,
    )

    expected_carbon_gain = [0.00020176809, -0.0045352375, 0.00730189308, 0.00026054171]

    actual_carbon_gain = calculate_actual_carbon_gain_symbiotic(
        max_uptake_rates=max_uptake_rates,
        external_carbon_supply=carbon_supply_from_plants.ectomycorrhiza,
        nitrogen_exchange=dummy_carbon_data["plant_n_uptake_ecto"],
        phosphorus_exchange=dummy_carbon_data["plant_p_uptake_ecto"],
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_groups["ectomycorrhiza"],
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
