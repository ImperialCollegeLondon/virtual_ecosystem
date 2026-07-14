"""Test module for models.litter.losses.py."""

import numpy as np
import pytest


def test_calculate_litter_losses(
    dummy_litter_data,
    fixture_core_constants,
    post_consumption_pools,
    updated_pools,
    litter_inputs,
    input_chemistries,
):
    """Test that function to calculate all litter pool losses works correctly."""
    from dataclasses import asdict

    from virtual_ecosystem.models.litter.losses import calculate_litter_losses

    expected_losses = {
        "above_metabolic_carbon": [0.00921291, 0.0044742, 0.00223216, 0.00212139],
        "above_structural_carbon": [3.364579e-4, 1.236247e-3, 2.379036e-5, 2.578927e-5],
        "woody_carbon": [0.000974, 0.00054363, 0.00319062, 0.00318409],
        "below_metabolic_carbon": [0.01820262, 0.01481599, 0.00224357, 0.0023987],
        "below_structural_carbon": [6.128354e-4, 9.892553e-4, 4.322987e-6, 5.671167e-6],
        "above_metabolic_nitrogen": [0.00126204, 0.00051428, 0.00022101, 0.00021647],
        "above_structural_nitrogen": [8.97219e-6, 2.86169e-5, 5.19452e-7, 5.13719e-7],
        "woody_nitrogen": [1.75495e-5, 8.58815e-6, 6.74550e-5, 5.38763e-5],
        "below_metabolic_nitrogen": [0.00170118, 0.00131115, 0.0001476, 0.00019344],
        "below_structural_nitrogen": [1.21353e-5, 1.77924e-5, 5.91484e-8, 9.26657e-8],
        "above_metabolic_phosphorus": [1.60784e-4, 6.51267e-5, 2.22993e-5, 2.21439e-5],
        "above_structural_phosphorus": [9.96909e-7, 2.61252e-6, 5.72166e-8, 4.52294e-8],
        "woody_phosphorus": [1.75338e-6, 7.12210e-7, 3.76563e-6, 5.31479e-6],
        "below_metabolic_phosphorus": [5.858584e-5, 3.60223e-5, 7.11791e-6, 5.81644e-6],
        "below_structural_phosphorus": [1.11324e-6, 1.66093e-6, 5.59176e-9, 8.70881e-9],
        "above_structural_lignin": [1.682289e-4, 1.236247e-4, 1.665325e-5, 1.805249e-5],
        "woody_lignin": [0.000487, 0.000434904, 0.001116717, 0.0011144315],
        "below_structural_lignin": [3.064177e-4, 2.473138e-4, 3.242240e-6, 4.253376e-6],
        "N_mineralisation_rate": [0.00600376, 0.00376086, 0.00087329, 0.00092879],
        "P_mineralisation_rate": [4.464663e-4, 2.122694e-4, 6.649138e-5, 6.665819e-5],
    }

    actual_losses = calculate_litter_losses(
        data=dummy_litter_data,
        original_pools=post_consumption_pools,
        final_pools=updated_pools,
        litter_inputs=litter_inputs,
        input_chemistries=input_chemistries,
        update_interval=2.0,
        active_microbe_depth=fixture_core_constants.max_depth_of_microbial_activity,
    )

    # Convert to a dict to check the values
    actual_losses = asdict(actual_losses)

    # Check that all keys match and have correct values for both dictionaries
    assert set(expected_losses.keys()) == set(actual_losses.keys())

    for key in actual_losses.keys():
        assert np.allclose(actual_losses[key], expected_losses[key])


def test_calculate_carbon_pool_loss(
    post_consumption_pools, updated_pools, litter_inputs
):
    """Test that function to calculate total carbon loss from a pool works correctly."""
    from virtual_ecosystem.models.litter.losses import calculate_carbon_pool_loss

    expected_loss = [0.00921291, 0.0044742, 0.00223216, 0.00212139]

    actual_loss = calculate_carbon_pool_loss(
        old_pool_size=post_consumption_pools["above_metabolic"]
        .sel(element="C")
        .to_numpy(),
        final_pool_size=updated_pools["above_metabolic"],
        input_rate=litter_inputs.above_metabolic,
        update_interval=2.0,
    )

    assert np.allclose(actual_loss, expected_loss)


@pytest.mark.parametrize(
    "carbon_loss,expected_nutrient_loss",
    [
        pytest.param(
            np.array([0.00924801, 0.00456158, 0.00226926, 0.00218688]),
            [0.00126685, 0.00052432, 0.00022468, 0.00022315],
            id="standard_loss",
        ),
        pytest.param(
            np.array([0.32449688, 0.15805352, 0.08320238, 0.0776660]),
            [0.04308754, 0.01763553, 0.00753933, 0.00756049],
            id="high_loss",
        ),
    ],
)
def test_calculate_nutrient_pool_loss(
    post_consumption_pools,
    litter_inputs,
    input_chemistries,
    carbon_loss,
    expected_nutrient_loss,
):
    """Test that function to calculate total carbon loss from a pool works correctly."""
    from virtual_ecosystem.models.litter.losses import calculate_nutrient_pool_loss

    actual_nutrient_loss = calculate_nutrient_pool_loss(
        initial_pool_carbon=post_consumption_pools["above_metabolic"]
        .sel(element="C")
        .to_numpy(),
        initial_pool_nutrient=post_consumption_pools["above_metabolic"]
        .sel(element="N")
        .to_numpy(),
        carbon_loss=carbon_loss,
        input_rate_carbon=litter_inputs.above_metabolic,
        input_rate_nutrient=input_chemistries.above_metabolic_nitrogen,
        update_interval=2.0,
    )

    assert np.allclose(actual_nutrient_loss, expected_nutrient_loss)


@pytest.mark.parametrize(
    "carbon_loss,expected_lignin_loss",
    [
        pytest.param(
            np.array([0.00033659, 0.00123865, 2.38e-5, 2.553e-5]),
            [0.000168295, 0.000123865, 1.666e-5, 1.7871e-5],
            id="standard_loss",
        ),
        pytest.param(
            np.array([0.50553312, 0.25184648, 0.10319762, 0.117284]),
            [0.25147791, 0.02610905, 0.07010142, 0.07865439],
            id="high_loss",
        ),
    ],
)
def test_calculate_lignin_pool_loss(
    dummy_litter_data,
    post_consumption_pools,
    litter_inputs,
    input_chemistries,
    carbon_loss,
    expected_lignin_loss,
):
    """Test that function to calculate total carbon loss from a pool works correctly."""
    from virtual_ecosystem.models.litter.losses import calculate_lignin_pool_loss

    actual_lignin_loss = calculate_lignin_pool_loss(
        initial_pool_size=post_consumption_pools["above_structural"]
        .sel(element="C")
        .to_numpy(),
        carbon_loss=carbon_loss,
        input_rate=litter_inputs.above_structural,
        initial_lignin_proportion=dummy_litter_data["lignin_above_structural"],
        input_lignin_proportion=input_chemistries.above_structural_lignin,
        update_interval=2.0,
    )

    assert np.allclose(actual_lignin_loss, expected_lignin_loss)
