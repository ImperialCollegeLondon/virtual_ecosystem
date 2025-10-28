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
        "above_metabolic_carbon": [0.00924801, 0.00456158, 0.00226926, 0.00218688],
        "above_structural_carbon": [0.00033659, 0.00123865, 2.38e-5, 2.553e-5],
        "woody_carbon": [0.000974, 0.00054363, 0.00319062, 0.00318409],
        "below_metabolic_carbon": [0.01820252, 0.014805149, 0.002237224, 0.002398703],
        "below_structural_carbon": [0.000612829, 0.000988361, 4.1361556e-6, 5.6372e-6],
        "above_metabolic_nitrogen": [0.00126685, 0.00052432, 0.00022468, 0.00022315],
        "above_structural_nitrogen": [8.97573e-6, 2.86724e-5, 5.19651e-7, 5.08566e-7],
        "woody_nitrogen": [1.75495e-5, 8.58815e-6, 6.74550e-5, 5.38763e-5],
        "below_metabolic_nitrogen": [0.00170117, 0.00131019, 0.00014719, 0.00019344],
        "below_structural_nitrogen": [1.21352e-5, 1.77763e-5, 5.65822e-8, 9.21111e-8],
        "above_metabolic_phosphorus": [0.0001614, 6.6398e-5, 2.2670e-5, 2.2828e-5],
        "above_structural_phosphorus": [9.97304e-7, 2.61760e-6, 5.72391e-8, 4.47738e-8],
        "woody_phosphorus": [1.75338e-6, 7.12210e-7, 3.76563e-6, 5.31479e-6],
        "below_metabolic_phosphorus": [5.85855e-5, 3.59960e-5, 7.09779e-6, 5.81645e-6],
        "below_structural_phosphorus": [1.11322e-6, 1.65944e-6, 5.35009e-9, 8.65663e-9],
        "above_structural_lignin": [0.000168295, 0.000123865, 1.666e-5, 1.7871e-5],
        "woody_lignin": [0.000487, 0.000434904, 0.001116717, 0.0011144315],
        "below_structural_lignin": [0.0003064145, 0.00024709, 3.1021167e-6, 4.2279e-6],
        "N_mineralisation_rate": [0.00601335, 0.0037791, 0.0008798, 0.00094215],
        "P_mineralisation_rate": [0.000447699, 0.000214767, 6.719202e-5, 6.802534e-5],
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

    expected_loss = [0.00924801, 0.00456158, 0.00226926, 0.00218688]

    actual_loss = calculate_carbon_pool_loss(
        old_pool_size=post_consumption_pools["above_metabolic"],
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
            [0.04304924, 0.01761422, 0.00758305, 0.00764055],
            id="high_loss",
        ),
    ],
)
def test_calculate_nutrient_pool_loss(
    dummy_litter_data,
    post_consumption_pools,
    litter_inputs,
    input_chemistries,
    carbon_loss,
    expected_nutrient_loss,
):
    """Test that function to calculate total carbon loss from a pool works correctly."""
    from virtual_ecosystem.models.litter.losses import calculate_nutrient_pool_loss

    actual_nutrient_loss = calculate_nutrient_pool_loss(
        initial_pool_size=post_consumption_pools["above_metabolic"],
        carbon_loss=carbon_loss,
        input_rate=litter_inputs.above_metabolic,
        initial_carbon_nutrient_ratio=dummy_litter_data["c_n_ratio_above_metabolic"],
        input_carbon_nutrient_ratio=input_chemistries.above_metabolic_nitrogen,
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
            [0.251383899, 0.025468, 0.0701715, 0.079914],
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
        initial_pool_size=post_consumption_pools["above_structural"],
        carbon_loss=carbon_loss,
        input_rate=litter_inputs.above_structural,
        initial_lignin_proportion=dummy_litter_data["lignin_above_structural"],
        input_lignin_proportion=input_chemistries.above_structural_lignin,
        update_interval=2.0,
    )

    assert np.allclose(actual_lignin_loss, expected_lignin_loss)
