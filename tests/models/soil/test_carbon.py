"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_rainforest.models.soil.constants import SoilConsts


@pytest.fixture
def moist_temp_scalars(dummy_carbon_data, top_soil_layer_index):
    """Combined moisture and temperature scalars based on dummy carbon data."""
    from virtual_rainforest.models.soil.carbon import (
        convert_moisture_to_scalar,
        convert_temperature_to_scalar,
    )

    moist_scalars = convert_moisture_to_scalar(
        dummy_carbon_data["soil_moisture"][top_soil_layer_index],
        SoilConsts.moisture_scalar_coefficient,
        SoilConsts.moisture_scalar_exponent,
    )
    temp_scalars = convert_temperature_to_scalar(
        dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        SoilConsts.temp_scalar_coefficient_1,
        SoilConsts.temp_scalar_coefficient_2,
        SoilConsts.temp_scalar_coefficient_3,
        SoilConsts.temp_scalar_coefficient_4,
        SoilConsts.temp_scalar_reference_temp,
    )

    return moist_scalars * temp_scalars


def test_top_soil_data_extraction(dummy_carbon_data, top_soil_layer_index):
    """Test that top soil data can be extracted from the data object correctly."""

    top_soil_temps = [35.0, 37.5, 40.0, 25.0]
    top_soil_moistures = [0.5, 0.7, 0.6, 0.2]

    assert np.allclose(
        dummy_carbon_data["soil_temperature"][top_soil_layer_index], top_soil_temps
    )
    assert np.allclose(
        dummy_carbon_data["soil_moisture"][top_soil_layer_index], top_soil_moistures
    )


def test_calculate_soil_carbon_updates(dummy_carbon_data, top_soil_layer_index):
    """Test that the two pool update functions work correctly."""

    from virtual_rainforest.models.soil.carbon import calculate_soil_carbon_updates

    change_in_pools = {
        "soil_c_pool_lmwc": [0.00509349, 0.02038796, 0.71353723, 0.00125521],
        "soil_c_pool_maom": [0.13088391, 0.05654771, -0.39962841, 0.00533357],
        "soil_c_pool_microbe": [-0.33131188, -0.16636299, -0.76078599, -0.01275669],
        "soil_c_pool_pom": [-0.00168464, -0.00936813, -0.00873008, 0.00403342],
    }

    # Make order of pools object
    pool_order = {}
    for pool in change_in_pools.keys():
        pool_order[pool] = np.array([])

    delta_pools = calculate_soil_carbon_updates(
        dummy_carbon_data["soil_c_pool_lmwc"].to_numpy(),
        dummy_carbon_data["soil_c_pool_maom"].to_numpy(),
        dummy_carbon_data["soil_c_pool_microbe"].to_numpy(),
        dummy_carbon_data["soil_c_pool_pom"].to_numpy(),
        dummy_carbon_data["pH"],
        dummy_carbon_data["bulk_density"],
        dummy_carbon_data["soil_moisture"][top_soil_layer_index],
        dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        dummy_carbon_data["percent_clay"],
        dummy_carbon_data["litter_C_mineralisation_rate"],
        pool_order,
        constants=SoilConsts,
    )

    # Check that the updates are correctly calculated. Using a loop here implicitly
    # checks that the output order matches the input order.
    for i, pool in enumerate(change_in_pools.keys()):
        assert np.allclose(delta_pools[i * 4 : (i + 1) * 4], change_in_pools[pool])


def test_calculate_mineral_association(dummy_carbon_data, moist_temp_scalars):
    """Test that mineral_association runs and generates the correct values."""

    from virtual_rainforest.models.soil.carbon import calculate_mineral_association

    output_l_to_m = [-7.35822655e-03, -1.27716013e-02, -7.16245859e-01, 3.29436494e-05]

    # Then calculate mineral association rate
    lmwc_to_maom = calculate_mineral_association(
        dummy_carbon_data["soil_c_pool_lmwc"],
        dummy_carbon_data["soil_c_pool_maom"],
        dummy_carbon_data["pH"],
        dummy_carbon_data["bulk_density"],
        moist_temp_scalars,
        dummy_carbon_data["percent_clay"],
        constants=SoilConsts,
    )

    # Check that expected values are generated
    assert np.allclose(lmwc_to_maom, output_l_to_m)


