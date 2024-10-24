"""Test module for soil.carbon.py.

This module tests the functionality of the soil carbon module
"""

import numpy as np
import pytest

from virtual_ecosystem.models.soil.constants import SoilConsts


def test_calculate_soil_carbon_updates(dummy_carbon_data, fixture_core_components):
    """Test that the two pool update functions work correctly."""
    from virtual_ecosystem.core.constants import CoreConsts
    from virtual_ecosystem.models.soil.carbon import calculate_soil_carbon_updates

    change_in_pools = {
        "soil_c_pool_lmwc": [0.00226177439, 0.006049897295, -0.019174323, 0.024255464],
        "soil_c_pool_maom": [0.038767651, 0.00829848, 0.05982197, 0.07277182],
        "soil_c_pool_microbe": [-0.04978105, -0.02020101, -0.10280967, -0.00719517],
        "soil_c_pool_pom": [0.00177803841, -0.007860960795, -0.012016245, 0.00545032],
        "soil_c_pool_necromass": [0.001137474, 0.009172067, 0.033573266, -0.08978050],
        "soil_enzyme_pom": [1.18e-8, 1.67e-8, 1.8e-9, -1.12e-8],
        "soil_enzyme_maom": [-0.00031009, -5.09593e-5, 0.0005990658, -3.72112e-5],
        "soil_n_pool_don": [-1.9262695e-7, -3.5218340e-6, -2.5583461e-6, -6.0040799e-5],
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
        soil_c_pool_necromass=dummy_carbon_data["soil_c_pool_necromass"].to_numpy(),
        soil_enzyme_pom=dummy_carbon_data["soil_enzyme_pom"].to_numpy(),
        soil_enzyme_maom=dummy_carbon_data["soil_enzyme_maom"].to_numpy(),
        soil_n_pool_don=dummy_carbon_data["soil_n_pool_don"].to_numpy(),
        pH=dummy_carbon_data["pH"],
        bulk_density=dummy_carbon_data["bulk_density"],
        soil_moisture=dummy_carbon_data["soil_moisture"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        soil_water_potential=dummy_carbon_data["matric_potential"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        vertical_flow_rate=dummy_carbon_data["vertical_flow"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        clay_fraction=dummy_carbon_data["clay_fraction"],
        C_mineralisation_rate=dummy_carbon_data["litter_C_mineralisation_rate"],
        N_mineralisation_rate=dummy_carbon_data["litter_N_mineralisation_rate"],
        delta_pools_ordered=pool_order,
        model_constants=SoilConsts,
        core_constants=CoreConsts,
    )

    # Check that the updates are correctly calculated. Using a loop here implicitly
    # checks that the output order matches the input order.
    for i, pool in enumerate(change_in_pools.keys()):
        assert np.allclose(delta_pools[i * 4 : (i + 1) * 4], change_in_pools[pool])


def test_calculate_microbial_changes(
    dummy_carbon_data, fixture_core_components, environmental_factors
):
    """Check that calculation of microbe related changes works correctly."""

    from virtual_ecosystem.models.soil.carbon import calculate_microbial_changes

    expected_lmwc_uptake = [1.29159055e-2, 8.43352433e-3, 5.77096991e-2, 5.77363558e-5]
    expected_microbe = [-0.04978105, -0.02020101, -0.10280967, -0.00719517]
    expected_pom_enzyme = [1.17571917e-8, 1.67442231e-8, 1.83311362e-9, -1.11675865e-8]
    expected_maom_enzyme = [-3.1009224e-4, -5.0959256e-5, 5.9906583e-4, -3.7211168e-5]
    expected_necromass = [0.05474086, 0.02303502, 0.11952352, 0.00726011]

    mic_changes = calculate_microbial_changes(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        soil_enzyme_pom=dummy_carbon_data["soil_enzyme_pom"],
        soil_enzyme_maom=dummy_carbon_data["soil_enzyme_maom"],
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ],
        env_factors=environmental_factors,
        constants=SoilConsts,
    )

    # Check that each rate matches expectation
    assert np.allclose(mic_changes.lmwc_uptake, expected_lmwc_uptake)
    assert np.allclose(mic_changes.microbe_change, expected_microbe)
    assert np.allclose(mic_changes.pom_enzyme_change, expected_pom_enzyme)
    assert np.allclose(mic_changes.maom_enzyme_change, expected_maom_enzyme)
    assert np.allclose(mic_changes.necromass_generation, expected_necromass)


def test_calculate_enzyme_mediated_rates(
    dummy_carbon_data, environmental_factors, fixture_core_components
):
    """Check that calculation of enzyme mediated rates works as expected."""

    from virtual_ecosystem.models.soil.carbon import calculate_enzyme_mediated_rates

    expected_pom_to_lmwc = [3.39844565e-4, 8.91990315e-3, 1.25055119e-2, 4.14247999e-5]
    expected_maom_to_lmwc = [1.45988485e-3, 2.10172756e-3, 4.69571604e-3, 8.62951373e-6]

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

    assert np.allclose(actual_rates.pom_to_lmwc, expected_pom_to_lmwc)
    assert np.allclose(actual_rates.maom_to_lmwc, expected_maom_to_lmwc)


def test_calculate_enzyme_changes(dummy_carbon_data):
    """Check that the determination of enzyme pool changes works correctly."""

    from virtual_ecosystem.models.soil.carbon import calculate_enzyme_changes

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
    from virtual_ecosystem.models.soil.carbon import (
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
    from virtual_ecosystem.models.soil.carbon import calculate_carbon_use_efficiency

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
    from virtual_ecosystem.models.soil.carbon import calculate_enzyme_turnover

    actual_decay = calculate_enzyme_turnover(
        enzyme_pool=dummy_carbon_data["soil_enzyme_pom"], turnover_rate=turnover
    )

    assert np.allclose(actual_decay, expected_decay)


def test_calculate_microbial_carbon_uptake(
    dummy_carbon_data, fixture_core_components, environmental_factors
):
    """Check microbial carbon uptake calculates correctly."""
    from virtual_ecosystem.models.soil.carbon import calculate_microbial_carbon_uptake

    expected_uptake = [1.29159055e-2, 8.43352433e-3, 5.77096991e-2, 5.77363558e-5]
    expected_assimilation = [4.64972597e-3, 2.78306303e-3, 1.73129097e-2, 2.77134508e-5]

    actual_uptake, actual_assimilation = calculate_microbial_carbon_uptake(
        soil_c_pool_lmwc=dummy_carbon_data["soil_c_pool_lmwc"],
        soil_c_pool_microbe=dummy_carbon_data["soil_c_pool_microbe"],
        water_factor=environmental_factors.water,
        pH_factor=environmental_factors.pH,
        soil_temp=dummy_carbon_data["soil_temperature"][
            fixture_core_components.layer_structure.index_topsoil_scalar
        ].to_numpy(),
        constants=SoilConsts,
    )

    assert np.allclose(actual_uptake, expected_uptake)
    assert np.allclose(actual_assimilation, expected_assimilation)


def test_calculate_enzyme_mediated_decomposition(
    dummy_carbon_data, fixture_core_components, environmental_factors
):
    """Check that particulate organic matter decomposition is calculated correctly."""
    from virtual_ecosystem.models.soil.carbon import (
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

    from virtual_ecosystem.models.soil.carbon import calculate_maom_desorption

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

    from virtual_ecosystem.models.soil.carbon import calculate_sorption_to_maom

    actual_sorption = calculate_sorption_to_maom(
        soil_c_pool=dummy_carbon_data[pool_name],
        sorption_rate_constant=sorption_rate_constant,
    )

    assert np.allclose(actual_sorption, expected_sorption)


def test_calculate_necromass_breakdown(dummy_carbon_data):
    """Check that necromass breakdown to lmwc is calculated correctly."""

    from virtual_ecosystem.models.soil.carbon import calculate_necromass_breakdown

    expected_breakdown = [0.0134008455, 0.0034657359, 0.0214875626, 0.0242601513]

    actual_breakdown = calculate_necromass_breakdown(
        soil_c_pool_necromass=dummy_carbon_data["soil_c_pool_necromass"],
        necromass_decay_rate=SoilConsts.necromass_decay_rate,
    )

    assert np.allclose(actual_breakdown, expected_breakdown)


def test_calculate_mineralisation_split(dummy_carbon_data):
    """Test that the calculation of the mineralisation split works as expected."""
    from virtual_ecosystem.models.soil.carbon import calculate_mineralisation_split

    expected_split = {
        "dissolved": [3.18159e-6, 1.590795e-6, 7.35e-7, 8.25e-6],
        "particulate": [0.00211787841, 0.001058939205, 0.000489265, 0.00549175],
    }

    actual_split = calculate_mineralisation_split(
        mineralisation_rate=dummy_carbon_data["litter_C_mineralisation_rate"],
        litter_leaching_coefficient=SoilConsts.litter_leaching_fraction_carbon,
    )

    assert set(expected_split.keys()) == set(actual_split.keys())

    for key in actual_split.keys():
        assert np.allclose(actual_split[key], expected_split[key])
