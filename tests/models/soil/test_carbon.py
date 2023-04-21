"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check


@pytest.fixture
def moist_temp_scalars(dummy_carbon_data):
    """Combined moisture and temperature scalars based on dummy carbon data."""
    from virtual_rainforest.models.soil.carbon import (
        convert_moisture_to_scalar,
        convert_temperature_to_scalar,
    )

    moist_scalars = convert_moisture_to_scalar(dummy_carbon_data["soil_moisture"])
    temp_scalars = convert_temperature_to_scalar(dummy_carbon_data["soil_temperature"])

    return moist_scalars * temp_scalars


def test_calculate_soil_carbon_updates(dummy_carbon_data):
    """Test that the two pool update functions work correctly."""

    from virtual_rainforest.models.soil.carbon import calculate_soil_carbon_updates

    change_in_pools = [
        [-0.0003182, 0.00010624, -0.00016632, 0.00015492],
        [0.1386398, 0.0693311, 0.31676087, 0.0053009],
        [-0.33730482, -0.16913635, -0.77253482, -0.01293334],
    ]

    delta_pools = calculate_soil_carbon_updates(
        dummy_carbon_data["soil_c_pool_lmwc"].to_numpy(),
        dummy_carbon_data["soil_c_pool_maom"].to_numpy(),
        dummy_carbon_data["soil_c_pool_microbe"].to_numpy(),
        dummy_carbon_data["pH"],
        dummy_carbon_data["bulk_density"],
        dummy_carbon_data["soil_moisture"],
        dummy_carbon_data["soil_temperature"],
        dummy_carbon_data["percent_clay"],
        {"soil_c_pool_lmwc": np.array([]), "soil_c_pool_maom": np.array([])},
    )

    # Check that the updates are correctly calculated
    assert np.allclose(delta_pools[:4], change_in_pools[0])
    assert np.allclose(delta_pools[4:8], change_in_pools[1])
    assert np.allclose(delta_pools[8:], change_in_pools[2])


def test_calculate_mineral_association(dummy_carbon_data, moist_temp_scalars):
    """Test that mineral_association runs and generates the correct values."""

    from virtual_rainforest.models.soil.carbon import calculate_mineral_association

    output_l_to_m = [0.000397665, 1.178336e-5, 0.0001434178, 2.80359e-7]

    # Then calculate mineral association rate
    lmwc_to_maom = calculate_mineral_association(
        dummy_carbon_data["soil_c_pool_lmwc"],
        dummy_carbon_data["soil_c_pool_maom"],
        dummy_carbon_data["pH"],
        dummy_carbon_data["bulk_density"],
        moist_temp_scalars,
        dummy_carbon_data["percent_clay"],
    )

    # Check that expected values are generated
    assert np.allclose(lmwc_to_maom, output_l_to_m)


def test_calculate_equilibrium_maom(dummy_carbon_data):
    """Test that equilibrium maom calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_equilibrium_maom

    Q_max = [2.385207e6, 1.980259e6, 647142.61, 2.805371e6]
    output_eqb_maoms = [19900.19, 969.4813, 832.6088, 742.4128]

    equib_maoms = calculate_equilibrium_maom(
        dummy_carbon_data["pH"], Q_max, dummy_carbon_data["soil_c_pool_lmwc"]
    )
    assert np.allclose(equib_maoms, output_eqb_maoms)


@pytest.mark.parametrize(
    "alternative,output_capacities,raises,expected_log_entries",
    [
        (
            None,
            [2.385207e6, 1.980259e6, 647142.61, 2.805371e6],
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
            )
        else:
            max_capacities = calculate_max_sorption_capacity(
                dummy_carbon_data["bulk_density"], dummy_carbon_data["percent_clay"]
            )

        assert np.allclose(max_capacities, output_capacities)

    log_check(caplog, expected_log_entries)


def test_calculate_binding_coefficient(dummy_carbon_data):
    """Test that Langmuir binding coefficient calculation works as expected."""
    from virtual_rainforest.models.soil.carbon import calculate_binding_coefficient

    output_coefs = [0.16826738, 0.02449064, 0.0128825, 0.05294197]

    binding_coefs = calculate_binding_coefficient(dummy_carbon_data["pH"])

    assert np.allclose(binding_coefs, output_coefs)


def test_convert_temperature_to_scalar(dummy_carbon_data):
    """Test that scalar_temperature runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_temperature_to_scalar

    output_scalars = [1.27113, 1.27196, 1.27263, 1.26344]

    temp_scalar = convert_temperature_to_scalar(dummy_carbon_data["soil_temperature"])

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
    caplog, dummy_carbon_data, alternative, output_scalars, raises, expected_log_entries
):
    """Test that scalar_moisture runs and generates the correct value."""
    from virtual_rainforest.models.soil.carbon import convert_moisture_to_scalar

    # Check that initialisation fails (or doesn't) as expected
    with raises:
        if alternative:
            moist_scalar = convert_moisture_to_scalar(
                np.array(alternative, dtype=np.float32)
            )
        else:
            moist_scalar = convert_moisture_to_scalar(
                dummy_carbon_data["soil_moisture"]
            )

        assert np.allclose(moist_scalar, output_scalars)

    log_check(caplog, expected_log_entries)


