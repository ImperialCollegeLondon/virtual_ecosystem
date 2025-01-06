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
        time_interval=3600,
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

    exp_sens_heat = lyr_str.from_template()
    exp_sens_heat[lyr_str.index_flux_layers] = np.array(
        [-98.591399, -78.774914, -44.8992, 78.426]
    )[:, None]
    np.testing.assert_allclose(
        result["sensible_heat_flux"],
        exp_sens_heat,
        rtol=1e-04,
        atol=1e-04,
    )

    exp_lat_heat = lyr_str.from_template()
    exp_lat_heat[lyr_str.index_flux_layers] = np.array(
        [
            [66.835395, 66.835395, 66.835395, 66.835395],
            [66.835395, 66.835395, 66.835395, 66.835395],
            [66.835395, 66.835395, 66.835395, 66.835395],
            [0.003342, 0.033418, 0.334177, 0.334177],
        ]
    )
    np.testing.assert_allclose(
        result["latent_heat_flux"],
        exp_lat_heat,
        rtol=1e-04,
        atol=1e-04,
    )

    exp_wind = lyr_str.from_template()
    exp_wind[lyr_str.index_filled_atmosphere] = np.array(
        [0.727122, 0.615474, 0.001, 0.001, 0.001]
    )[:, None]
    np.testing.assert_allclose(
        result["wind_speed"],
        exp_wind,
        rtol=1e-04,
        atol=1e-04,
    )
