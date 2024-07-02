"""Test module for hydrology.hydrology_model.py."""

import numpy as np
import pytest
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts


def test_setup_hydrology_input_current_timestep(
    dummy_climate_data, fixture_core_components
):
    """Test that correct values are selected for current time step."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        setup_hydrology_input_current_timestep,
    )

    layer_structure = fixture_core_components.layer_structure
    result = setup_hydrology_input_current_timestep(
        data=dummy_climate_data,
        time_index=0,
        days=30,
        seed=42,
        layer_structure=layer_structure,
        soil_layer_thickness_mm=layer_structure.soil_layer_thickness * 1000,
        soil_moisture_capacity=0.9,
        soil_moisture_residual=0.1,
        core_constants=CoreConsts(),
        latent_heat_vap_equ_factors=[1.91846e6, 33.91],
    )

    # Check if all variables were created TODO switch back to subcanopy
    var_list = [
        "latent_heat_vapourisation",
        "molar_density_air",
        "current_precipitation",
        "surface_temperature",
        "surface_humidity",
        "surface_pressure",
        "surface_wind_speed",
        "leaf_area_index_sum",
        "current_evapotranspiration",
        "top_soil_moisture_capacity",
        "top_soil_moisture_residual",
        "previous_accumulated_runoff",
        "previous_subsurface_flow_accumulated",
        "groundwater_storage",
        "current_soil_moisture",
    ]

    assert set(result.keys()) == set(var_list)

    # check if climate values are selected correctly
    np.testing.assert_allclose(
        np.sum(result["current_precipitation"], axis=1),
        (dummy_climate_data["precipitation"].isel(time_index=0)).to_numpy(),
    )
    # Get the surface layer index as an integer to extract a 1D slice
    surface_idx = fixture_core_components.layer_structure.role_indices["surface"].item()
    np.testing.assert_allclose(
        result["surface_temperature"],
        dummy_climate_data["air_temperature"][surface_idx],
    )
    np.testing.assert_allclose(
        result["surface_humidity"],
        dummy_climate_data["relative_humidity"][surface_idx],
    )
    # The reference data is a time series with cell id in axis 0, the result has cell_id
    # on axis 1, so need to extract from the second axis
    np.testing.assert_allclose(
        result["surface_pressure"],
        dummy_climate_data["atmospheric_pressure_ref"][:, 0].to_numpy(),
    )
    np.testing.assert_allclose(
        result["current_soil_moisture"],
        DataArray(np.tile([[5], [500]], fixture_core_components.grid.n_cells)),
    )


@pytest.mark.parametrize(
    argnames="init_soilm, expected",
    argvalues=(pytest.param(0.5, np.array([[250], [250]]), id="scalar_init_soilm"),),
)
def test_initialise_soil_moisture_mm(fixture_core_components, init_soilm, expected):
    """Test soil moisture is initialised correctly."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        initialise_soil_moisture_mm,
    )

    layer_structure = fixture_core_components.layer_structure

    result = initialise_soil_moisture_mm(
        layer_structure=layer_structure,
        soil_layer_thickness=np.tile(
            layer_structure.soil_layer_thickness[:, None] * 1000,
            fixture_core_components.grid.n_cells,
        ),
        initial_soil_moisture=init_soilm,
    )
    # The fixture is configured with soil layers [-0.25, -1.0]
    exp_result = DataArray(np.broadcast_to(expected, (2, 4)))
    np.testing.assert_allclose(
        result[layer_structure.role_indices["all_soil"]], exp_result
    )
