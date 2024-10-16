"""Test module for abiotic.energy_balance.py."""

import numpy as np

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def test_initialise_absorbed_radiation(dummy_climate_data, fixture_core_components):
    """Test initial absorbed radiation has correct dimensions."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_absorbed_radiation,
    )

    lyr_strct = fixture_core_components.layer_structure

    leaf_area_index_true = dummy_climate_data["leaf_area_index"][
        lyr_strct.index_filled_canopy
    ]
    layer_heights_canopy = dummy_climate_data["layer_heights"][
        lyr_strct.index_filled_canopy
    ]

    result = initialise_absorbed_radiation(
        topofcanopy_radiation=dummy_climate_data["topofcanopy_radiation"]
        .isel(time_index=0)
        .to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.to_numpy(),
        light_extinction_coefficient=0.01,
    )

    exp_result = np.array([[0.09995] * 4, [0.09985] * 4, [0.09975] * 4])
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_initialise_canopy_temperature(dummy_climate_data, fixture_core_components):
    """Test that canopy temperature is initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_temperature,
    )

    lyr_strct = fixture_core_components.layer_structure

    air_temperature = dummy_climate_data["air_temperature"][
        lyr_strct.index_filled_canopy
    ]

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


def test_initialise_canopy_and_soil_fluxes(dummy_climate_data, fixture_core_components):
    """Test that canopy and soil fluxes initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_and_soil_fluxes,
    )

    result = initialise_canopy_and_soil_fluxes(
        air_temperature=dummy_climate_data["air_temperature"],
        topofcanopy_radiation=(
            dummy_climate_data["topofcanopy_radiation"].isel(time_index=0)
        ),
        leaf_area_index=dummy_climate_data["leaf_area_index"],
        layer_heights=dummy_climate_data["layer_heights"],
        layer_structure=fixture_core_components.layer_structure,
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
        np.testing.assert_allclose(result[var][1:4].to_numpy(), np.full((3, 4), 0.001))
        np.testing.assert_allclose(result[var][12].to_numpy(), np.repeat(0.001, 4))


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


def test_calculate_surface_temperature():
    """Test calculation of surface temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_surface_temperature,
    )

    core_consts = CoreConsts()
    abiotic_consts = AbioticConsts()

    result = calculate_surface_temperature(
        absorbed_shortwave_radiation=np.repeat(400, 3),
        heat_conductivity=np.repeat(0.2, 3),
        vapour_conductivity=np.repeat(0.01, 3),
        surface_temperature=np.repeat(25.0, 3),
        temperature_average_air_surface=np.repeat(20.0, 3),
        atmospheric_pressure=np.repeat(101.3, 3),
        effective_vapour_pressure_air=np.repeat(1.2, 3),
        surface_emissivity=0.9,
        ground_heat_flux=np.repeat(30.0, 3),
        relative_humidity=np.repeat(0.6, 3),
        stefan_boltzmann_constant=core_consts.stefan_boltzmann_constant,
        celsius_to_kelvin=core_consts.zero_Celsius,
        latent_heat_vap_equ_factors=abiotic_consts.latent_heat_vap_equ_factors,
        molar_heat_capacity_air=29.1,
        specific_heat_equ_factors=abiotic_consts.specific_heat_equ_factors,
        saturation_vapour_pressure_factors=[0.61078, 7.5, 237.3],
    )
    exp_result = np.repeat(21.96655, 3)

    np.testing.assert_allclose(result, exp_result, atol=1e-5)


# def test_calculate_leaf_and_air_temperature(
#     fixture_core_components,
#     dummy_climate_data,
# ):
#     """Test updating leaf and air temperature."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         calculate_leaf_and_air_temperature,
#     )
#     from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts

#     lyr_strct = fixture_core_components.layer_structure