def test_calculate_equilibrium_maom(dummy_carbon_data):
    """Test that equilibrium maom calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_equilibrium_maom

    Q_max = [2.38520786, 1.98025934, 0.64714262, 2.80537157]
    output_eqb_maoms = [2.13182275, 0.65105909, 0.36433141, 0.58717765]

    equib_maoms = calculate_equilibrium_maom(
        dummy_carbon_data["pH"],
        Q_max,
        dummy_carbon_data["soil_c_pool_lmwc"],
        constants=SoilConsts,
    )
    assert np.allclose(equib_maoms, output_eqb_maoms)


@pytest.mark.parametrize(
    "alternative,output_capacities,raises,expected_log_entries",
    [
        (
            None,
            [2.38520786, 1.98025934, 0.64714262, 2.80537157],
            does_not_raise(),
            (),
        ),
        (
            [156.0],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative clay content must be expressed as a percentage!"),),
        ),
        (
            [-9.0],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative clay content must be expressed as a percentage!"),),
        ),
    ],
)
def test_calculate_max_sorption_capacity(
    caplog,
    dummy_carbon_data,
    alternative,
    output_capacities,
    raises,
    expected_log_entries,
):
    """Test that max sorption capacity calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_max_sorption_capacity

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        if alternative:
            max_capacities = calculate_max_sorption_capacity(
                dummy_carbon_data["bulk_density"],
                np.array(alternative, dtype=np.float32),
                SoilConsts.max_sorption_with_clay_slope,
                SoilConsts.max_sorption_with_clay_intercept,
            )
        else:
            max_capacities = calculate_max_sorption_capacity(
                dummy_carbon_data["bulk_density"],
                dummy_carbon_data["percent_clay"],
                SoilConsts.max_sorption_with_clay_slope,
                SoilConsts.max_sorption_with_clay_intercept,
            )

        assert np.allclose(max_capacities, output_capacities)

    log_check(caplog, expected_log_entries)


def test_calculate_binding_coefficient(dummy_carbon_data):
    """Test that Langmuir binding coefficient calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_binding_coefficient

    output_coefs = [168.26740611, 24.49063242, 12.88249552, 52.9419581]

    binding_coefs = calculate_binding_coefficient(
        dummy_carbon_data["pH"],
        SoilConsts.binding_with_ph_slope,
        SoilConsts.binding_with_ph_intercept,
    )

    assert np.allclose(binding_coefs, output_coefs)


@pytest.mark.parametrize(
    "activation_energy,expected_factors",
    [
        (30000.0, [2.57153601, 2.82565326, 3.10021393, 1.73629781]),
        (45000.0, [4.12371761, 4.74983258, 5.45867825, 2.28789625]),
        (57000.0, [6.01680536, 7.19657491, 8.58309980, 2.85289648]),
    ],
)
def calculate_temperature_effect_on_microbes(
    dummy_carbon_data, top_soil_layer_index, activation_energy, expected_factors
):
    """Test function to calculate microbial temperature response."""
    from virtual_rainforest.models.soil.carbon import (
        calculate_temperature_effect_on_microbes,
    )

    actual_factors = calculate_temperature_effect_on_microbes(
        soil_temperature=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        activation_energy=activation_energy,
        reference_temperature=SoilConsts.arrhenius_reference_temp,
        gas_constant=SoilConsts.universal_gas_constant,
    )

    assert np.allclose(expected_factors, actual_factors)


def test_convert_temperature_to_scalar(dummy_carbon_data, top_soil_layer_index):
    """Test that scalar_temperature runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_temperature_to_scalar

    output_scalars = [1.27113, 1.27196, 1.27263, 1.26344]

    temp_scalar = convert_temperature_to_scalar(
        dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        SoilConsts.temp_scalar_coefficient_1,
        SoilConsts.temp_scalar_coefficient_2,
        SoilConsts.temp_scalar_coefficient_3,
        SoilConsts.temp_scalar_coefficient_4,
        SoilConsts.temp_scalar_reference_temp,
    )

    assert np.allclose(temp_scalar, output_scalars)


