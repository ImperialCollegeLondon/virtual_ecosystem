"""Test module for abiotic_simple.abiotic_simple_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG, ERROR, INFO

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError

# Global set of messages from model required var checks
MODEL_VAR_CHECK_LOG = [
    (DEBUG, "abiotic_simple model: required var 'air_temperature_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'relative_humidity_ref' checked"),
]


@pytest.mark.parametrize(
    "raises,expected_log_entries",
    [
        (does_not_raise(), tuple(MODEL_VAR_CHECK_LOG)),
    ],
)
def test_abiotic_simple_model_initialization(
    caplog,
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    raises,
    expected_log_entries,
):
    """Test `AbioticSimpleModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )
    from virtual_ecosystem.models.abiotic_simple.constants import (
        AbioticSimpleBounds,
        AbioticSimpleConsts,
    )

    with raises:
        # Initialize model
        model = AbioticSimpleModel(
            data=dummy_climate_data_varying_canopy,
            core_components=fixture_core_components,
            constants=AbioticSimpleConsts(),
        )

        # In cases where it passes then checks that the object has the right properties
        assert isinstance(model, BaseModel)
        assert model.model_name == "abiotic_simple"
        assert repr(model) == "AbioticSimpleModel(update_interval=1209600 seconds)"
        assert model.bounds == AbioticSimpleBounds()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,satvap1,raises,expected_log_entries",
    [
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n",
            [0.61078, 7.5, 237.3],
            does_not_raise(),
            tuple(
                [
                    (
                        INFO,
                        "Initialised abiotic_simple.AbioticSimpleConsts from config",
                    ),
                    (
                        INFO,
                        "Information required to initialise the abiotic simple model "
                        "successfully extracted.",
                    ),
                    *MODEL_VAR_CHECK_LOG,
                ],
            ),
            id="default_config",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants.AbioticSimpleConsts]\n"
            "saturation_vapour_pressure_factors = [1.0, 2.0, 3.0]\n",
            [1.0, 2.0, 3.0],
            does_not_raise(),
            tuple(
                [
                    (
                        INFO,
                        "Initialised abiotic_simple.AbioticSimpleConsts from config",
                    ),
                    (
                        INFO,
                        "Information required to initialise the abiotic simple model "
                        "successfully extracted.",
                    ),
                    *MODEL_VAR_CHECK_LOG,
                ],
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants.AbioticSimpleConsts]\n"
            "saturation_vapour_pressure_factorx = [1.0, 2.0, 3.0]\n",
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Unknown names supplied for AbioticSimpleConsts: "
                    "saturation_vapour_pressure_factorx",
                ),
                (INFO, "Valid names are: "),
                (
                    CRITICAL,
                    "Could not initialise abiotic_simple.AbioticSimpleConsts "
                    "from config",
                ),
            ),
            id="modified_config_incorrect",
        ),
    ],
)
def test_generate_abiotic_simple_model(
    caplog,
    dummy_climate_data_varying_canopy,
    cfg_string,
    satvap1,
    raises,
    expected_log_entries,
):
    """Test that the initialisation of the simple abiotic model works as expected."""
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    # Build the config object and core components
    config = Config(cfg_strings=cfg_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AbioticSimpleModel.from_config(
            data=dummy_climate_data_varying_canopy,
            core_components=core_components,
            config=config,
        )
        assert model.model_constants.saturation_vapour_pressure_factors == satvap1

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_setup(dummy_climate_data_varying_canopy, fixture_empty_2d_array):
    """Test set up and update."""
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    # Build the config object and core components
    config = Config(
        cfg_strings="[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n"
    )
    core_components = CoreComponents(config)

    # initialise model
    model = AbioticSimpleModel.from_config(
        data=dummy_climate_data_varying_canopy,
        core_components=core_components,
        config=config,
    )

    model.setup()
    exp_soil_temp = DataArray(
        np.full((3, 15, 3), np.nan),
        dims=["cell_id", "layers", "climate_stats"],
        coords={
            "layers": np.arange(0, 15),
            "layer_roles": (
                "layers",
                core_components.layer_structure.layer_roles,
            ),
            "cell_id": [0, 1, 2],
            "climate_stats": ["mean", "min", "max"],
        },
    )
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((3, 3, 3), 0.141727),
            dims=["cell_id", "time_index", "climate_stats"],
            coords={"cell_id": [0, 1, 2], "climate_stats": ["mean", "min", "max"]},
        ),
    )

    # Run the update step
    model.update(time_index=0)

    for var in [
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
    ]:
        assert var in model.data

    exp_air_temp = fixture_empty_2d_array.copy()
    exp_air_temp[[0, 1, 2, 3, 11, 12], :] = [
        [30.0, 30.0, 30.0],
        [29.91965, 29.946434, 29.973217],
        [29.414851, 29.609901, np.nan],
        [28.551891, np.nan, np.nan],
        [26.19, 27.46, 28.73],
        [22.81851, 25.21234, 27.60617],
    ]

    soil_indices = [13, 14]
    soil_values = [
        [[20.712458, 20.712458, 20.712458], [20, 20, 20]],
        [[22.451549, 22.451549, 22.451549], [20, 20, 20]],
        [[21.360448, 21.360448, 21.360448], [20, 20, 20]],
    ]

    soil_temps = [fixture_empty_2d_array.copy() for _ in range(3)]

    for soil_temp, val in zip(soil_temps, soil_values):
        soil_temp[soil_indices, :] = val

    exp_soil_temp = xr.concat(
        soil_temps, dim=xr.DataArray(["mean", "min", "max"], dims="climate_stats")
    )
    np.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)
