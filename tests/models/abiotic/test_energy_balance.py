"""Test module for abiotic.energy_balance.py."""

import numpy as np
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_initialise_absorbed_radiation(dummy_climate_data):
    """Test initial absorbed radiation has correct dimensions."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_absorbed_radiation,
    )

    d = dummy_climate_data
    leaf_area_index_true = d["leaf_area_index"][
        d["leaf_area_index"]["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    layer_heights_canopy = d["layer_heights"][
        d["leaf_area_index"]["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")

    result = initialise_absorbed_radiation(
        topofcanopy_radiation=d["topofcanopy_radiation"].isel(time_index=0).to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.to_numpy(),
        light_extinction_coefficient=0.01,
    )

    exp_result = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_initialise_canopy_temperature(dummy_climate_data):
    """Test that canopy temperature is initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_temperature,
    )

    d = dummy_climate_data
    air_temperature = d["air_temperature"][
        d["leaf_area_index"]["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    absorbed_radiation = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])

    result = initialise_canopy_temperature(
        air_temperature=air_temperature,
        absorbed_radiation=absorbed_radiation,
        canopy_temperature_ini_factor=0.01,
    )
    exp_result = np.array([[29.845994] * 4, [28.872169] * 4, [27.207403] * 4])

    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_slope_of_saturated_pressure_curve():
    """Test calculation of slope of saturated pressure curve."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_slope_of_saturated_pressure_curve,
    )

    const = AbioticConsts()
    result = calculate_slope_of_saturated_pressure_curve(
        temperature=np.full((4, 3), 20.0),
        saturated_pressure_slope_parameters=const.saturated_pressure_slope_parameters,
    )
    exp_result = np.full((4, 3), 0.14474)
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_initialise_canopy_and_soil_fluxes(dummy_climate_data):
    """Test that canopy and soil fluxes initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_and_soil_fluxes,
    )

    true_canopy_indexes = (
        dummy_climate_data["leaf_area_index"][
            dummy_climate_data["leaf_area_index"]["layer_roles"] == "canopy"
        ]
        .dropna(dim="layers", how="all")
        .indexes["layers"]
    )
    result = initialise_canopy_and_soil_fluxes(
        air_temperature=dummy_climate_data["air_temperature"],
        topofcanopy_radiation=(
            dummy_climate_data["topofcanopy_radiation"].isel(time_index=0)
        ),
        leaf_area_index=dummy_climate_data["leaf_area_index"],
        layer_heights=dummy_climate_data["layer_heights"],
        true_canopy_indexes=true_canopy_indexes,
        topsoil_layer_index=13,
        light_extinction_coefficient=0.01,
        canopy_temperature_ini_factor=0.01,
    )

    exp_abs = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])

    for var in [
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "canopy_absorption",
    ]:
        assert var in result

    np.testing.assert_allclose(
        result["canopy_absorption"][1:4].to_numpy(), exp_abs, rtol=1e-04, atol=1e-04
    )
    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        np.testing.assert_allclose(result[var][1:4].to_numpy(), np.zeros((3, 4)))
        np.testing.assert_allclose(result[var][13].to_numpy(), np.zeros(4))


