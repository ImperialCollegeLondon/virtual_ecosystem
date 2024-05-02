"""Test module for hydrology.hydrology_model.py."""

import numpy as np
import xarray as xr
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts


def test_calculate_layer_thickness():
    """Test."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        calculate_layer_thickness,
    )

    soil_layer_heights = np.array([[-0.5, -0.5, -0.5], [-1.2, -1.2, -1.2]])
    exp_result = np.array([[500, 500, 500], [700, 700, 700]])

    result = calculate_layer_thickness(soil_layer_heights, 1000)

    np.testing.assert_allclose(result, exp_result)


def test_setup_hydrology_input_current_timestep(
    dummy_climate_data, fixture_core_components
):
    """Test that correct values are selected for current time step."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        setup_hydrology_input_current_timestep,
    )

    dummy_climate_data["soil_moisture"] = xr.concat(
        [
            DataArray(np.full((13, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(np.full((2, 3), 50), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )
    result = setup_hydrology_input_current_timestep(
        data=dummy_climate_data,
        time_index=0,
        days=30,
        seed=42,
        layer_roles=fixture_core_components.layer_structure.layer_roles,
        soil_layer_thickness=np.array([[10, 10, 10], [100, 100, 100]]),
        soil_moisture_capacity=0.9,
        soil_moisture_residual=0.1,
        core_constants=CoreConsts(),
        latent_heat_vap_equ_factors=[1.91846e6, 33.91],
    )

    # Check if all variables were created
    var_list = [
        "current_precipitation",
        "subcanopy_temperature",
        "subcanopy_humidity",
        "subcanopy_pressure",
        "subcanopy_wind_speed",
        "leaf_area_index_sum"
        "current_evapotranspiration"
        "soil_layer_heights"
        "soil_layer_thickness"
        "top_soil_moisture_capacity_mm"
        "top_soil_moisture_residual_mm"
        "soil_moisture_true",
        "previous_accumulated_runoff"
        "previous_subsurface_flow_accumulated"
        "groundwater_storage",
    ]

    variables = [var for var in result if var not in var_list]
    assert variables

    # check if climate values are selected correctly
    np.testing.assert_allclose(
        np.sum(result["current_precipitation"], axis=1),
        (dummy_climate_data["precipitation"].isel(time_index=0)).to_numpy(),
    )
    np.testing.assert_allclose(
        result["subcanopy_temperature"], dummy_climate_data["air_temperature"][11]
    )
    np.testing.assert_allclose(
        result["subcanopy_humidity"], dummy_climate_data["relative_humidity"][11]
    )
    np.testing.assert_allclose(
        result["subcanopy_pressure"],
        (dummy_climate_data["atmospheric_pressure_ref"].isel(time_index=0)).to_numpy(),
    )
    np.testing.assert_allclose(
        result["soil_moisture_mm"], DataArray(np.full((2, 3), 50.0))
    )


def test_initialise_soil_moisture_mm(fixture_core_components):
    """Test soil moisture is initialised correctly."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        initialise_soil_moisture_mm,
    )

    result = initialise_soil_moisture_mm(
        soil_layer_thickness=np.array([[10, 10, 10, 10], [100, 100, 100, 100]]),
        layer_structure=fixture_core_components.layer_structure,
        n_cells=4,
        initial_soil_moisture=0.5,
    )
    exp_result = DataArray([[5.0, 5.0, 5.0, 5.0], [50.0, 50.0, 50.0, 50.0]])
    np.testing.assert_allclose(result[13:15], exp_result)
