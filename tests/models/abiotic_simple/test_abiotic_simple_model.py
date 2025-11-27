"""Test module for abiotic_simple.abiotic_simple_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, INFO
from unittest.mock import patch

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check, patch_bypass_setup, patch_run_update

# Global set of messages from model required var checks
MODEL_VAR_CHECK_LOG = [
    (DEBUG, "abiotic_simple model: required var 'air_temperature_ref' checked"),
    (DEBUG, "abiotic_simple model: required var 'relative_humidity_ref' checked"),
    (INFO, "Replacing data array for 'soil_temperature'"),
    (INFO, "Replacing data array for 'net_radiation'"),
    (INFO, "Replacing data array for 'vapour_pressure_deficit_ref'"),
    (INFO, "Replacing data array for 'vapour_pressure_ref'"),
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
    fixture_abiotic_constants,
    fixture_pyrealm_config,
):
    """Test `AbioticSimpleModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )
    from virtual_ecosystem.models.abiotic_simple.model_config import (
        AbioticSimpleConfiguration,
    )

    default_config = AbioticSimpleConfiguration()

    with (
        patch_run_update(AbioticSimpleModel),
        patch_bypass_setup(AbioticSimpleModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        with raises:
            # Initialize model
            model = AbioticSimpleModel(
                data=dummy_climate_data_varying_canopy,
                core_components=fixture_core_components,
                model_configuration=default_config,
                abiotic_constants=fixture_abiotic_constants,
                pyrealm_core_constants=fixture_pyrealm_config.core,
            )

            # In cases where it passes then checks that the object has the right
            # properties
            assert isinstance(model, BaseModel)
            assert model.model_name == "abiotic_simple"
            assert repr(model) == "AbioticSimpleModel(update_interval=1209600 seconds)"
            assert model.bounds == default_config.bounds

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_string,raises,expected_log_entries",
    [
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n[abiotic_simple]\n",
            does_not_raise(),
            tuple(
                [
                    (
                        INFO,
                        "Information required to initialise the abiotic simple model "
                        "successfully extracted.",
                    ),
                    *MODEL_VAR_CHECK_LOG[:2],
                ],
            ),
            id="default_config",
        ),
        pytest.param(
            "[core.timing]\nupdate_interval = '1 week'\n"
            "[abiotic_simple.constants]\n"
            "initial_net_radiation = 20\n",
            does_not_raise(),
            tuple(
                [
                    (
                        INFO,
                        "Information required to initialise the abiotic simple model "
                        "successfully extracted.",
                    ),
                    *MODEL_VAR_CHECK_LOG[:2],
                ],
            ),
            id="modified_config_correct",
        ),
    ],
)
def test_generate_abiotic_simple_model(
    caplog,
    dummy_climate_data_varying_canopy,
    cfg_string,
    raises,
    expected_log_entries,
):
    """Test that the initialisation of the simple abiotic model works as expected."""
    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )

    config_data = ConfigurationLoader(cfg_strings=cfg_string)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)

    caplog.clear()

    # We patch the _setup step as it is tested separately
    object_to_patch = (
        "virtual_ecosystem.models.abiotic_simple.abiotic_simple_model"
        ".AbioticSimpleModel"
    )
    with (
        patch_run_update(AbioticSimpleModel),
        patch_bypass_setup(AbioticSimpleModel) as mock_bypass_setup,
        patch(f"{object_to_patch}._setup") as mock_setup,
    ):
        mock_bypass_setup.return_value = False
        # Check whether model is initialised (or not) as expected
        with raises:
            AbioticSimpleModel.from_config(
                data=dummy_climate_data_varying_canopy,
                configuration=configuration,
                core_components=core_components,
            )

            mock_setup.assert_called_once()

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_setup(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_abiotic_constants,
    fixture_pyrealm_config,
):
    """Test set up and update."""

    from virtual_ecosystem.models.abiotic_simple.abiotic_simple_model import (
        AbioticSimpleModel,
    )
    from virtual_ecosystem.models.abiotic_simple.model_config import (
        AbioticSimpleConfiguration,
    )

    lyr_strct = fixture_core_components.layer_structure

    # initialise model
    with (
        patch_run_update(AbioticSimpleModel),
        patch_bypass_setup(AbioticSimpleModel) as mock_bypass_setup,
    ):
        mock_bypass_setup.return_value = False
        model = AbioticSimpleModel(
            data=dummy_climate_data_varying_canopy,
            core_components=fixture_core_components,
            model_configuration=AbioticSimpleConfiguration(),
            abiotic_constants=fixture_abiotic_constants,
            pyrealm_core_constants=fixture_pyrealm_config.core,
        )

    exp_soil_temp = lyr_strct.from_template()
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((4, 3), 0.423372),
            dims=["cell_id", "time_index"],
            coords={"cell_id": [0, 1, 2, 3]},
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
        "wind_speed",
    ]:
        assert var in model.data

    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = [
        [30.0, 30.0, 30.0, 30.0],
        [29.91965, 29.946434, 29.973217, np.nan],
        [29.414851, 29.609901, np.nan, np.nan],
        [28.551891, np.nan, np.nan, np.nan],
        [22.81851, 25.21234, 27.60617, 30.0],
    ]
    xr.testing.assert_allclose(model.data["air_temperature"], exp_air_temp)

    exp_wind = lyr_strct.from_template()
    exp_wind[lyr_strct.index_filled_atmosphere] = [
        [1, 1, 1, 1],
        [0.993673, 0.995782, 0.997891, np.nan],
        [0.953925, 0.969284, np.nan, np.nan],
        [0.885976, np.nan, np.nan, np.nan],
        [0.434528, 0.623019, 0.811509, 1.0],
    ]
    xr.testing.assert_allclose(model.data["wind_speed"], exp_wind)

    exp_soil_temp = lyr_strct.from_template()
    exp_soil_temp[lyr_strct.index_all_soil] = [
        [20.712458, 21.317566, 21.922674, 22.527783],
        [20.0, 20.0, 20.0, 20.0],
    ]
    xr.testing.assert_allclose(model.data["soil_temperature"], exp_soil_temp)

    exp_netrad = lyr_strct.from_template()
    exp_netrad[lyr_strct.index_flux_layers] = [
        [449.955469, 449.955309, 449.955149, np.nan],
        [449.958399, 449.957284, np.nan, np.nan],
        [449.96307, np.nan, np.nan, np.nan],
        [449.990086, 449.988875, 449.987557, 449.987557],
    ]
    xr.testing.assert_allclose(model.data["net_radiation"], exp_netrad)