def test_calculate_longwave_emission():
    """Test that longwave radiation is calculated correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_longwave_emission,
    )

    result = calculate_longwave_emission(
        temperature=np.repeat(290.0, 3),
        emissivity=AbioticConsts.soil_emissivity,
        stefan_boltzmann=CoreConsts.stefan_boltzmann_constant,
    )
    np.testing.assert_allclose(result, np.repeat(320.84384, 3), rtol=1e-04, atol=1e-04)


def test_calculate_leaf_and_air_temperature(
    fixture_core_components,
    dummy_climate_data,
):
    """Test updating leaf and air temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_leaf_and_air_temperature,
    )
    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts

    layer_structure = fixture_core_components.layer_structure

    true_canopy_indexes = [1, 2, 3]
    result = calculate_leaf_and_air_temperature(
        data=dummy_climate_data,
        time_index=1,
        topsoil_layer_index=13,
        true_canopy_indexes=true_canopy_indexes,
        true_canopy_layers_n=3,
        layer_structure=layer_structure,
        abiotic_constants=AbioticConsts(),
        abiotic_simple_constants=AbioticSimpleConsts(),
        core_constants=CoreConsts(),
    )

    exp_air_temp = layer_structure.from_template()
    t_vals = [30.0, 29.999969, 29.995439, 28.796977, 21.319547, 20.08797]
    exp_air_temp.T[..., [0, 1, 2, 3, 11, 12]] = t_vals

    exp_leaf_temp = layer_structure.from_template()
    tl_vals = [30.078613, 29.091601, 26.951191]
    exp_leaf_temp.T[..., [1, 2, 3]] = tl_vals

    exp_vp = layer_structure.from_template()
    vp_vals = [0.14, 0.140323, 0.18372, 1.296359, 0.203754, 0.023795]
    exp_vp.T[..., [0, 1, 2, 3, 11, 12]] = vp_vals

    exp_vpd = layer_structure.from_template()
    vpd_vals = [0.098781, 0.099009, 0.129644, 0.94264, 0.179767, 0.021697]
    exp_vpd.T[..., [0, 1, 2, 3, 11, 12]] = vpd_vals

    exp_gv = layer_structure.from_template()
    gv_vals = [0.203513, 0.202959, 0.202009]
    exp_gv.T[..., [1, 2, 3]] = gv_vals

    exp_sens_heat = layer_structure.from_template()
    sens_heat_vals = [0.0, 1.397746, 1.315211, -1.515519, 1.0]
    exp_sens_heat.T[..., [0, 1, 2, 3, 13]] = sens_heat_vals

    exp_latent_heat = layer_structure.from_template()
    lat_heat_vals = [0.0, 8.330748, 8.426556, 11.740824, 1.0]
    exp_latent_heat.T[..., [0, 1, 2, 3, 13]] = lat_heat_vals

    np.testing.assert_allclose(
        result["air_temperature"], exp_air_temp, rtol=1e-03, atol=1e-03
    )
    np.testing.assert_allclose(
        result["canopy_temperature"], exp_leaf_temp, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["vapour_pressure"], exp_vp, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["vapour_pressure_deficit"], exp_vpd, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_vapour_conductivity"], exp_gv, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["sensible_heat_flux"], exp_sens_heat, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["latent_heat_flux"][1:4], exp_latent_heat[1:4], rtol=1e-04, atol=1e-04
    )


def test_leaf_and_air_temperature_linearisation(dummy_climate_data):
    """Test linearisation of air and leaf temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        leaf_and_air_temperature_linearisation,
    )

    leaf_area_index = dummy_climate_data["leaf_area_index"]
    true_canopy_layers_indexes = (
        leaf_area_index[leaf_area_index["layer_roles"] == "canopy"]
        .dropna(dim="layers", how="all")
        .indexes["layers"]
    )
    a_A, b_A = leaf_and_air_temperature_linearisation(
        conductivity_from_ref_height=(
            dummy_climate_data["conductivity_from_ref_height"][
                true_canopy_layers_indexes
            ]
        ),
        conductivity_from_soil=np.repeat(0.1, 4),
        leaf_air_heat_conductivity=(
            dummy_climate_data["leaf_air_heat_conductivity"][true_canopy_layers_indexes]
        ),
        air_temperature_ref=(
            dummy_climate_data["air_temperature_ref"].isel(time_index=0).to_numpy()
        ),
        top_soil_temperature=dummy_climate_data["soil_temperature"][13].to_numpy(),
    )

    exp_a = np.array([[29.677419, 29.677419, 29.677419, 29.677419]] * 3)
    exp_b = np.array([[0.04193548, 0.04193548, 0.04193548, 0.04193548]] * 3)
    np.testing.assert_allclose(a_A, exp_a)
    np.testing.assert_allclose(b_A, exp_b)


def test_longwave_radiation_flux_linearisation():
    """Test linearisation of longwave radiation fluxes."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        longwave_radiation_flux_linearisation,
    )

    a_R, b_R = longwave_radiation_flux_linearisation(
        a_A=np.array([[29.677419, 29.677419, 29.677419]] * 3),
        b_A=np.array([[0.04193548, 0.04193548, 0.04193548]] * 3),
        air_temperature_ref=np.full((3, 3), 30.0),
        leaf_emissivity=0.8,
        stefan_boltzmann_constant=CoreConsts.stefan_boltzmann_constant,
    )

    exp_a = np.array([[0.035189, 0.035189, 0.035189]] * 3)
    exp_b = np.array([[0.005098, 0.005098, 0.005098]] * 3)
    np.testing.assert_allclose(a_R, exp_a, rtol=1e-04, atol=1e-04)
    np.testing.assert_allclose(b_R, exp_b, rtol=1e-04, atol=1e-04)


