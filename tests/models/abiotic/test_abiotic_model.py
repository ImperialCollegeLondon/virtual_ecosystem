"""Test module for abiotic.abiotic_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import DEBUG, ERROR, INFO

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError

REQUIRED_INIT_VAR_CHECKS = (
    (DEBUG, "abiotic model: required var 'air_temperature_ref' checked"),
    (DEBUG, "abiotic model: required var 'atmospheric_co2_ref' checked"),
    (DEBUG, "abiotic model: required var 'atmospheric_pressure_ref' checked"),
    (DEBUG, "abiotic model: required var 'layer_heights' checked"),
    (DEBUG, "abiotic model: required var 'leaf_area_index' checked"),
    (DEBUG, "abiotic model: required var 'mean_annual_temperature' checked"),
    (DEBUG, "abiotic model: required var 'relative_humidity_ref' checked"),
    (DEBUG, "abiotic model: required var 'shortwave_absorption' checked"),
    (DEBUG, "abiotic model: required var 'wind_speed_ref' checked"),
    (DEBUG, "abiotic model: required var 'downward_longwave_radiation' checked"),
    (DEBUG, "abiotic model: required var 'aerodynamic_resistance_canopy' checked"),
    (DEBUG, "abiotic model: required var 'specific_heat_air' checked"),
    (DEBUG, "abiotic model: required var 'latent_heat_vapourisation' checked"),
    (DEBUG, "abiotic model: required var 'density_air' checked"),
)

SETUP_MANIPULATIONS = (
    (INFO, "Adding data array for 'vapour_pressure_deficit_ref'"),
    (INFO, "Adding data array for 'vapour_pressure_ref'"),
    (INFO, "Adding data array for 'air_temperature'"),
    (INFO, "Adding data array for 'relative_humidity'"),
    (INFO, "Adding data array for 'vapour_pressure_deficit'"),
    (INFO, "Adding data array for 'wind_speed'"),
    (INFO, "Adding data array for 'vapour_pressure'"),
    (INFO, "Adding data array for 'atmospheric_pressure'"),
    (INFO, "Adding data array for 'atmospheric_co2'"),
    (INFO, "Adding data array for 'soil_temperature'"),
    (INFO, "Adding data array for 'net_radiation'"),
    (INFO, "Adding data array for 'canopy_temperature'"),
    (INFO, "Adding data array for 'sensible_heat_flux'"),
    (INFO, "Adding data array for 'latent_heat_flux'"),
    (INFO, "Adding data array for 'longwave_emission'"),
    (INFO, "Adding data array for 'ground_heat_flux'"),
)


@pytest.fixture
def fixture_abiotic_init_data(dummy_climate_data_varying_canopy):
    """Returns a reduced dataset suitable for initialising an Abiotic Model."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel

    # Reduce to data to initialise model
    init_data = Data(grid=dummy_climate_data_varying_canopy.grid)
    for var in AbioticModel.vars_required_for_init:
        init_data[var] = dummy_climate_data_varying_canopy[var]

    return init_data


def test_abiotic_model_initialization(
    caplog,
    fixture_abiotic_init_data,
    fixture_core_components,
    fixture_abiotic_constants,
):
    """Test `AbioticModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel

    # Initialize model
    model = AbioticModel(
        data=fixture_abiotic_init_data,
        core_components=fixture_core_components,
        model_constants=fixture_abiotic_constants,
    )

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "abiotic"
    assert str(model) == "A abiotic model instance"
    assert repr(model) == "AbioticModel(update_interval=1209600 seconds)"

    # Final check that expected logging entries are produced
    log_check(
        caplog,
        expected_log=REQUIRED_INIT_VAR_CHECKS + SETUP_MANIPULATIONS,
    )


def test_abiotic_model_initialization_no_data(
    caplog, fixture_core_components, fixture_abiotic_constants
):
    """Test `AbioticModel` initialization with no data."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel

    with pytest.raises(ValueError):
        # Make four cell grid
        grid = Grid(cell_nx=4, cell_ny=1)
        empty_data = Data(grid)

        # Try and initialise model with empty data object
        _ = AbioticModel(
            empty_data,
            core_components=fixture_core_components,
            model_constants=fixture_abiotic_constants,
        )

    # Final check that expected logging entries are produced

    expected_var_warnings = (
        (ERROR, f"abiotic model: init data missing required var '{var}'")
        for var in AbioticModel.vars_required_for_init
    )

    log_check(
        caplog,
        expected_log=(
            *expected_var_warnings,
            (ERROR, "abiotic model: error checking vars_required_for_init, see log."),
        ),
    )


