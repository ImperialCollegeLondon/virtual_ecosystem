"""Test microclimate.py."""

import numpy as np


def test_run_microclimate(
    dummy_climate_data_varying_canopy,
    fixture_core_components,
    fixture_core_constants,
    fixture_abiotic_constants,
    fixture_abiotic_simple_configuration,
    fixture_pyrealm_config,
):
    """Test microclimate function."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        run_microclimate,
    )

    lyr_str = fixture_core_components.layer_structure
    result = run_microclimate(
        data=dummy_climate_data_varying_canopy,
        time_index=0,
        time_interval=86400 * 30,
        month=1,
        cell_area=10000,
        layer_structure=lyr_str,
        abiotic_constants=fixture_abiotic_constants,
        core_constants=fixture_core_constants,
        pyrealm_core_constants=fixture_pyrealm_config.core,
        abiotic_bounds=fixture_abiotic_simple_configuration.bounds,
    )

    for var in [
        "canopy_temperature",
        "air_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
    ]:
        assert var in result

    # Check that values fall within a reasonable expected range
    soil_temps = result["soil_temperature"].isel(layers=lyr_str.index_all_soil)

    # To test with varying canopy layers, need to mask
    canopy_mask = ~np.isnan(
        dummy_climate_data_varying_canopy["canopy_temperature"].isel(
            layers=lyr_str.index_filled_canopy
        )
    )
    atm_mask = ~np.isnan(
        dummy_climate_data_varying_canopy["air_temperature"].isel(
            layers=lyr_str.index_filled_atmosphere
        )
    )

    canopy_temp_result = result["canopy_temperature"].isel(
        layers=lyr_str.index_filled_canopy
    )
    air_temp_result = result["air_temperature"].isel(
        layers=lyr_str.index_filled_atmosphere
    )
    rel_hum_result = result["relative_humidity"].isel(
        layers=lyr_str.index_filled_atmosphere
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
    assert ((soil_temps >= 10.0) & (soil_temps <= 30.0)).all()
    assert (
        (valid_values_can_temp_clean >= 15.0) & (valid_values_can_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_air_temp_clean >= 15.0) & (valid_values_air_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_rel_hum_clean >= 0.0) & (valid_values_rel_hum_clean <= 100.0)
    ).all()
