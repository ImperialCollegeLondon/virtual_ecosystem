"""Test microclimate.py."""

import numpy as np
from pyrealm.constants import CoreConst as PyrealmConst

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


# Test integration (TODO add structural and value range check)
def test_run_microclimate(dummy_climate_data, fixture_core_components):
    """Test microclimate function."""

    from virtual_ecosystem.models.abiotic.microclimate import (
        run_microclimate,
    )

    lyr_str = fixture_core_components.layer_structure
    result = run_microclimate(
        data=dummy_climate_data,
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
            [20.12272, 18.944219, 7.156909, 7.156909],
            [20.000273, 19.997652, 19.971446, 19.971446],
        ]
    )
    np.testing.assert_allclose(
        result["soil_temperature"][lyr_str.index_all_soil],
        exp_soiltemp[lyr_str.index_all_soil],
        rtol=1e-04,
        atol=1e-04,
    )

    exp_cantemp = lyr_str.from_template()
    exp_cantemp[lyr_str.index_filled_canopy] = np.array(
        [28.160042, 27.401159, 26.100414]
    )[:, None]
    np.testing.assert_allclose(
        result["canopy_temperature"][lyr_str.index_filled_canopy],
        exp_cantemp[lyr_str.index_filled_canopy],
        rtol=1e-04,
        atol=1e-04,
    )

    exp_airtemp = lyr_str.from_template()
    exp_airtemp[lyr_str.index_above_scalar] = 30.0
    exp_airtemp[lyr_str.index_filled_canopy] = np.array(
        [29.806235, 28.840201, 27.188575]
    )[:, None]
    exp_airtemp[lyr_str.index_surface_scalar] = np.array(
        [21.009713, 20.918322, 20.004237, 20.004237]
    )
    np.testing.assert_allclose(
        result["air_temperature"],
        exp_airtemp,
        rtol=1e-02,
        atol=1e-02,
    )

    exp_relhum = lyr_str.from_template()
    exp_relhum[lyr_str.index_filled_atmosphere] = np.array([100, 100, 100, 100, 100])[
        :, None
    ]
    np.testing.assert_allclose(
        result["relative_humidity"],
        exp_relhum,
        rtol=1e-04,
        atol=1e-04,
    )

    # Sensible heat flux, canopy only
    exp_shc = lyr_str.from_template()
    exp_shc[lyr_str.index_filled_canopy] = np.array(
        [-149.364835, -130.806504, -99.244963]
    )[:, None]
    exp_shc[lyr_str.index_topsoil_scalar] = np.array(
        [-95.064986, -200.811136, -1258.465378, -1258.465378]
    )
    np.testing.assert_allclose(
        result["sensible_heat_flux"],
        exp_shc,
        rtol=1e-04,
        atol=1e-04,
    )
