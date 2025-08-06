"""Test microclimate.py."""

import numpy as np
from pyrealm.constants import CoreConst as PyrealmConst

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


# Test integration (TODO add structural and value range check)
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
    )

    for var in [
        "canopy_temperature",
        "air_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
    ]:
        assert var in result

    exp_soiltemp = lyr_str.from_template()
    exp_soiltemp[lyr_str.index_all_soil] = np.array(
        [
            [21.095, 21.053, 20.627, 20.627],
            [20.018, 20.017, 20.010, 20.010],
        ]
    )
    np.testing.assert_allclose(
        result["soil_temperature"][lyr_str.index_all_soil],
        exp_soiltemp[lyr_str.index_all_soil],
        rtol=1e-02,
        atol=1e-02,
    )

    exp_cantemp = lyr_str.from_template()
    exp_cantemp[lyr_str.index_filled_canopy] = np.array(
        [
            [29.610504, 29.622654, 29.639607, 29.639607],
            [28.871156, 28.871156, np.nan, np.nan],
            [27.206382, np.nan, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(
        result["canopy_temperature"][lyr_str.index_filled_canopy],
        exp_cantemp[lyr_str.index_filled_canopy],
        rtol=1e-02,
        atol=1e-02,
    )

    # Check that all air temperature values fall within a reasonable expected range
    air_temp_result = result["air_temperature"].isel(
        layers=lyr_str.index_filled_atmosphere
    )

    mask = ~np.isnan(
        dummy_climate_data_varying_canopy["air_temperature"].isel(
            layers=lyr_str.index_filled_atmosphere
        )
    )

    # Use the mask as a DataArray for .where()
    valid_values = air_temp_result.where(mask)

    # Now drop the NaNs (i.e., masked values)
    valid_values_clean = valid_values.dropna(
        dim="layers", how="any"
    )  # or "all" if you're doing 2D

    # Now do the test
    assert ((valid_values_clean >= 16.0) & (valid_values_clean <= 36.0)).all()

    exp_relhum = lyr_str.from_template()
    exp_relhum[lyr_str.index_filled_atmosphere] = np.array(
        [
            [0, 0, 0, 0],
            [100, 100, 100, 100],
            [100, 100, np.nan, np.nan],
            [-6026.23241652, np.nan, np.nan, np.nan],  # TODO
            [100, 100, 100, 100],
        ]
    )
    np.testing.assert_allclose(
        result["relative_humidity"],
        exp_relhum,
        rtol=1e-02,
        atol=1e-02,
    )


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
    result = run_microclimate(
        data=dummy_climate_data_varying_canopy,
        time_index=0,
        time_interval=3600 * 4,
        cell_area=10000,
        layer_structure=lyr_str,
        abiotic_constants=AbioticConsts(),
        core_constants=CoreConsts(),
        pyrealm_const=PyrealmConst(),
    )

    for var in [
        "canopy_temperature",
        "air_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
    ]:
        assert var in result

    exp_soiltemp = lyr_str.from_template()
    exp_soiltemp[lyr_str.index_all_soil] = np.array(
        [
            [21.183763, 21.243605, 21.838676, 21.838676],
            [20.084981, 20.084812, 20.083032, 20.083032],
        ]
    )
    np.testing.assert_allclose(
        result["soil_temperature"][lyr_str.index_all_soil],
        exp_soiltemp[lyr_str.index_all_soil],
        rtol=1e-02,
        atol=1e-02,
    )

    exp_cantemp = lyr_str.from_template()
    exp_cantemp[lyr_str.index_filled_canopy] = np.array(
        [
            [-77.485154, -64.989835, -70.259562, -70.212418],  # TODO Newton
            [30.197086, 29.538892, np.nan, np.nan],
            [28.556955, np.nan, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(
        result["canopy_temperature"][lyr_str.index_filled_canopy],
        exp_cantemp[lyr_str.index_filled_canopy],
        rtol=1e-02,
        atol=1e-02,
    )

    # Check that all air temperature values fall within a reasonable expected range
    air_temp_result = result["air_temperature"].isel(
        layers=lyr_str.index_filled_atmosphere
    )

    mask = ~np.isnan(
        dummy_climate_data_varying_canopy["air_temperature"].isel(
            layers=lyr_str.index_filled_atmosphere
        )
    )

    # Use the mask as a DataArray for .where()
    valid_values = air_temp_result.where(mask)

    # Now drop the NaNs (i.e., masked values)
    valid_values_clean = valid_values.dropna(
        dim="layers", how="any"
    )  # or "all" if you're doing 2D

    # Now do the test  # TODO Newton
    assert ((valid_values_clean >= 16.0) & (valid_values_clean <= 36.0)).all()

    exp_relhum = lyr_str.from_template()
    exp_relhum[lyr_str.index_filled_atmosphere] = np.array(
        [
            [0, 0, 0, 0],
            [100, 100, 14.183972, -12.672991],  # TODO Newton
            [100, 100, np.nan, np.nan],
            [100, np.nan, np.nan, np.nan],
            [100, 100, 100, 100],
        ]
    )
    np.testing.assert_allclose(
        result["relative_humidity"],
        exp_relhum,
        rtol=1e-02,
        atol=1e-02,
    )


def test_run_microclimate_minutes(
    dummy_climate_data_varying_canopy, fixture_core_components
):
    """Test microclimate function iterates once for <1h time interval."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        run_microclimate,
    )

    lyr_str = fixture_core_components.layer_structure
    result = run_microclimate(
        data=dummy_climate_data_varying_canopy,
        time_index=0,
        time_interval=60,
        cell_area=10000,
        layer_structure=lyr_str,
        abiotic_constants=AbioticConsts(),
        core_constants=CoreConsts(),
        pyrealm_const=PyrealmConst(),
    )

    exp_cantemp = lyr_str.from_template()
    exp_cantemp[lyr_str.index_filled_canopy] = np.array(
        [
            [-402.04104199, -382.55823063, -354.81732085, -354.81732085],  # TODO Newton
            [28.85334069, 28.85334069, np.nan, np.nan],
            [27.18862662, np.nan, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(
        result["canopy_temperature"][lyr_str.index_filled_canopy],
        exp_cantemp[lyr_str.index_filled_canopy],
        rtol=1e-02,
        atol=1e-02,
    )

    # Check that all air temperature values fall within a reasonable expected range
    air_temp_result = result["air_temperature"].isel(
        layers=lyr_str.index_filled_atmosphere
    )

    mask = ~np.isnan(
        dummy_climate_data_varying_canopy["air_temperature"].isel(
            layers=lyr_str.index_filled_atmosphere
        )
    )

    # Use the mask as a DataArray for .where()
    valid_values = air_temp_result.where(mask)

    # Now drop the NaNs (i.e., masked values)
    valid_values_clean = valid_values.dropna(
        dim="layers", how="any"
    )  # or "all" if you're doing 2D

    # Now do the test
    assert ((valid_values_clean >= 16.0) & (valid_values_clean <= 36.0)).all()
