"""Test module for models.litter.losses.py."""

import numpy as np


def test_calculate_litter_losses(post_consumption_pools, updated_pools, litter_inputs):
    """Test that function to calculate all litter pool losses works correctly."""
    from dataclasses import asdict

    from virtual_ecosystem.models.litter.losses import calculate_litter_losses

    expected_losses = {
        "above_metabolic_carbon": [0.00924801, 0.00456158, 0.00226926, 0.00218688],
        "above_structural_carbon": [0.00033659, 0.00123865, 2.38e-5, 2.553e-5],
        "woody_carbon": [0.000974, 0.00054363, 0.00319062, 0.00318409],
        "below_metabolic_carbon": [0.01820252, 0.014805149, 0.002237224, 0.002398703],
        "below_structural_carbon": [0.000612829, 0.000988361, 4.1361556e-6, 5.6372e-6],
    }

    actual_losses = calculate_litter_losses(
        original_pools=post_consumption_pools,
        final_pools=updated_pools,
        litter_inputs=litter_inputs,
        update_interval=2.0,
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

    expected_loss = [0.00924801, 0.00456158, 0.00226926, 0.00218688]

    actual_loss = calculate_carbon_pool_loss(
        old_pool_size=post_consumption_pools["above_metabolic"],
        final_pool_size=updated_pools["above_metabolic"],
        input_rate=litter_inputs.above_metabolic,
        update_interval=2.0,
    )

    assert np.allclose(actual_loss, expected_loss)
