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

    np.testing.assert_allclose(
        result,
        np.array(
            [
                [0.09995, 0.09995, 0.09995],
                [0.09985, 0.09985, 0.09985],
                [0.09975, 0.09975, 0.09975],
            ]
        ),
        rtol=1e-04,
        atol=1e-04,
    )


def test_initialise_canopy_temperature(dummy_climate_data):
    """Test that canopy temperature is initialised correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        initialise_canopy_temperature,
    )

    d = dummy_climate_data
    air_temperature = d["air_temperature"][
        d["leaf_area_index"]["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    absorbed_radiation = np.array(
        [
            [0.09995, 0.09995, 0.09995],
            [0.09985, 0.09985, 0.09985],
            [0.09975, 0.09975, 0.09975],
        ]
    )

    exp_result = np.array(
        [
            [29.845994, 29.845994, 29.845994],
            [28.872169, 28.872169, 28.872169],
            [27.207403, 27.207403, 27.207403],
        ]
    )
    result = initialise_canopy_temperature(
        air_temperature=air_temperature,
        absorbed_radiation=absorbed_radiation,
        canopy_temperature_ini_factor=0.01,
    )
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_calculate_slope_of_saturated_pressure_curve():
    """Test calculation of slope of saturated pressure curve."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_slope_of_saturated_pressure_curve,
    )

    result = calculate_slope_of_saturated_pressure_curve(
        temperature=np.full((4, 3), 20.0)
    )
    exp_result = np.full((4, 3), 0.14474)
    np.testing.assert_allclose(result, exp_result, rtol=1e-04, atol=1e-04)


def test_initialise_canopy_and_soil_fluxes(dummy_climate_data):
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
        light_extinction_coefficient=0.01,
        canopy_temperature_ini_factor=0.01,
    )

    for var in [
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "canopy_absorption",
    ]:
        assert var in result

    np.testing.assert_allclose(
        result["canopy_absorption"][1:4].to_numpy(),
        np.array(
            [
                [0.09995, 0.09995, 0.09995],
                [0.09985, 0.09985, 0.09985],
                [0.09975, 0.09975, 0.09975],
            ]
        ),
        rtol=1e-04,
        atol=1e-04,
    )
    for var in ["sensible_heat_flux", "latent_heat_flux"]:
        np.testing.assert_allclose(result[var][1:4].to_numpy(), np.zeros((3, 3)))
        np.testing.assert_allclose(result[var][12].to_numpy(), np.zeros(3))


