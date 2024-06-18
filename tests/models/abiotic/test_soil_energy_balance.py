"""Test module for abiotic.abiotic_model.energy_balance.py."""

import numpy as np
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_calculate_soil_absorption():
    """Test that soil absorption is calculated correctly."""

    from virtual_ecosystem.models.abiotic.soil_energy_balance import (
        calculate_soil_absorption,
    )

    result = calculate_soil_absorption(
        shortwave_radiation_surface=np.array([100, 10, 0]),
        surface_albedo=np.array([0.2, 0.2, 0.2]),
    )

    np.testing.assert_allclose(result, np.array([80, 8, 0]), rtol=1e-04, atol=1e-04)


def test_calculate_sensible_heat_flux_soil():
    """Test sensible heat from soil is calculated correctly."""

    from virtual_ecosystem.models.abiotic.soil_energy_balance import (
        calculate_sensible_heat_flux_soil,
    )

    result = calculate_sensible_heat_flux_soil(
        air_temperature_surface=np.array([290, 290, 290]),
        topsoil_temperature=np.array([295, 290, 285]),
        molar_density_air=np.array([38, 38, 38]),
        specific_heat_air=np.array([29, 29, 29]),
        aerodynamic_resistance=np.array([1250.0, 1250.0, 1250.0]),
    )
    np.testing.assert_allclose(
        result,
        np.array([4.408, 0.0, -4.408]),
        rtol=1e-04,
        atol=1e-04,
    )


def test_calculate_latent_heat_flux_from_soil_evaporation():
    """Test evaporation to latent heat flux conversion works correctly."""

    from virtual_ecosystem.models.abiotic.soil_energy_balance import (
        calculate_latent_heat_flux_from_soil_evaporation,
    )

    result = calculate_latent_heat_flux_from_soil_evaporation(
        soil_evaporation=np.array([0.001, 0.01, 0.1]),
        latent_heat_vapourisation=np.array([2254.0, 2254.0, 2254.0]),
    )
    np.testing.assert_allclose(result, np.array([2.254, 22.54, 225.4]))


def test_update_surface_temperature():
    """Test surface temperature with positive and negative radiation flux."""

    from virtual_ecosystem.models.abiotic.soil_energy_balance import (
        update_surface_temperature,
    )

    result = update_surface_temperature(
        topsoil_temperature=np.array([297, 297, 297]),
        surface_net_radiation=np.array([100, 0, -100]),
        surface_layer_depth=np.array([0.1, 0.1, 0.1]),
        grid_cell_area=100,
        update_interval=43200,
        specific_heat_capacity_soil=AbioticConsts.specific_heat_capacity_soil,
        volume_to_weight_conversion=1000.0,
    )

    np.testing.assert_allclose(result, np.array([297.00016, 297.0, 296.99984]))


def test_calculate_ground_heat_flux():
    """Test graound heat flux is calculated correctly."""

    from virtual_ecosystem.models.abiotic.soil_energy_balance import (
        calculate_ground_heat_flux,
    )

    result = calculate_ground_heat_flux(
        soil_absorbed_radiation=np.array([100, 50, 0]),
        topsoil_longwave_emission=np.array([10, 10, 10]),
        topsoil_sensible_heat_flux=np.array([10, 10, 10]),
        topsoil_latent_heat_flux=np.array([10, 10, 10]),
    )
    np.testing.assert_allclose(result, np.array([70, 20, -30]))


def test_calculate_soil_heat_balance(dummy_climate_data):
    """Test full surface heat balance is run correctly."""

    from virtual_ecosystem.models.abiotic.soil_energy_balance import (
        calculate_soil_heat_balance,
    )

    data = dummy_climate_data
    data["soil_evaporation"] = DataArray(
        np.array([0.001, 0.01, 0.1, 0.1]), dims="cell_id"
    )
    data["molar_density_air"] = DataArray(
        np.full((14, 4), 38), dims=["layers", "cell_id"]
    )
    data["specific_heat_air"] = DataArray(
        np.full((14, 4), 29), dims=["layers", "cell_id"]
    )
    data["aerodynamic_resistance_surface"] = DataArray(np.repeat(1250.0, 4))
    data["latent_heat_vapourisation"] = DataArray(
        np.full((14, 4), 2254.0), dims=["layers", "cell_id"]
    )

    result = calculate_soil_heat_balance(
        data=data,
        time_index=0,
        topsoil_layer_index=11,
        update_interval=43200,
        abiotic_consts=AbioticConsts,
        core_consts=CoreConsts,
    )

    # Check if all variables were created
    var_list = [
        "soil_absorption",
        "longwave_emission_soil",
        "sensible_heat_flux_soil",
        "latent_heat_flux_soil",
        "ground_heat_flux",
    ]

    variables = [var for var in result if var not in var_list]
    assert variables

    test_values = {
        "soil_absorption": np.repeat(79.625, 4),
        "longwave_emission_soil": np.repeat(0.007258, 4),
        "sensible_heat_flux_soil": np.repeat(3.397735, 4),
        "latent_heat_flux_soil": np.array([2.254, 22.54, 225.4, 225.4]),
        "ground_heat_flux": np.array([73.966007, 53.680007, -149.179993, -149.179993]),
    }

    for var, values in test_values.items():
        assert np.allclose(result[var], values, rtol=1e-04, atol=1e-04)
