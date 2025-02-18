"""Test microclimate.py."""

import numpy as np

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts


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
        abiotic_simple_constants=AbioticSimpleConsts(),
        core_constants=CoreConsts(),
    )

    # exp_longwave_emission = lyr_str.from_template()
    # exp_longwave_emission[lyr_str.index_flux_layers] = np.array(
    #     [424.66886, 420.013465, 412.137266, 391.685362]
    # )[:, None]
    # np.testing.assert_allclose(
    #     result["longwave_emission"][lyr_str.index_flux_layers],
    #     exp_longwave_emission[lyr_str.index_flux_layers],
    #     rtol=1e-04,
    #     atol=1e-04,
    # )

    # exp_sens_heat = lyr_str.from_template()
    # exp_sens_heat[lyr_str.index_flux_layers] = np.array(
    #     [-67.539934, -64.089671, -58.191538, -20.43684]
    # )[:, None]
    # np.testing.assert_allclose(
    #     result["sensible_heat_flux"][lyr_str.index_flux_layers],
    #     exp_sens_heat[lyr_str.index_flux_layers],
    #     rtol=1e-04,
    #     atol=1e-04,
    # )

    # exp_lat_heat = lyr_str.from_template()
    # exp_lat_heat[lyr_str.index_flux_layers] = np.array(
    #     [
    #         [66.835395, 66.835395, 66.835395, 66.835395],
    #         [66.835395, 66.835395, 66.835395, 66.835395],
    #         [66.835395, 66.835395, 66.835395, 66.835395],
    #         [0.003342, 0.033418, 0.334177, 0.334177],
    #     ]
    # )
    # np.testing.assert_allclose(
    #     result["latent_heat_flux"],
    #     exp_lat_heat,
    #     rtol=1e-04,
    #     atol=1e-04,
    # )

    # exp_wind = lyr_str.from_template()
    # exp_wind[lyr_str.index_filled_atmosphere] = np.array(
    #     [0.727122, 0.615474, 0.001, 0.001, 0.001]
    # )[:, None]
    # np.testing.assert_allclose(
    #     result["wind_speed"],
    #     exp_wind,
    #     rtol=1e-04,
    #     atol=1e-04,
    # )

    exp_soiltemp = lyr_str.from_template()
    exp_soiltemp[lyr_str.index_all_soil] = np.array([17.357065, 19.966271])[:, None]
    np.testing.assert_allclose(
        result["soil_temperature"][lyr_str.index_all_soil],
        exp_soiltemp[lyr_str.index_all_soil],
        rtol=1e-04,
        atol=1e-04,
    )

    exp_cantemp = lyr_str.from_template()
    exp_cantemp[lyr_str.index_filled_canopy] = np.array(
        [23.023263, 22.210275, 20.819253]
    )[:, None]
    np.testing.assert_allclose(
        result["canopy_temperature"][lyr_str.index_filled_canopy],
        exp_cantemp[lyr_str.index_filled_canopy],
        rtol=1e-04,
        atol=1e-04,
    )

    exp_airtemp = lyr_str.from_template()
    exp_airtemp[lyr_str.index_filled_atmosphere] = np.array(
        [30.0, 26.322969, 25.473039, 24.019511, 19.6246]
    )[:, None]
    np.testing.assert_allclose(
        result["air_temperature"],
        exp_airtemp,
        rtol=1e-04,
        atol=1e-04,
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
        [1.41727, 1.195479, 1.170102, 1.127572, 1.088259]
    )[:, None]
    np.testing.assert_allclose(
        result["vapour_pressure"],
        exp_vp,
        rtol=1e-04,
        atol=1e-04,
    )

    exp_vpd = lyr_str.from_template()
    exp_vpd[lyr_str.index_filled_atmosphere] = np.array([0, 0, 0, 0, 0])[:, None]
    np.testing.assert_allclose(
        result["vapour_pressure_deficit"],
        exp_vpd,
        rtol=1e-04,
        atol=1e-04,
    )