def test_calculate_longwave_emission():
    """Test that longwave radiation is calculated correctly."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_longwave_emission,
    )

    result = calculate_longwave_emission(
        temperature=np.array([290.0, 290.0, 290.0]),
        emissivity=AbioticConsts.soil_emissivity,
        stefan_boltzmann=CoreConsts.stefan_boltzmann_constant,
    )
    np.testing.assert_allclose(
        result,
        np.array([320.843847, 320.843847, 320.843847]),
        rtol=1e-04,
        atol=1e-04,
    )


def test_calculate_leaf_and_air_temperature(
    dummy_climate_data,
):
    """Test updating leaf and air temperature."""

    from virtual_ecosystem.models.abiotic.energy_balance import (
        calculate_leaf_and_air_temperature,
    )
    from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts

    # from virtual_ecosystem.core.core_components import LayerStructure
    # from virtual_ecosystem.core.config import Config
    # cfg_string = """
    #     [core]
    #     [core.grid]
    #     cell_nx = 10
    #     cell_ny = 10
    #     [core.timing]
    #     start_date = "2020-01-01"
    #     update_interval = "2 weeks"
    #     run_length = "50 years"
    #     [core.data_output_options]
    #     save_initial_state = true
    #     save_final_state = true
    #     out_initial_file_name = "model_at_start.nc"
    #     out_final_file_name = "model_at_end.nc"
    #     [core.layers]
    #     canopy_layers = 10
    #     soil_layers = [-0.25, -1.0]
    #     above_canopy_height_offset = 2.0
    #     surface_layer_height = 0.1
    #     subcanopy_layer_height = 1.5
    #     """
    # config = Config(cfg_strings=cfg_string)
    # layer_structure = LayerStructure(config=config)

    result = calculate_leaf_and_air_temperature(
        data=dummy_climate_data,
        time_index=1,
        topsoil_layer_index=13,
        true_canopy_layers_n=3,
        # layer_structure=layer_structure,
        canopy_layers=10,
        soil_layers=[0.25, 1.5],
        n_layers=15,
        abiotic_constants=AbioticConsts(),
        abiotic_simple_constants=AbioticSimpleConsts(),
        core_constants=CoreConsts(),
    )

    exp_air_temp = DataArray(
        np.concatenate(
            (
                np.array(
                    [
                        [30.0, 30.0, 30.0],
                        [29.999967, 29.999967, 29.999967],
                        [29.995428, 29.995428, 29.995428],
                        [29.504507, 29.504507, 29.504507],
                    ],
                ),
                np.full((7, 3), np.nan),
                np.array(
                    [[21.425606, 21.425606, 21.425606], [20.09504, 20.09504, 20.09504]]
                ),
                np.full((2, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )

    exp_leaf_temp = DataArray(
        np.concatenate(
            (
                np.full((1, 3), np.nan),
                np.array(
                    [
                        [30.078712, 30.078712, 30.078712],
                        [29.105456, 29.105456, 29.105456],
                        [27.396327, 27.396327, 27.396327],
                    ],
                ),
                np.full((11, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )
    exp_vapour_pressure = DataArray(
        np.concatenate(
            (
                np.array(
                    [
                        [0.14, 0.14, 0.14],
                        [0.14001, 0.14001, 0.14001],
                        [0.141425, 0.141425, 0.141425],
                        [0.281758, 0.281758, 0.281758],
                    ],
                ),
                np.full((7, 3), np.nan),
                np.array(
                    [
                        [0.228266, 0.228266, 0.228266],
                        [0.219455, 0.219455, 0.219455],
                    ]
                ),
                np.full((2, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )

    exp_vpd = DataArray(
        np.concatenate(
            (
                np.array(
                    [
                        [0.098781, 0.098781, 0.098781],
                        [0.098789, 0.098789, 0.098789],
                        [0.099798, 0.099798, 0.099798],
                        [0.201279, 0.201279, 0.201279],
                    ],
                ),
                np.full((7, 3), np.nan),
                np.array(
                    [
                        [0.200826, 0.200826, 0.200826],
                        [0.200064, 0.200064, 0.200064],
                    ]
                ),
                np.full((2, 3), np.nan),
            ),
        ),
        dims=["layers", "cell_id"],
    )

    exp_gv = DataArray(
        np.concatenate(
            [
                [
                    [np.nan, np.nan, np.nan],
                    [0.203513, 0.203513, 0.203513],
                    [0.202959, 0.202959, 0.202959],
                    [0.202009, 0.202009, 0.202009],
                ],
                [[np.nan, np.nan, np.nan]] * 11,
            ],
        ),
        dims=["layers", "cell_id"],
    )
    np.testing.assert_allclose(
        result["air_temperature"], exp_air_temp, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["canopy_temperature"], exp_leaf_temp, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["vapour_pressure"], exp_vapour_pressure, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["vapour_pressure_deficit"], exp_vpd, rtol=1e-04, atol=1e-04
    )
    np.testing.assert_allclose(
        result["leaf_vapour_conductivity"], exp_gv, rtol=1e-04, atol=1e-04
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
        conductivity_from_soil=np.repeat(0.1, 3),
        leaf_air_heat_conductivity=(
            dummy_climate_data["leaf_air_heat_conductivity"][true_canopy_layers_indexes]
        ),
        air_temperature_ref=(
            dummy_climate_data["air_temperature_ref"].isel(time_index=0).to_numpy()
        ),
        top_soil_temperature=dummy_climate_data["soil_temperature"][13].to_numpy(),
    )

    exp_a = np.array([[29.677419, 29.677419, 29.677419]] * 3)
    exp_b = np.array([[0.04193548, 0.04193548, 0.04193548]] * 3)
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
