"""Test microclimate.py."""

import numpy as np
from pyrealm.constants import CoreConst as PyrealmConst

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleBounds


def test_run_microclimate(dummy_climate_data_varying_canopy, fixture_core_components):
    """Test microclimate function."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        run_microclimate,
    )

    lyr_str = fixture_core_components.layer_structure
    result = run_microclimate(
        data=dummy_climate_data_varying_canopy,
        time_index=0,
        time_interval=86400 * 30,
        cell_area=10000,
        layer_structure=lyr_str,
        abiotic_constants=AbioticConsts(),
        core_constants=CoreConsts(),
        pyrealm_const=PyrealmConst(),
        abiotic_bounds=AbioticSimpleBounds(),
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
    assert ((soil_temps >= 18.0) & (soil_temps <= 25.0)).all()
    assert (
        (valid_values_can_temp_clean >= 15.0) & (valid_values_can_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_air_temp_clean >= 15.0) & (valid_values_air_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_rel_hum_clean >= 0.0) & (valid_values_rel_hum_clean <= 100.0)
    ).all()


def test_run_microclimate_subdaily(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test microclimate function iterates over hours - no time index."""

    # TODO this test returns different results on windows machines (around 1.5 K),
    # likely because of differences in rounding digits.
    from virtual_ecosystem.models.abiotic.microclimate import (
        run_microclimate,
    )

    lyr_str = fixture_core_components.layer_structure

    # Adjust input data to more realistsic values over this time scale
    dummy_climate_data_varying_canopy["canopy_evaporation"] = (
        dummy_climate_data_varying_canopy["canopy_evaporation"] / 86400 * 3600
    )
    dummy_climate_data_varying_canopy["transpiration"] = (
        dummy_climate_data_varying_canopy["transpiration"] / 86400 * 3600
    )
    result = run_microclimate(
        data=dummy_climate_data_varying_canopy,
        time_index=0,
        time_interval=3600 * 4,
        cell_area=10000,
        layer_structure=lyr_str,
        abiotic_constants=AbioticConsts(),
        core_constants=CoreConsts(),
        pyrealm_const=PyrealmConst(),
        abiotic_bounds=AbioticSimpleBounds(),
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
    assert ((soil_temps >= 18.0) & (soil_temps <= 25.0)).all()
    assert (
        (valid_values_can_temp_clean >= 15.0) & (valid_values_can_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_air_temp_clean >= 15.0) & (valid_values_air_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_rel_hum_clean >= 0.0) & (valid_values_rel_hum_clean <= 100.0)
    ).all()


def test_run_microclimate_minutes(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test microclimate function iterates once for <1h time interval."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        run_microclimate,
    )

    lyr_str = fixture_core_components.layer_structure
    # Adjust input data to more realistsic values over this time scale
    dummy_climate_data_varying_canopy["canopy_evaporation"] = (
        dummy_climate_data_varying_canopy["canopy_evaporation"] / 86400 * 60
    )
    dummy_climate_data_varying_canopy["transpiration"] = (
        dummy_climate_data_varying_canopy["transpiration"] / 86400 * 60
    )

    result = run_microclimate(
        data=dummy_climate_data_varying_canopy,
        time_index=0,
        time_interval=60,
        cell_area=10000,
        layer_structure=lyr_str,
        abiotic_constants=AbioticConsts(),
        core_constants=CoreConsts(),
        pyrealm_const=PyrealmConst(),
        abiotic_bounds=AbioticSimpleBounds(),
    )

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
    assert ((soil_temps >= 18.0) & (soil_temps <= 25.0)).all()
    assert (
        (valid_values_can_temp_clean >= 15.0) & (valid_values_can_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_air_temp_clean >= 15.0) & (valid_values_air_temp_clean <= 40.0)
    ).all()
    assert (
        (valid_values_rel_hum_clean >= 0.0) & (valid_values_rel_hum_clean <= 100.0)
    ).all()
