"""Test module for hydrology.hydrology_model.py."""

import numpy as np
import pytest
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.hydrology.constants import HydroConsts


def test_initialise_atmosphere_for_hydrology(
    dummy_climate_data, fixture_core_components
):
    """Test initialisation of atmospheric variables for hydrology."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        initialise_atmosphere_for_hydrology,
    )

    data = dummy_climate_data
    layer_structure = fixture_core_components.layer_structure
    output = initialise_atmosphere_for_hydrology(
        data=data,
        model_constants=HydroConsts,
        abiotic_constants=AbioticConsts,
        core_constants=CoreConsts,
        layer_structure=layer_structure,
    )

    # Check keys exist
    expected_keys = [
        "aerodynamic_resistance_surface",
        "aerodynamic_resistance_canopy",
        "stomatal_conductance",
        "density_air",
        "specific_heat_air",
        "latent_heat_vapourisation",
    ]
    for key in expected_keys:
        assert key in output


def test_setup_hydrology_input_current_timestep(
    dummy_climate_data, fixture_core_components
):
    """Test that correct values are selected for current time step."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        setup_hydrology_input_current_timestep,
    )

    lyr_strct = fixture_core_components.layer_structure
    result = setup_hydrology_input_current_timestep(
        data=dummy_climate_data,
        time_index=0,
        days=30,
        seed=42,
        layer_structure=lyr_strct,
        soil_layer_thickness_mm=lyr_strct.soil_layer_thickness * 1000,
        soil_moisture_capacity=0.9,
        soil_moisture_residual=0.1,
    )

    # Check if all variables were created TODO switch back to subcanopy
    var_list = [
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
    surface_idx = lyr_strct.index_surface_scalar
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
    np.testing.assert_allclose(result[layer_structure.index_all_soil], exp_result)


def test_calculate_psychrometric_constant():
    """Test psychrometric constant."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        calculate_psychrometric_constant,
    )

    atmospheric_pressure = np.array([101.3], dtype=np.float32)  # in kPa
    latent_heat_vapourization = np.array([2268.0], dtype=np.float32)  # in kJ/kg
    specific_heat_air = np.array([1.005], dtype=np.float32)  # in kJ/kg·K
    molecular_weight_ratio_water_to_dry_air = 0.622  # dimensionless

    # Expected result calculated manually or using a known value
    expected_output = np.array([0.072168])

    # Call the function
    output = calculate_psychrometric_constant(
        atmospheric_pressure,
        latent_heat_vapourization,
        specific_heat_air,
        molecular_weight_ratio_water_to_dry_air,
    )

    # Assert that the output is as expected within a small tolerance
    np.testing.assert_allclose(output, expected_output, rtol=1e-5)


def test_check_precipitation_surface_raises_error():
    """Test check surface precipitation is positive."""

    from virtual_ecosystem.models.hydrology.hydrology_tools import (
        check_precipitation_surface,
    )

    test_array = np.array([1.0, 0.5, -0.2, 0.8])

    with pytest.raises(
        ValueError,
        match="Surface precipitation should not be negative! Consider checking that the"
        " canopy water balance is correct.",
    ):
        check_precipitation_surface(test_array)
