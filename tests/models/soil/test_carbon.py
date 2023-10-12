"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

from contextlib import nullcontext as does_not_raise
from logging import ERROR

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_rainforest.models.soil.constants import SoilConsts


def test_calculate_soil_carbon_updates(dummy_carbon_data, top_soil_layer_index):
    """Test that the two pool update functions work correctly."""

    from virtual_rainforest.models.soil.carbon import calculate_soil_carbon_updates

    change_in_pools = {
        "soil_c_pool_lmwc": [0.2856888982, 0.6083493583, 1.0312899782, 0.0247322212],
        "soil_c_pool_maom": [0.10296645, 0.04445693, -0.31401747, 0.00422143],
        "soil_c_pool_microbe": [-0.16002809, -0.07621711, -0.36452355, -0.01140071],
        "soil_c_pool_pom": [-0.2271067778, -0.5757869357, -0.3535922958, -0.0121264188],
        "soil_enzyme_pom": [1.18e-8, 1.67e-8, 1.8e-9, -1.12e-8],
    }

    # Make order of pools object
    pool_order = {}
    for pool in change_in_pools.keys():
        pool_order[pool] = np.array([])

    delta_pools = calculate_soil_carbon_updates(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"].to_numpy(),
        soil_c_pool_maom=dummy_carbon_data["soil_c_pool_maom"].to_numpy(),
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"].to_numpy(),
        soil_c_pool_pom=dummy_carbon_data["soil_c_pool_pom"].to_numpy(),
        soil_enzyme_pom=dummy_carbon_data["soil_enzyme_pom"].to_numpy(),
        pH=dummy_carbon_data["pH"],
        bulk_density=dummy_carbon_data["bulk_density"],
        soil_moisture=np.array([0.5, 0.7, 0.6, 0.2]),
        soil_water_potential=dummy_carbon_data["matric_potential"][
            top_soil_layer_index
        ].to_numpy(),
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        percent_clay=dummy_carbon_data["percent_clay"],
        mineralisation_rate=dummy_carbon_data["litter_C_mineralisation_rate"],
        delta_pools_ordered=pool_order,
        constants=SoilConsts,
    )

    # Check that the updates are correctly calculated. Using a loop here implicitly
    # checks that the output order matches the input order.
    for i, pool in enumerate(change_in_pools.keys()):
        assert np.allclose(delta_pools[i * 4 : (i + 1) * 4], change_in_pools[pool])


