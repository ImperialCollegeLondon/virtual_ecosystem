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
            [27.223404, 27.296955, 27.407225, 27.407225],
            [28.871276, 28.871276, np.nan, np.nan],
            [27.206485, np.nan, np.nan, np.nan],
        ]
    )
    np.testing.assert_allclose(
        result["canopy_temperature"][lyr_str.index_filled_canopy],
        exp_cantemp[lyr_str.index_filled_canopy],
        rtol=1e-02,
        atol=1e-02,
    )

    # Check that all air temperature values fall within a reasonable expected range
    # mask = np.isnan(
    #     dummy_climate_data_varying_canopy["air_temperature"][
    #         lyr_str.index_filled_atmosphere
    #     ]
    # )
    # air_temp_result = result["air_temperature"][lyr_str.index_filled_atmosphere]
    # assert np.all((air_temp_result[~mask] >= 16.0) & (air_temp_result[~mask] <= 36.0))

    print(result["air_temperature"])
    # np.array([[30.00023402, 30.00024546,         nan,         nan],
    #    [29.83391357, 29.83371163,         nan,         nan],
    #    [28.88179021,         nan,         nan,         nan],
    #    [27.21446276,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [21.10594219, 21.07185157, 20.73094533, 20.73094533],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    # ]
    # )

    exp_relhum = lyr_str.from_template()
    exp_relhum[lyr_str.index_filled_atmosphere] = np.array(
        [
            [100, 100, np.nan, np.nan],
            [100, 100, np.nan, np.nan],
            [100, np.nan, np.nan, np.nan],
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
    print(result["air_temperature"])
    # np.array([[29.98536857, 29.99051257,         nan,         nan],
    #    [33.7172163 , 31.35657893,         nan,         nan],
    #    [34.28084653,         nan,         nan,         nan],
    #    [32.64513234,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [21.87141268, 21.73480416, 20.36795001, 20.36795001],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan]])

    # Check that all air temperature values fall within a reasonable expected range
    air_temp_result = result["air_temperature"][lyr_str.index_filled_atmosphere]
    assert np.all((air_temp_result >= 16.0) & (air_temp_result <= 36.0))


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
    print(result["air_temperature"])
    # np.array([[30.00164585, 30.00056018,         nan,         nan],
    #    [28.8318953 , 29.62049735,         nan,         nan],
    #    [21.30954266,         nan,         nan,         nan],
    #    [19.59780849,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan],
    #    [21.10594219, 21.07185157, 20.73094533, 20.73094533],
    #    [        nan,         nan,         nan,         nan],
    #    [        nan,         nan,         nan,         nan]])
    # Check that all air temperature values fall within a reasonable expected range
    air_temp_result = result["air_temperature"][lyr_str.index_filled_atmosphere]
    assert np.all((air_temp_result >= 16.0) & (air_temp_result <= 36.0))
