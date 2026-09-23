"""Tests functions in the fruit module."""

import pytest
import xarray as xr


@pytest.mark.parametrize(
    argnames="vals,rate,baseline,days,expected",
    argvalues=(
        pytest.param([20.0], 0.5, 0, 30, [1.0], id="high_rate_high_temp"),
        pytest.param([0.0], 0.5, 0, 30, [0.0], id="high_rate_low_temp"),
        pytest.param([20.0], 0.0075, 0, 30, [0.9888], id="default_rate"),
        pytest.param([20.0], 0.0075, 19, 30, [0.2015], id="higher_baseline_reduces"),
        pytest.param([20.0], 0.0075, 0, 10, [0.7769], id="shorter_period_reduces"),
        pytest.param(
            [20.0, 0, 20, 0, 20],
            0.5,
            0,
            30,
            [1.0, 0.0, 1.0, 0.0, 1.0],
            id="multi_cell",
        ),
    ),
)
def test_calculate_fallen_fruit_decay_fraction(vals, rate, baseline, days, expected):
    """Test that the calculation of the fallen fruit decay fraction works correctly."""
    from virtual_ecosystem.models.plants.fruit import (
        calculate_fallen_fruit_decay_fraction,
    )

    surface_temperature = xr.DataArray(vals, dims="cell_id")
    expected = xr.DataArray(expected, dims="cell_id")
    result = calculate_fallen_fruit_decay_fraction(
        decay_rate=rate,
        surface_temperature=surface_temperature,
        days=days,
        base_temperature=baseline,
    )

    xr.testing.assert_allclose(result, expected, atol=0.0001)