#     result = calculate_leaf_and_air_temperature(
#         data=dummy_climate_data,
#         time_index=1,
#         layer_structure=lyr_strct,
#         abiotic_constants=AbioticConsts(),
#         abiotic_simple_constants=AbioticSimpleConsts(),
#         core_constants=CoreConsts(),
#     )

#     exp_air_temp = lyr_strct.from_template()
#     exp_air_temp[lyr_strct.index_filled_atmosphere] = np.array(
#         [30.0, 29.999969, 29.995439, 28.796977, 20.08797]
#     )[:, None]

#     exp_leaf_temp = lyr_strct.from_template()
#     exp_leaf_temp[lyr_strct.index_filled_canopy] = np.array(
#         [30.078613, 29.091601, 26.951191]
#     )[:, None]

#     exp_vp = lyr_strct.from_template()
#     exp_vp[lyr_strct.index_filled_atmosphere] = np.array(
#         [0.14, 0.140323, 0.18372, 1.296359, 0.023795]
#     )[:, None]

#     exp_vpd = lyr_strct.from_template()
#     exp_vpd[lyr_strct.index_filled_atmosphere] = np.array(
#         [0.098781, 0.099009, 0.129644, 0.94264, 0.021697]
#     )[:, None]

#     exp_gv = lyr_strct.from_template()
#     exp_gv[lyr_strct.index_filled_canopy] = np.array([0.203513, 0.202959, 0.202009])[
#         :, None
#     ]

#     # TODO - flux layer index does not include above but these tests do - what is best
#     flux_index = np.logical_or(lyr_strct.index_flux_layers, lyr_strct.index_above)

#     exp_sens_heat = lyr_strct.from_template()
#     exp_sens_heat[flux_index] = np.array([0.0, 1.397746, 1.315211, -1.515519, 1.0])[
#         :, None
#     ]

#     exp_latent_heat = lyr_strct.from_template()
#     exp_latent_heat[flux_index] = np.array([0.0, 8.330748, 8.426556, 11.740824, 1.0])[
#         :, None
#     ]

#     np.testing.assert_allclose(
#         result["air_temperature"], exp_air_temp, rtol=1e-03, atol=1e-03
#     )
#     np.testing.assert_allclose(
#         result["canopy_temperature"], exp_leaf_temp, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["vapour_pressure"], exp_vp, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["vapour_pressure_deficit"], exp_vpd, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["leaf_vapour_conductivity"], exp_gv, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["sensible_heat_flux"], exp_sens_heat, rtol=1e-04, atol=1e-04
#     )
#     np.testing.assert_allclose(
#         result["latent_heat_flux"][1:4], exp_latent_heat[1:4], rtol=1e-04, atol=1e-04
#     )


# def test_leaf_and_air_temperature_linearisation(
#     fixture_core_components, dummy_climate_data
# ):
#     """Test linearisation of air and leaf temperature."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         leaf_and_air_temperature_linearisation,
#     )

#     lyr_strct = fixture_core_components.layer_structure

#     a_A, b_A = leaf_and_air_temperature_linearisation(
#         conductivity_from_ref_height=(
#             dummy_climate_data["conductivity_from_ref_height"][
#                 lyr_strct.index_filled_canopy
#             ]
#         ),
#         conductivity_from_soil=np.repeat(0.1, 4),
#         leaf_air_heat_conductivity=(
#             dummy_climate_data["leaf_air_heat_conductivity"][
#                 lyr_strct.index_filled_canopy
#             ]
#         ),
#         air_temperature_ref=(
#             dummy_climate_data["air_temperature_ref"].isel(time_index=0).to_numpy()
#         ),
#         top_soil_temperature=dummy_climate_data["soil_temperature"][
#             lyr_strct.index_topsoil
#         ].to_numpy(),
#     )

#     exp_a = np.full((3, 4), fill_value=29.677419)
#     exp_b = np.full((3, 4), fill_value=0.04193548)
#     np.testing.assert_allclose(a_A, exp_a)
#     np.testing.assert_allclose(b_A, exp_b)


