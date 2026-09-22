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
        "above_metabolic_carbon": [0.00921295, 0.00447439, 0.00223216, 0.00212283],
        "above_structural_carbon": [
            3.36458168e-4,
            1.23631256e-3,
            2.37903614e-5,
            2.57920483e-5,
        ],
        "woody_carbon": [0.000974, 0.00054363, 0.00319062, 0.00318409],
        "below_metabolic_carbon": [0.02169604, 0.0176682, 0.00267751, 0.00286285],
        "below_structural_carbon": [
            7.33622472e-04,
            1.18398857e-03,
            5.17543991e-06,
            6.78947934e-06,
        ],
        "above_metabolic_nitrogen": [0.00126205, 0.0005143, 0.00022101, 0.00021661],
        "above_structural_nitrogen": [
            8.97219538e-6,
            2.86183907e-5,
            5.19452232e-7,
            5.13773877e-7,
        ],
        "woody_nitrogen": [1.75495e-5, 8.58815e-6, 6.74550e-5, 5.38763e-5],
        "below_metabolic_nitrogen": [0.00202767, 0.00156356, 0.00017615, 0.00023088],
        "below_structural_nitrogen": [
            1.45271225e-05,
            2.12947449e-05,
            7.08119215e-08,
            1.10938735e-07,
        ],
        "above_metabolic_phosphorus": [
            1.60784470e-4,
            6.51294204e-5,
            2.22993458e-5,
            2.21588720e-5,
        ],
        "above_structural_phosphorus": [
            9.96909850e-7,
            2.61266207e-6,
            5.72166187e-8,
            4.52343081e-8,
        ],
        "woody_phosphorus": [1.75338e-6, 7.12210e-7, 3.76563e-6, 5.31479e-6],
        "below_metabolic_phosphorus": [
            6.98295429e-05,
            4.29569608e-05,
            8.49464189e-06,
            6.94192069e-06,
        ],
        "below_structural_phosphorus": [
            1.33265146e-06,
            1.98787709e-06,
            6.69440047e-09,
            1.04261214e-08,
        ],
        "above_structural_lignin": [1.682289e-4, 1.236247e-4, 1.665325e-5, 1.805249e-5],
        "woody_lignin": [0.000487, 0.000434904, 0.001116717, 0.0011144315],
        "below_structural_lignin": [
            3.66811236e-04,
            2.95997143e-04,
            3.88157993e-06,
            5.09210951e-06,
        ],
        "N_mineralisation_rate": [0.00666153, 0.00427272, 0.00093041, 0.00100398],
        "P_mineralisation_rate": [
            4.69393910e-04,
            2.26798263e-04,
            6.92470563e-05,
            6.89424851e-05,
        ],
    }

    actual_losses = calculate_litter_losses(
        data=dummy_litter_data,
        original_pools=post_consumption_pools,
        final_pools=updated_pools,
        litter_inputs=litter_inputs,
        input_chemistries=input_chemistries,
        update_interval=2.0,
        microbial_simulation_depth=fixture_core_constants.microbial_simulation_depth,
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

    expected_loss = [0.00921295, 0.00447439, 0.00223216, 0.00212283]

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
            [0.04309494, 0.01763821, 0.00753933, 0.00755138],
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
            [0.25147855, 0.02613087, 0.07010142, 0.07864394],
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