def test_calculate_maintenance_respiration(dummy_carbon_data, moist_temp_scalars):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_maintenance_respiration

    expected_resps = [0.19906823, 0.0998193, 0.45592854, 0.00763283]

    main_resps = calculate_maintenance_respiration(
        dummy_carbon_data["soil_c_pool_microbe"], moist_temp_scalars
    )

    assert np.allclose(main_resps, expected_resps)


def test_calculate_necromass_adsorption(dummy_carbon_data, moist_temp_scalars):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_necromass_adsorption

    expected_adsorps = [0.13824183, 0.06931897, 0.31661708, 0.00530057]

    actual_adsorps = calculate_necromass_adsorption(
        dummy_carbon_data["soil_c_pool_microbe"], moist_temp_scalars
    )

    assert np.allclose(actual_adsorps, expected_adsorps)


def test_calculate_carbon_use_efficiency(dummy_carbon_data):
    """Check carbon use efficiency calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_carbon_use_efficiency

    expected_cues = [0.36, 0.33, 0.3, 0.48]

    actual_cues = calculate_carbon_use_efficiency(dummy_carbon_data["soil_temperature"])

    assert np.allclose(actual_cues, expected_cues)


def test_calculate_microbial_saturation(dummy_carbon_data):
    """Check microbial activity saturation calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_microbial_saturation

    expected_saturated = [0.99876016, 0.99687933, 0.99936324, 0.99285147]

    actual_saturated = calculate_microbial_saturation(
        dummy_carbon_data["soil_c_pool_microbe"]
    )

    assert np.allclose(actual_saturated, expected_saturated)


def test_calculate_microbial_carbon_uptake(dummy_carbon_data, moist_temp_scalars):
    """Check microbial carbon uptake calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_microbial_carbon_uptake

    expected_uptake = [5.99893556e-06, 2.77613754e-06, 1.17605887e-05, 1.76827789e-07]

    actual_uptake = calculate_microbial_carbon_uptake(
        dummy_carbon_data["soil_c_pool_lmwc"],
        dummy_carbon_data["soil_c_pool_microbe"],
        moist_temp_scalars,
        dummy_carbon_data["soil_temperature"],
    )

    assert np.allclose(actual_uptake, expected_uptake)


def test_calculate_labile_carbon_leaching(dummy_carbon_data, moist_temp_scalars):
    """Check leaching of labile carbon is calculated correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_labile_carbon_leaching

    expected_leaching = [7.15045537e-05, 3.61665981e-05, 1.68115460e-04, 1.59018704e-06]

    actual_leaching = calculate_labile_carbon_leaching(
        dummy_carbon_data["soil_c_pool_lmwc"], moist_temp_scalars
    )

    assert np.allclose(actual_leaching, expected_leaching)


def test_calculate_direct_litter_input_to_lmwc():
    """Check direct litter input to lmwc is calculated correctly."""
    from virtual_rainforest.models.soil.carbon import (
        calculate_direct_litter_input_to_lmwc,
    )

    actual_input = calculate_direct_litter_input_to_lmwc()

    assert np.isclose(actual_input, 0.00015697011)
