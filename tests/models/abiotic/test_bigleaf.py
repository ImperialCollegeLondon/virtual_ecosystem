"""Test bigleaf module."""

import numpy as np

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
from virtual_ecosystem.models.hydrology.constants import HydroConsts


def test_bigleaf(dummy_climate_data, fixture_core_components):
    """Test bigleaf model."""

    from virtual_ecosystem.models.abiotic.bigleaf import bigleaf

    data = dummy_climate_data
    timestep = {
        "year": 2024,
        "month": 10,
        "day": 16,
        "hour": 12,
    }

    latitude = np.array([5.0, 5.1, 5.2, 5.3])
    longitude = np.repeat(102.0, 4)
    slope = np.array([5.0, 10.0, 5.0, 10.0])
    aspect = np.array([0.0, 180.0, 0.0, 180.0])

    core_constants = CoreConsts()
    abiotic_constants = AbioticConsts()
    abiotic_simple_constants = AbioticSimpleConsts()
    hydro_constants = HydroConsts()
    layer_structure = fixture_core_components.layer_structure

    # Expected result
    expected_output = {
        "canopy_temperature": np.array([26.161933, 26.189558, 26.161933, 26.189558]),
        "ground_temperature": np.array([23.570943, 23.602405, 23.570943, 23.602405]),
        "sensible_heat_flux": np.array(
            [-283.829567, -281.20334, -283.848943, -281.176712]
        ),
        "ground_heat_flux": np.array([0.0, 0.0, 0.0, 0.0]),
        "net_radiation": np.array([-182.354931, -174.56186, -182.354931, -174.56186]),
        "psih": np.array([-4.553863e-12, -4.512036e-12, -4.553863e-12, -4.512036e-12]),
        "psim": np.array([-3.502971e-12, -3.470797e-12, -3.502971e-12, -3.470797e-12]),
        "phih": np.array([1.0, 1.0, 1.0, 1.0]),
        "monin_obukov_length": np.array(
            [1.416422e13, 1.429552e13, 1.416422e13, 1.429552e13]
        ),
        "friction_velocity": np.array([0.550454, 0.550454, 0.550454, 0.550454]),
        "albedo": np.array([0.210373, 0.183297, 0.210373, 0.183297]),
        "canopy_shortwave_absorption": np.array(
            [236.887959, 245.01088, 236.887959, 245.01088]
        ),
        "ground_shortwave_absorption": np.array(
            [47.898979, 54.152699, 47.898979, 54.152699]
        ),
    }

    # Run the function
    output = bigleaf(
        data=data,
        timestep=timestep,
        time_index=0,
        latitude=latitude,
        longitude=longitude,
        slope=slope,
        aspect=aspect,
        core_constants=core_constants,
        abiotic_constants=abiotic_constants,
        abiotic_simple_constants=abiotic_simple_constants,
        hydro_constants=hydro_constants,
        layer_structure=layer_structure,
    )

    # Compare results
    for var in expected_output:
        np.testing.assert_allclose(output[var], expected_output[var], rtol=1e-4)