def test_calculate_mineral_association(dummy_carbon_data, moist_scalars):
    """Test that mineral_association runs and generates the correct values."""

    from virtual_rainforest.models.soil.carbon import calculate_mineral_association

    output_l_to_m = [-5.78872135e-03, -1.00408341e-02, -5.62807109e-01, 2.60743689e-05]

    # Then calculate mineral association rate
    lmwc_to_maom = calculate_mineral_association(
        dummy_carbon_data["soil_c_pool_lmwc"],
        dummy_carbon_data["soil_c_pool_maom"],
        dummy_carbon_data["pH"],
        dummy_carbon_data["bulk_density"],
        moist_scalars,
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


def test_determine_microbial_biomass_losses(dummy_carbon_data, top_soil_layer_index):
    """Check that the determination of microbial biomass losses works correctly."""
    from virtual_rainforest.models.soil.carbon import determine_microbial_biomass_losses

    expected_maintenance = [0.05443078, 0.02298407, 0.12012258, 0.00722288]
    expected_pom_enzyme = [0.0005443078, 0.0002298407, 0.0012012258, 7.22288e-5]
    expected_maom_enzyme = [0.0005443078, 0.0002298407, 0.0012012258, 7.22288e-5]
    expected_decay_to_pom = [0.0266710822, 0.0112621943, 0.0588600642, 0.0035392112]
    expected_decay_to_lmwc = [0.0266710822, 0.0112621943, 0.0588600642, 0.0035392112]

    losses = determine_microbial_biomass_losses(
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        constants=SoilConsts,
    )

    # Check that each rate matches expectation
    assert np.allclose(losses.maintenance_synthesis, expected_maintenance)
    assert np.allclose(losses.pom_enzyme_production, expected_pom_enzyme)
    assert np.allclose(losses.maom_enzyme_production, expected_maom_enzyme)
    assert np.allclose(losses.necromass_decay_to_lmwc, expected_decay_to_lmwc)
    assert np.allclose(losses.necromass_decay_to_pom, expected_decay_to_pom)

    # Then check that sum of other rates is the same as the overall
    # maintenance_synthesis rate
    assert np.allclose(
        losses.maintenance_synthesis,
        losses.pom_enzyme_production
        + losses.maom_enzyme_production
        + losses.necromass_decay_to_lmwc
        + losses.necromass_decay_to_pom,
    )


def test_calculate_maintenance_biomass_synthesis(
    dummy_carbon_data, moist_scalars, top_soil_layer_index
):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_rainforest.models.soil.carbon import (
        calculate_maintenance_biomass_synthesis,
    )

    expected_loss = [0.05443078, 0.02298407, 0.12012258, 0.00722288]

    actual_loss = calculate_maintenance_biomass_synthesis(
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        constants=SoilConsts,
    )

    assert np.allclose(actual_loss, expected_loss)


def test_calculate_necromass_adsorption(dummy_carbon_data, moist_scalars):
    """Check maintenance respiration cost calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_necromass_adsorption

    expected_adsorps = [0.10875517, 0.05449776, 0.24878964, 0.00419536]

    actual_adsorps = calculate_necromass_adsorption(
        dummy_carbon_data["soil_c_pool_microbe"],
        moist_scalars,
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
    from virtual_rainforest.models.soil.carbon import calculate_enzyme_turnover

    actual_decay = calculate_enzyme_turnover(
        enzyme_pool=dummy_carbon_data["soil_enzyme_pom"], turnover_rate=turnover
    )

    assert np.allclose(actual_decay, expected_decay)


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
    dummy_carbon_data, top_soil_layer_index, water_factors
):
    """Check microbial carbon uptake calculates correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_microbial_carbon_uptake

    expected_uptake = [3.15786124e-3, 1.26472838e-3, 4.38868085e-3, 1.75270792e-5]

    actual_uptake = calculate_microbial_carbon_uptake(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        water_factor=water_factors,
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        constants=SoilConsts,
    )

    assert np.allclose(actual_uptake, expected_uptake)


def test_calculate_labile_carbon_leaching(dummy_carbon_data, moist_scalars):
    """Check leaching of labile carbon is calculated correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_labile_carbon_leaching

    expected_leaching = [5.62526764e-05, 2.84336164e-05, 1.32100695e-04, 1.25860748e-06]

    actual_leaching = calculate_labile_carbon_leaching(
        dummy_carbon_data["soil_c_pool_lmwc"],
        moist_scalars,
        SoilConsts.leaching_rate_labile_carbon,
    )

    assert np.allclose(actual_leaching, expected_leaching)


def test_calculate_pom_decomposition(
    dummy_carbon_data, top_soil_layer_index, water_factors
):
    """Check that particulate organic matter decomposition is calculated correctly."""
    from virtual_rainforest.models.soil.carbon import calculate_pom_decomposition

    expected_decomp = [0.25589892, 0.58810966, 0.41294236, 0.02116563]

    actual_decomp = calculate_pom_decomposition(
        dummy_carbon_data["soil_c_pool_pom"],
        dummy_carbon_data["soil_c_pool_microbe"],
        water_factor=water_factors,
        soil_temp=dummy_carbon_data["soil_temperature"][top_soil_layer_index],
        constants=SoilConsts,
    )

    assert np.allclose(actual_decomp, expected_decomp)
