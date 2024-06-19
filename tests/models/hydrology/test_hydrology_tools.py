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

    result = setup_hydrology_input_current_timestep(
        data=dummy_climate_data,
        time_index=0,
        days=30,
        seed=42,
        layer_structure=fixture_core_components.layer_structure,
        soil_layer_thickness_mm=fixture_core_components.soil_layer_thickness * 1000,
        soil_moisture_capacity=0.9,
        soil_moisture_residual=0.1,
        core_constants=CoreConsts(),
        latent_heat_vap_equ_factors=[1.91846e6, 33.91],
    )

    # Check if all variables were created TODO switch back to subcanopy
    var_list = [
        "current_precipitation",
        # "subcanopy_temperature",
        # "subcanopy_humidity",
        # "subcanopy_pressure",
        # "subcanopy_wind_speed",
        "surface_temperature",
        "surface_humidity",
        "surface_pressure",
        "surface_wind_speed",
        "leaf_area_index_sum",
        "current_evapotranspiration",
        "soil_layer_heights",
        "soil_layer_thickness",
        "top_soil_moisture_capacity_mm",
        "top_soil_moisture_residual_mm",
        "soil_moisture_true",
        "previous_accumulated_runoff",
        "previous_subsurface_flow_accumulated",
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
        result["surface_temperature"],
        dummy_climate_data["air_temperature"].isel(
            layers=fixture_core_components.layer_structure.role_indices["surface"]
        ),
    )
    np.testing.assert_allclose(
        result["surface_humidity"],
        dummy_climate_data["relative_humidity"].isel(
            layers=fixture_core_components.layer_structure.role_indices["surface"]
        ),
    )
    np.testing.assert_allclose(
        result["surface_pressure"],
        (dummy_climate_data["atmospheric_pressure_ref"].isel(time_index=0)).to_numpy(),
    )
    np.testing.assert_allclose(
        result["soil_moisture_mm"],
        DataArray(
            np.full(
                (
                    len(fixture_core_components.soil_layers),
                    fixture_core_components.n_cells,
                ),
                50.0,
            )
        ),
    )


@pytest.mark.parametrize(
    argnames="init_soilm, expected",
    argvalues=(
        pytest.param(0.5, np.array([125, 375]), id="scalar_init_soilm"),
        pytest.param(
            np.array([0.25, 0.5]), np.array([62.5, 375]), id="scalar_init_soilm"
        ),
    ),
)
def test_initialise_soil_moisture_mm(fixture_core_components, init_soilm, expected):
    """Test soil moisture is initialised correctly."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        initialise_soil_moisture_mm,
    )

    layer_structure = fixture_core_components.layer_structure

    result = initialise_soil_moisture_mm(
        layer_structure=layer_structure,
        soil_layer_thickness=layer_structure.soil_layer_thickness * 1000,
        initial_soil_moisture=init_soilm,
    )
    # The fixture is configured with soil layers [-0.25, -1.0]
    exp_result = DataArray(np.broadcast_to(expected[:, None], (2, 4)))
    np.testing.assert_allclose(
        result[layer_structure.role_indices["all_soil"]], exp_result
    )
