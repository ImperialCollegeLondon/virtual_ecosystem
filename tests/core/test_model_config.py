"""Test core.model_config."""

import datetime
from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest
from pint import Quantity
from pydantic import ValidationError


@pytest.mark.parametrize(
    argnames="value, raises",
    argvalues=[
        (1, pytest.raises(ValidationError)),
        ("h", pytest.raises(ValidationError)),
        ([1], pytest.raises(ValidationError)),
        ([-1], does_not_raise()),
        ([-1, -0.5], pytest.raises(ValidationError)),
        ([-0.5, -1.5], does_not_raise()),
    ],
)
def test_LayersConfiguration_soil_layers(value, raises):
    """Testing LayersConfiguration validation."""
    from virtual_ecosystem.core.model_config import LayersConfiguration

    with raises:
        LayersConfiguration(soil_layers=value)


@pytest.mark.parametrize(
    argnames="value, raises",
    argvalues=[
        (1, does_not_raise()),
        (1.23, does_not_raise()),
        (0, pytest.raises(ValidationError)),
        (np.inf, pytest.raises(ValidationError)),
        (np.nan, pytest.raises(ValidationError)),
        (-9, pytest.raises(ValidationError)),
        (-9.5, pytest.raises(ValidationError)),
    ],
)
def test_LayersConfiguration_heights(value, raises):
    """Testing LayersConfiguration validation."""
    from virtual_ecosystem.core.model_config import LayersConfiguration

    with raises:
        LayersConfiguration(
            above_canopy_height_offset=value,
            subcanopy_layer_height=value + 1,  # Must be above surface layer
            surface_layer_height=value,
        )


@pytest.mark.parametrize(
    argnames="surf, subc, raises",
    argvalues=[
        (0.1, 2, does_not_raise()),
        (1.2, 1.21, does_not_raise()),
        (1.2, 1.2, pytest.raises(ValidationError)),  # Validation is > not >=
        (1.2, 0.1, pytest.raises(ValidationError)),
    ],
)
def test_LayersConfiguration_relative_heights(surf, subc, raises):
    """Testing LayersConfiguration validation."""
    from virtual_ecosystem.core.model_config import LayersConfiguration

    with raises:
        LayersConfiguration(
            subcanopy_layer_height=subc,
            surface_layer_height=surf,
        )


@pytest.mark.parametrize(
    argnames="value, raises",
    argvalues=[
        (10, does_not_raise()),
        (0, pytest.raises(ValidationError)),
        (1.23, pytest.raises(ValidationError)),
        (np.inf, pytest.raises(ValidationError)),
        (np.nan, pytest.raises(ValidationError)),
        (-9, pytest.raises(ValidationError)),
        (-9.5, pytest.raises(ValidationError)),
        ("h", pytest.raises(ValidationError)),
        ([1], pytest.raises(ValidationError)),
    ],
)
def test_LayersConfiguration_n_layers(value, raises):
    """Testing LayersConfiguration validation."""
    from virtual_ecosystem.core.model_config import LayersConfiguration

    with raises:
        LayersConfiguration(canopy_layers=value)


@pytest.mark.parametrize(
    argnames="config,output,raises,err_msg",
    argvalues=[
        pytest.param(
            {
                "start_date": datetime.date(2020, 1, 1),
                "update_interval": "10 minutes",
                "run_length": "30 years",
            },
            {
                "start_time": np.datetime64("2020-01-01"),
                "update_interval": np.timedelta64(10, "m"),
                "update_interval_as_quantity": Quantity("10 minutes"),
                "end_time": np.datetime64("2049-12-31T12:00"),
            },
            does_not_raise(),
            None,
            id="timing correct",
        ),
        pytest.param(
            {
                "start_date": datetime.date(2020, 1, 1),
                "update_interval": "10 metres",
                "run_length": "30 years",
            },
            None,
            pytest.raises(ValidationError),
            "Value error, Cannot parse value as time quantity: 10 metres",
            id="bad update dimension",
        ),
        pytest.param(
            {
                "start_date": datetime.date(2020, 1, 1),
                "update_interval": "10 epochs",
                "run_length": "30 years",
            },
            None,
            pytest.raises(ValidationError),
            "Value error, Cannot parse value as time quantity: 10 epochs",
            id="unknown update unit",
        ),
        pytest.param(
            {
                "start_date": datetime.date(2020, 1, 1),
                "update_interval": "10 minutes",
                "run_length": "1 minute",
            },
            None,
            pytest.raises(ValidationError),
            "Value error, Model run length (1 minute) expires before "
            "first update (10 minutes)",
            id="run length too short",
        ),
    ],
)
def test_ModelTiming(config, output, raises, err_msg):
    """Test that function to extract main loop timing works as intended."""

    from virtual_ecosystem.core.core_components import ModelTiming
    from virtual_ecosystem.core.model_config import TimingConfiguration

    with raises as excep:
        cfg = TimingConfiguration(**config)
        model_timing = ModelTiming(config=cfg)

        assert model_timing.end_time == output["end_time"]
        assert model_timing.update_interval == output["update_interval"]
        assert model_timing.start_time == output["start_time"]
        assert (
            model_timing.update_interval_quantity
            == output["update_interval_as_quantity"]
        )
        assert len(model_timing.update_dates) == model_timing.n_updates
        return

    assert excep.value.errors()[0]["msg"] == err_msg