# def test_longwave_radiation_flux_linearisation():
#     """Test linearisation of longwave radiation fluxes."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         longwave_radiation_flux_linearisation,
#     )

#     a_R, b_R = longwave_radiation_flux_linearisation(
#         a_A=np.full((3, 4), fill_value=29.677419),
#         b_A=np.full((3, 4), fill_value=0.04193548),
#         air_temperature_ref=np.full((3, 4), 30.0),
#         leaf_emissivity=0.8,
#         stefan_boltzmann_constant=CoreConsts.stefan_boltzmann_constant,
#     )

#     exp_a = np.full((3, 4), fill_value=0.035189)
#     exp_b = np.full((3, 4), fill_value=0.005098)
#     np.testing.assert_allclose(a_R, exp_a, rtol=1e-04, atol=1e-04)
#     np.testing.assert_allclose(b_R, exp_b, rtol=1e-04, atol=1e-04)


# def test_vapour_pressure_linearisation():
#     """Test linearisation of vapour pressure."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         vapour_pressure_linearisation,
#     )

#     a_E, b_E = vapour_pressure_linearisation(
#         vapour_pressure_ref=np.full((3, 4), 0.14),
#         saturated_vapour_pressure_ref=np.full((3, 4), 0.5),
#         soil_vapour_pressure=np.full((3, 4), 0.14),
#         conductivity_from_soil=np.repeat(0.1, 4),
#         leaf_vapour_conductivity=np.full((3, 4), 0.2),
#         conductivity_from_ref_height=np.full((3, 4), 3),
#         delta_v_ref=np.full((3, 4), 0.14474),
#     )

#     exp_a = np.full((3, 4), fill_value=0.161818)
#     exp_b = np.full((3, 4), fill_value=0.043861)
#     np.testing.assert_allclose(a_E, exp_a, rtol=1e-04, atol=1e-04)
#     np.testing.assert_allclose(b_E, exp_b, rtol=1e-04, atol=1e-04)


# def test_latent_heat_flux_linearisation():
#     """Test latent heat flux linearisation."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         latent_heat_flux_linearisation,
#     )

#     a_L, b_L = latent_heat_flux_linearisation(
#         latent_heat_vapourisation=np.full((3, 4), 2245.0),
#         leaf_vapour_conductivity=np.full((3, 4), 0.2),
#         atmospheric_pressure_ref=np.repeat(96.0, 4),
#         saturated_vapour_pressure_ref=np.full((3, 4), 0.5),
#         a_E=np.full((3, 4), fill_value=0.161818),
#         b_E=np.full((3, 4), fill_value=0.043861),
#         delta_v_ref=np.full((3, 4), 0.14474),
#     )

#     exp_a = np.full((3, 4), fill_value=13.830078)
#     exp_b = np.full((3, 4), fill_value=46.3633)
#     np.testing.assert_allclose(a_L, exp_a, rtol=1e-04, atol=1e-04)
#     np.testing.assert_allclose(b_L, exp_b, rtol=1e-04, atol=1e-04)


# def test_calculate_delta_canopy_temperature():
#     """Test calculate delta canopy temperature."""

#     from virtual_ecosystem.models.abiotic.energy_balance import (
#         calculate_delta_canopy_temperature,
#     )

#     delta_t = calculate_delta_canopy_temperature(
#         absorbed_radiation=np.full((3, 4), 10),
#         a_R=np.full((3, 4), fill_value=0.035189),
#         a_L=np.full((3, 4), fill_value=13.830078),
#         b_R=np.full((3, 4), fill_value=0.005098),
#         b_L=np.full((3, 4), fill_value=46.3633),
#         b_H=np.full((3, 4), fill_value=46.3633),
#     )

#     exp_delta_t = np.full((3, 4), fill_value=-0.041238)
#     np.testing.assert_allclose(delta_t, exp_delta_t, rtol=1e-04, atol=1e-04)
