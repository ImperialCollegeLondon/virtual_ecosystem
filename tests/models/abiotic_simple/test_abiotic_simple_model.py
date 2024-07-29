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
    (DEBUG, "abiotic_simple model: required var 'atmospheric_pressure_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'atmospheric_co2_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'leaf_area_index' checked"),
    (DEBUG, "abiotic_simple model: required var 'layer_heights' checked"),
    # (DEBUG, "abiotic_simple model: required var 'wind_speed_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'mean_annual_temperature' checked"),
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


def test_setup(dummy_climate_data_varying_canopy, fixture_core_components):
    """Test set up and update."""

    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    lyr_strct = fixture_core_components.layer_structure

    # initialise model
    model = AbioticSimpleModel(
        data=dummy_climate_data_varying_canopy,
        core_components=fixture_core_components,
    )

    model.setup()

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.712458, 21.317566, 21.922674, 21.922674],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((4, 3), 0.141727),
            dims=["cell_id", "time_index"],
            coords={"cell_id": [0, 1, 2, 3]},
        ),
    )

    for var in [
        "vapour_pressure_ref",
        "vapour_pressure_deficit_ref",
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
    ]:
        assert var in model.data

    # Run the update step
    model.update(time_index=0)

    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.91965, 29.946434, 29.973217, 29.973217],
        [29.414851, 29.609901, np.nan, np.nan],
        [28.551891, np.nan, np.nan, np.nan],
        [22.81851, 25.21234, 27.60617, 27.60617],
    ]
    xr.testing.assert_allclose(model.data["air_temperature"], exp_air_temp)

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.712458, 21.317566, 21.922674, 21.922674],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)
