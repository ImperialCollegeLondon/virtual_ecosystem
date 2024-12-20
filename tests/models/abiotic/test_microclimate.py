"""Test microclimate.py."""

import numpy as np

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
        layer_structure=lyr_str,
        abiotic_constants=AbioticConsts(),
        core_constants=CoreConsts(),
    )

    exp_longwave_emission = lyr_str.from_template()
    exp_longwave_emission[lyr_str.index_flux_layers] = np.array(
        [434.633028, 434.633028, 434.633028, 406.202942]
    )[:, None]
    np.testing.assert_allclose(
        result["longwave_emission"],
        exp_longwave_emission,
        rtol=1e-04,
        atol=1e-04,
    )

    # exp_sens_heat = lyr_str.from_template()
    # exp_sens_heat[lyr_str.index_flux_layers] = np.array(
    #     [251.779542, 252.753367, 254.418132, 209.153685]
    # )[:, None]
    # np.testing.assert_allclose(
    #     result["sensible_heat_flux"],
    #     exp_sens_heat,
    #     rtol=1e-04,
    #     atol=1e-04,
    # )

    # exp_lat_heat = lyr_str.from_template()  # TODO uneven results in soil
    # exp_lat_heat[lyr_str.index_flux_layers] = np.array(
    #     [5.646972e-01, 5.646972e-01, 5.646972e-01, 2.823486e-05]
    # )[:, None]
    # np.testing.assert_allclose(
    #     result["latent_heat_flux"][12],
    #     exp_lat_heat[12],
    #     rtol=1e-04,
    #     atol=1e-04,
    # )

    exp_wind = lyr_str.from_template()
    exp_wind[lyr_str.index_filled_atmosphere] = np.array(
        [0.694646, 0.587985, 0.001, 0.001, 0.001]
    )[:, None]
    np.testing.assert_allclose(
        result["wind_speed"],
        exp_wind,
        rtol=1e-04,
        atol=1e-04,
    )