@pytest.mark.parametrize(
    "cfg_string, raises, expected_log_entries",
    [
        pytest.param(
            (
                "[core]\n[core.grid]\ncell_nx = 2\ncell_ny = 2\n"
                "[core.timing]\nupdate_interval = '12 hours'\n[abiotic]\n"
            ),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the abiotic model successfully "
                    "extracted.",
                ),
                *REQUIRED_INIT_VAR_CHECKS + SETUP_MANIPULATIONS,
            ),
            id="default_config",
        ),
        pytest.param(
            (
                "[core]\n[core.grid]\ncell_nx = 2\ncell_ny = 2\n"
                "[core.timing]\nupdate_interval = '12 hours'\n"
                "[abiotic.constants]\nzero_plane_scaling_parameter = 0.05\n"
            ),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the abiotic model successfully "
                    "extracted.",
                ),
                *REQUIRED_INIT_VAR_CHECKS + SETUP_MANIPULATIONS,
            ),
            id="modified_config_correct",
        ),
        pytest.param(
            (
                "[core]\n[core.grid]\ncell_nx = 2\ncell_ny = 2\n"
                "[core.timing]\nupdate_interval = '1 year'\n[abiotic]\n"
            ),
            pytest.raises(ConfigurationError),
            (
                (
                    INFO,
                    "Information required to initialise the abiotic model "
                    "successfully extracted.",
                ),
                *REQUIRED_INIT_VAR_CHECKS,
                (
                    ERROR,
                    "The update interval is slower than the abiotic upper "
                    "bound of 1 month.",
                ),
            ),
            id="time interval out of bounds",
        ),
    ],
)
def test_generate_abiotic_model(
    caplog,
    fixture_abiotic_init_data,
    cfg_string,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the abiotic model behaves as expected."""

    from virtual_ecosystem.core.config_builder import (
        ConfigurationLoader,
        generate_configuration,
    )
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel

    config_data = ConfigurationLoader(cfg_strings=cfg_string)
    configuration = generate_configuration(config_data.data)
    core_components = CoreComponents(configuration.core)
    caplog.clear()

    with raises:
        AbioticModel.from_config(
            data=fixture_abiotic_init_data,
            configuration=configuration,
            core_components=core_components,
        )

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_setup_and_update_abiotic_model(
    fixture_abiotic_init_data,
    dummy_climate_data_varying_canopy,
    fixture_core_components,
):
    """Test that setup() and update() returns expected output in data object."""

    from virtual_ecosystem.models.abiotic.abiotic_model import AbioticModel

    lyr_strct = fixture_core_components.layer_structure

    # initialise model
    model = AbioticModel(
        data=fixture_abiotic_init_data,
        core_components=fixture_core_components,
    )

    # check all variables are initialised in data object
    for var in model.vars_populated_by_init:
        assert var in model.data

    # Test that VPD was calculated for all time steps
    xr.testing.assert_allclose(
        model.data["vapour_pressure_deficit_ref"],
        DataArray(
            np.full((4, 3), 0.423372),
            dims=["cell_id", "time_index"],
            coords={
                "cell_id": [0, 1, 2, 3],
            },
        ),
    )

    # Test that soil temperature was created correctly
    expected_soil_temp = lyr_strct.from_template()
    expected_soil_temp[lyr_strct.index_all_soil] = np.array(
        [[20.712458, 21.317566, 21.922674, 22.527783], [20.0, 20.0, 20.0, 20.0]]
    )
    xr.testing.assert_allclose(model.data["soil_temperature"], expected_soil_temp)

    # Test that air temperature was interpolated correctly
    exp_air_temp = lyr_strct.from_template()
    exp_air_temp[lyr_strct.index_filled_atmosphere] = np.array(
        [
            [30, 30, 30, 30],
            [29.91965, 29.946434, 29.973217, np.nan],
            [29.414851, 29.609901, np.nan, np.nan],
            [28.551891, np.nan, np.nan, np.nan],
            [22.81851, 25.21234, 27.60617, 30.0],
        ]
    )
    xr.testing.assert_allclose(model.data["air_temperature"], exp_air_temp)

    # Test check fluxes initialise correctly
    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        expected_vals = lyr_strct.from_template()
        expected_vals[lyr_strct.index_filled_canopy] = 0.001
        expected_vals[lyr_strct.index_surface_scalar] = 0.001
        expected_vals[lyr_strct.index_topsoil_scalar] = 0.001
        xr.testing.assert_allclose(model.data[var], expected_vals)

    # Add update data to the model data
    for var in model.vars_required_for_update:
        model.data[var] = dummy_climate_data_varying_canopy[var]

    model.update(time_index=0)

    # Check that values fall within a reasonable expected range
    soil_temps = model.data["soil_temperature"].isel(layers=lyr_strct.index_all_soil)

    # To test with varying canopy layers, need to mask
    canopy_mask = ~np.isnan(
        dummy_climate_data_varying_canopy["canopy_temperature"].isel(
            layers=lyr_strct.index_filled_canopy
        )
    )
    atm_mask = ~np.isnan(
        dummy_climate_data_varying_canopy["air_temperature"].isel(
            layers=lyr_strct.index_filled_atmosphere
        )
    )

    canopy_temp_result = model.data["canopy_temperature"].isel(
        layers=lyr_strct.index_filled_canopy
    )
    air_temp_result = model.data["air_temperature"].isel(
        layers=lyr_strct.index_filled_atmosphere
    )
    rel_hum_result = model.data["relative_humidity"].isel(
        layers=lyr_strct.index_filled_atmosphere
    )

    # Use the mask as a DataArray for .where()
    valid_values_can_temp = canopy_temp_result.where(canopy_mask)
    valid_values_air_temp = air_temp_result.where(atm_mask)
    valid_values_rel_hum = rel_hum_result.where(atm_mask)

    # Now drop the NaNs (i.e., masked values)
    valid_values_can_temp_clean = valid_values_can_temp.dropna(dim="layers", how="any")
    valid_values_air_temp_clean = valid_values_air_temp.dropna(dim="layers", how="any")
    valid_values_rel_hum_clean = valid_values_rel_hum.dropna(dim="layers", how="any")

    # Now do the test
    assert ((soil_temps >= 0.0) & (soil_temps <= 40.0)).all()
    assert (
        (valid_values_can_temp_clean >= 0.0) & (valid_values_can_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_air_temp_clean >= 0.0) & (valid_values_air_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_rel_hum_clean >= 0.0) & (valid_values_rel_hum_clean <= 100.0)
    ).all()