def test_vapour_pressure_linearisation():
    """Test linearisation of vapour pressure."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        vapour_pressure_linearisation,
    )

    a_E, b_E = vapour_pressure_linearisation(
        vapour_pressure_ref=np.full((3, 3), 0.14),
        saturated_vapour_pressure_ref=np.full((3, 3), 0.5),
        soil_vapour_pressure=np.full((3, 3), 0.14),
        conductivity_from_soil=np.repeat(0.1, 3),
        leaf_vapour_conductivity=np.full((3, 3), 0.2),
        conductivity_from_ref_height=np.full((3, 3), 3),
        delta_v_ref=np.full((3, 3), 0.14474),
    )

    exp_a = np.array([[0.161818, 0.161818, 0.161818]] * 3)
    exp_b = np.array([[0.043861, 0.043861, 0.043861]] * 3)
    np.testing.assert_allclose(a_E, exp_a, rtol=1e-04, atol=1e-04)
    np.testing.assert_allclose(b_E, exp_b, rtol=1e-04, atol=1e-04)


def test_latent_heat_flux_linearisation():
    """Test latent heat flux linearisation."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        latent_heat_flux_linearisation,
    )

    a_L, b_L = latent_heat_flux_linearisation(
        latent_heat_vapourisation=np.full((3, 3), 2245.0),
        leaf_vapour_conductivity=np.full((3, 3), 0.2),
        atmospheric_pressure_ref=np.repeat(96.0, 3),
        saturated_vapour_pressure_ref=np.full((3, 3), 0.5),
        a_E=np.array([[0.161818, 0.161818, 0.161818]] * 3),
        b_E=np.array([[0.043861, 0.043861, 0.043861]] * 3),
        delta_v_ref=np.full((3, 3), 0.14474),
    )

    exp_a = np.array([[13.830078, 13.830078, 13.830078]] * 3)
    exp_b = np.array([[46.3633, 46.3633, 46.3633]] * 3)
    np.testing.assert_allclose(a_L, exp_a, rtol=1e-04, atol=1e-04)
    np.testing.assert_allclose(b_L, exp_b, rtol=1e-04, atol=1e-04)


def test_calculate_delta_canopy_temperature():
    """Test calculate delta canopy temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_delta_canopy_temperature,
    )

    delta_t = calculate_delta_canopy_temperature(
        absorbed_radiation=np.full((3, 3), 10),
        a_R=np.array([[0.035189, 0.035189, 0.035189]] * 3),
        a_L=np.array([[13.830078, 13.830078, 13.830078]] * 3),
        b_R=np.array([[0.005098, 0.005098, 0.005098]] * 3),
        b_L=np.array([[46.3633, 46.3633, 46.3633]] * 3),
        b_H=np.array([[46.3633, 46.3633, 46.3633]] * 3),
    )

    exp_delta_t = np.array([[-0.041238, -0.041238, -0.041238]] * 3)
    np.testing.assert_allclose(delta_t, exp_delta_t, rtol=1e-04, atol=1e-04)