@pytest.mark.parametrize(
    "alternative,output_scalars,raises,expected_log_entries",
    [
        (None, [0.750035, 0.947787, 0.880671, 0.167814], does_not_raise(), ()),
        (
            [-0.2],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative water content cannot go below zero or above one!"),),
        ),
        (
            [2.7],
            [],
            pytest.raises(ValueError),
            ((ERROR, "Relative water content cannot go below zero or above one!"),),
        ),
    ],
)
def test_convert_moisture_to_scalar(
    caplog,
    dummy_carbon_data,
    alternative,
    output_scalars,
    raises,
    expected_log_entries,
    top_soil_layer_index,
):
    """Test that scalar_moisture runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_moisture_to_scalar

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        if alternative:
            moist_scalar = convert_moisture_to_scalar(
                np.array(alternative, dtype=np.float32),
                SoilConsts.moisture_scalar_coefficient,
                SoilConsts.moisture_scalar_exponent,
            )
        else:
            moist_scalar = convert_moisture_to_scalar(
                dummy_carbon_data["soil_moisture"][top_soil_layer_index],
                SoilConsts.moisture_scalar_coefficient,
                SoilConsts.moisture_scalar_exponent,
            )

        assert np.allclose(moist_scalar, output_scalars)

    log_check(caplog, expected_log_entries)


def test_calculate_maintenance_respiration(dummy_carbon_data, moist_temp_scalars):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_maintenance_respiration

    expected_resps = [0.19906823, 0.0998193, 0.45592854, 0.00763283]

    main_resps = calculate_maintenance_respiration(
        dummy_carbon_data["soil_c_pool_microbe"],
        moist_temp_scalars,
        SoilConsts.microbial_turnover_rate,
    )

    assert np.allclose(main_resps, expected_resps)


def test_calculate_necromass_adsorption(dummy_carbon_data, moist_temp_scalars):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_necromass_adsorption

    expected_adsorps = [0.13824183, 0.06931897, 0.31661708, 0.00530057]

    actual_adsorps = calculate_necromass_adsorption(
        dummy_carbon_data["soil_c_pool_microbe"],
        moist_temp_scalars,
        SoilConsts.necromass_adsorption_rate,
    )

    assert np.allclose(actual_adsorps, expected_adsorps)


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


def test_calculate_microbial_saturation(dummy_carbon_data):
    """Check microbial activity saturation calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_microbial_saturation

    expected_saturated = [0.99876016, 0.99687933, 0.99936324, 0.99285147]

    actual_saturated = calculate_microbial_saturation(
        dummy_carbon_data["soil_c_pool_microbe"],
        SoilConsts.half_sat_microbial_activity,
    )

    assert np.allclose(actual_saturated, expected_saturated)


def test_calculate_microbial_pom_mineralisation_saturation(dummy_carbon_data):
    """Check microbial mineralisation saturation calculates correctly."""
    from virtual_rainforest.models.soil.carbon import (
        calculate_microbial_pom_mineralisation_saturation,
    )

    expected_saturated = [0.99793530, 0.99480968, 0.99893917, 0.98814229]

    actual_saturated = calculate_microbial_pom_mineralisation_saturation(
        dummy_carbon_data["soil_c_pool_microbe"],
        SoilConsts.half_sat_microbial_pom_mineralisation,
    )

    assert np.allclose(actual_saturated, expected_saturated)


def test_calculate_pom_decomposition_saturation(dummy_carbon_data):
    """Check POM decomposition saturation calculates correctly."""
    from virtual_rainforest.models.soil.carbon import (
        calculate_pom_decomposition_saturation,
    )

    expected_saturated = [0.4, 0.86956521, 0.82352941, 0.7]

    actual_saturated = calculate_pom_decomposition_saturation(
        dummy_carbon_data["soil_c_pool_pom"], SoilConsts.half_sat_pom_decomposition
    )

    assert np.allclose(actual_saturated, expected_saturated)


def test_calculate_microbial_carbon_uptake(
    dummy_carbon_data, top_soil_layer_index, moist_temp_scalars
):
    """Check microbial carbon uptake calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_microbial_carbon_uptake

    expected_uptake = [0.00599894, 0.00277614, 0.01176059, 0.00017683]

    actual_uptake = calculate_microbial_carbon_uptake(
        dummy_carbon_data["soil_c_pool_lmwc"],
        dummy_carbon_data["soil_c_pool_microbe"],
        moist_temp_scalars,
        dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        constants=SoilConsts,
    )

    assert np.allclose(actual_uptake, expected_uptake)


def test_calculate_labile_carbon_leaching(dummy_carbon_data, moist_temp_scalars):
    """Check leaching of labile carbon is calculated correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_labile_carbon_leaching

    expected_leaching = [7.15045537e-05, 3.61665981e-05, 1.68115460e-04, 1.59018704e-06]

    actual_leaching = calculate_labile_carbon_leaching(
        dummy_carbon_data["soil_c_pool_lmwc"],
        moist_temp_scalars,
        SoilConsts.leaching_rate_labile_carbon,
    )

    assert np.allclose(actual_leaching, expected_leaching)


def test_calculate_pom_decomposition(dummy_carbon_data, moist_temp_scalars):
    """Check that particulate organic matter decomposition is calculated correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_pom_decomposition

    expected_decomp = [0.0038056940, 0.0104286084, 0.0092200655, 0.0014665616]

    actual_decomp = calculate_pom_decomposition(
        dummy_carbon_data["soil_c_pool_pom"],
        dummy_carbon_data["soil_c_pool_microbe"],
        moist_temp_scalars,
        constants=SoilConsts,
    )

    assert np.allclose(actual_decomp, expected_decomp)
