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
        time_interval=3600,
        cell_area=10000,
        layer_structure=lyr_str,
        abiotic_constants=AbioticConsts(),
        core_constants=CoreConsts(),
        pyrealm_const=PyrealmConst(),
    )

    exp_soiltemp = lyr_str.from_template()
    exp_soiltemp[lyr_str.index_all_soil] = np.array([18.411252, 19.973347])[:, None]
    np.testing.assert_allclose(
        result["soil_temperature"][lyr_str.index_all_soil],
        exp_soiltemp[lyr_str.index_all_soil],
        rtol=1e-04,
        atol=1e-04,
    )

    exp_cantemp = lyr_str.from_template()
    exp_cantemp[lyr_str.index_filled_canopy] = np.array(
        [24.102749, 24.194221, 24.350592]
    )[:, None]
    np.testing.assert_allclose(
        result["canopy_temperature"][lyr_str.index_filled_canopy],
        exp_cantemp[lyr_str.index_filled_canopy],
        rtol=1e-04,
        atol=1e-04,
    )

    exp_airtemp = lyr_str.from_template()
    exp_airtemp[lyr_str.index_filled_atmosphere] = np.array(
        [30.0, 29.844655, 28.870898, 27.20625, 21.054269]
    )[:, None]
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

    exp_vp = lyr_str.from_template()
    exp_vp[lyr_str.index_filled_atmosphere] = np.array(
        [4.233724, 4.196183, 3.966909, 3.60022, 2.503226]
    )[:, None]
    np.testing.assert_allclose(
        result["vapour_pressure"], exp_vp, rtol=1e-04, atol=1e-04
    )

    exp_vpd = lyr_str.from_template()
    exp_vpd[lyr_str.index_filled_atmosphere] = np.array([0, 0, 0, 0, 0])[:, None]
    np.testing.assert_allclose(
        result["vapour_pressure_deficit"],
        exp_vpd,
        rtol=1e-04,
        atol=1e-04,
    )

    # Sensible heat flux, canopy only
    exp_shc = lyr_str.from_template()
    exp_shc[lyr_str.index_flux_layers] = np.array(
        [-441.691753, -352.913442, -201.145903, -104.469552]
    )[:, None]
    np.testing.assert_allclose(
        result["sensible_heat_flux"],
        exp_shc,
        rtol=1e-04,
        atol=1e-04,
    )
