"""Test module for scaling_functions.py."""

import pytest


@pytest.mark.parametrize(
    "mass, population_density, terms, scenario_id",
    [
        pytest.param(100000.0, 1.0, (-0.75, 4.23), "large_mass_low_density"),
        pytest.param(0.07, 32.0, (-0.75, 4.23), "small_mass_high_density"),
        pytest.param(1.0, 5.0, (-0.75, 4.23), "medium_mass_medium_density"),
    ],
)
def test_damuths_law(mass, population_density, terms, scenario_id):
    """Testing damuth's law for various body-masses."""

    from virtual_ecosystem.models.animals.scaling_functions import damuths_law

    testing_pop = damuths_law(mass, terms)
    assert testing_pop == pytest.approx(
        population_density
    ), f"Scenario {scenario_id} failed: Expect {population_density}, got {testing_pop}"


@pytest.mark.parametrize(
    "mass, temperature, terms, metabolic_type, met_rate",
    [
        # Test cases for an endothermic animal
        pytest.param(
            0.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "endothermic",
            0.0,
            id="endothermic_zero_mass",
        ),
        pytest.param(
            1.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "endothermic",
            2.3264417757316824e-16,
            id="endothermic_small_mass",
        ),
        pytest.param(
            1000.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "endothermic",
            3.218786623537764e-16,
            id="endothermic_large_mass",
        ),
        # Test cases for an ectothermic animal
        pytest.param(
            0.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "ectothermic",
            0.0,
            id="ectothermic_zero_mass",
        ),
        pytest.param(
            1.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "ectothermic",
            9.116692117764761e-17,
            id="ectothermic_small_mass",
        ),
        pytest.param(
            1000.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "ectothermic",
            1.261354870157637e-16,
            id="ectothermic_large_mass",
        ),
    ],
)
def test_metabolic_rate(mass, temperature, terms, metabolic_type, met_rate):
    """Testing metabolic rate for various body-masses."""

    from virtual_ecosystem.models.animals.animal_traits import MetabolicType
    from virtual_ecosystem.models.animals.scaling_functions import metabolic_rate

    testing_rate = metabolic_rate(
        mass, temperature, terms, MetabolicType(metabolic_type)
    )
    assert testing_rate == pytest.approx(met_rate, rel=1e-6)


@pytest.mark.parametrize(
    "mass, muscle, terms",
    [
        pytest.param(0.0, 0.0, (1.0, 0.38), id="zero_mass"),
        pytest.param(1.0, 380.0, (1.0, 0.38), id="small_mass"),
        pytest.param(1000.0, 380000.0, (1.0, 0.38), id="large_mass"),
    ],
)
def test_muscle_mass_scaling(mass, muscle, terms):
    """Testing muscle mass scaling for various body-masses."""

    from virtual_ecosystem.models.animals.scaling_functions import muscle_mass_scaling

    gains = muscle_mass_scaling(mass, terms)
    assert gains == pytest.approx(muscle, rel=1e-6)


@pytest.mark.parametrize(
    "mass, fat, terms",
    [
        pytest.param(0.0, 0.0, (1.19, 0.02), id="zero_mass"),
        pytest.param(1.0, 74.307045, (1.19, 0.02), id="low_mass"),
        pytest.param(1000.0, 276076.852920, (1.19, 0.02), id="large_mass"),
    ],
)
def test_fat_mass_scaling(mass, fat, terms):
    """Testing fat mass scaling for various body-masses."""

    from virtual_ecosystem.models.animals.scaling_functions import fat_mass_scaling

    gains = fat_mass_scaling(mass, terms)
    assert gains == pytest.approx(fat, rel=1e-6)


@pytest.mark.parametrize(
    "mass, energy, muscle_terms, fat_terms",
    [
        pytest.param(0.0, 0.0, (1.0, 0.38), (1.19, 0.02), id="zerp_mass"),
        pytest.param(1.0, 3180149.320736, (1.0, 0.38), (1.19, 0.02), id="low_mass"),
        pytest.param(
            1000.0, 4592537970.444037, (1.0, 0.38), (1.19, 0.02), id="high_mass"
        ),
    ],
)
def test_energetic_reserve_scaling(mass, energy, muscle_terms, fat_terms):
    """Testing energetic reserve scaling for various body-masses."""

    from virtual_ecosystem.models.animals.scaling_functions import (
        energetic_reserve_scaling,
    )

    gains = energetic_reserve_scaling(mass, muscle_terms, fat_terms)
    assert gains == pytest.approx(energy, rel=1e-6)


@pytest.mark.parametrize(
    "mass, intake_rate, terms",
    [
        pytest.param(0.0, 0.0, (0.71, 0.63), id="zero_mass"),
        pytest.param(1.0, 0.3024, (0.71, 0.63), id="low_mass"),
        pytest.param(1000.0, 40.792637, (0.71, 0.63), id="high_mass"),
    ],
)
def test_intake_rate_scaling(mass, intake_rate, terms):
    """Testing intake rate scaling for various body-masses."""

    from virtual_ecosystem.models.animals.scaling_functions import intake_rate_scaling

    test_rate = intake_rate_scaling(mass, terms)
    assert test_rate == pytest.approx(intake_rate, rel=1e-6)


def test_herbivore_prey_group_selection():
    """Test for herbivore diet type selection."""
    from virtual_ecosystem.models.animals.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result = prey_group_selection(DietType.HERBIVORE, 10.0, (0.1, 1000.0))
    assert result == {"plants": (0.0, 0.0)}


def test_carnivore_prey_group_selection():
    """Test for carnivore diet type selection."""
    from virtual_ecosystem.models.animals.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result = prey_group_selection(DietType.CARNIVORE, 10.0, (0.1, 1000.0))
    expected_output = {
        "herbivorous_mammal": (0.1, 1000.0),
        "carnivorous_mammal": (0.1, 1000.0),
        "herbivorous_bird": (0.1, 1000.0),
        "carnivorous_bird": (0.1, 1000.0),
        "herbivorous_insect": (0.1, 1000.0),
        "carnivorous_insect": (0.1, 1000.0),
    }
    assert result == expected_output


def test_prey_group_selection_invalid_diet_type():
    """Test for an invalid diet type."""

    from virtual_ecosystem.models.animals.scaling_functions import prey_group_selection

    with pytest.raises(ValueError, match="Invalid diet type:"):
        prey_group_selection("omnivore", 10.0, (0.1, 1000.0))


def test_prey_group_selection_mass_and_terms_impact():
    """Test to ensure `mass` and `terms` don't affect output."""
    from virtual_ecosystem.models.animals.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result_default = prey_group_selection(DietType.CARNIVORE, 10.0, (0.1, 1000.0))
    result_diff_mass = prey_group_selection(DietType.CARNIVORE, 50.0, (0.1, 1000.0))
    result_diff_terms = prey_group_selection(DietType.CARNIVORE, 10.0, (0.5, 500.0))

    assert result_default == result_diff_mass == result_diff_terms


@pytest.mark.parametrize(
    "mass, terms, expected, error_type",
    [
        pytest.param(1.0, (0.25, 0.05), 0.2055623, None, id="low_mass_valid"),
        pytest.param(1000.0, (0.01, 0.1), 0.1018162, None, id="high_mass_valid"),
        pytest.param(
            0.0,
            (0.71, 0.63),
            None,
            ZeroDivisionError,
            id="zero_mass_error",
        ),
        pytest.param(
            -1.0,
            (0.71, 0.63),
            None,
            TypeError,
            id="negative_mass_error",
        ),
        pytest.param(
            1.0,
            (0.71,),
            None,
            IndexError,
            id="invalid_terms_error",
        ),
    ],
)
def test_natural_mortality_scaling(mass, terms, expected, error_type):
    """Testing natural mortality scaling for various body-masses."""
    from virtual_ecosystem.models.animals.scaling_functions import (
        natural_mortality_scaling,
    )

    if error_type:
        with pytest.raises(error_type):
            natural_mortality_scaling(mass, terms)
    else:
        result = natural_mortality_scaling(mass, terms)
        assert result == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        pytest.param(1.0, 1.0, id="unit_value"),
        pytest.param(0.0, 0.0, id="zero_value"),
        pytest.param(-0.01, -0.01, id="negative_value"),
    ],
)
def test_background_mortality(input_value, expected_output):
    """Test the background_mortality function returns the correct mortality rate."""
    from virtual_ecosystem.models.animals.scaling_functions import background_mortality

    assert (
        background_mortality(input_value) == expected_output
    ), "The mortality rate returned did not match the expected value."


@pytest.mark.parametrize(
    "lambda_se, t_to_maturity, t_since_maturity, expected_mortality",
    [
        pytest.param(0.01, 100, 50, 0.01648721, id="typical_case"),
        pytest.param(0.01, 50, 100, 0.07389056, id="more_since_than_to"),
        pytest.param(0.0, 100, 50, 0.0, id="zero_senescence_rate"),
        pytest.param(
            0.01,
            0,
            100,
            None,
            id="zero_time_to_maturity",
            marks=pytest.mark.xfail(reason="Division by zero"),
        ),
        pytest.param(0.01, 100, 0, 0.01, id="zero_time_since_maturity"),
    ],
)
def test_senescence_mortality(
    lambda_se, t_to_maturity, t_since_maturity, expected_mortality
):
    """Test the calculation of senescence mortality rate."""

    from virtual_ecosystem.models.animals.scaling_functions import senescence_mortality

    if t_to_maturity == 0:
        with pytest.raises(ZeroDivisionError):
            senescence_mortality(lambda_se, t_to_maturity, t_since_maturity)
    else:
        result = senescence_mortality(lambda_se, t_to_maturity, t_since_maturity)
        assert result == pytest.approx(
            expected_mortality
        ), "The calculated mortality did not match the expected value."


@pytest.mark.parametrize(
    "lambda_max, J_st, zeta_st, mass_current, mass_max, expected_mortality, param_id",
    [
        pytest.param(
            1.0,
            0.6,
            0.05,
            50,
            100,
            0.880797077,
            "half_mass_case",
            id="half_mass_case",
        ),
        pytest.param(
            1.0,
            0.6,
            0.05,
            0,
            100,
            0.999993855,
            "zero_mass",
            id="zero_mass",
        ),
        pytest.param(
            1.0,
            0.6,
            0.05,
            100,
            100,
            0.00033535,
            "mass_equals_max",
            id="mass_equals_max",
        ),
        pytest.param(
            1.0,
            0.6,
            0.05,
            200,
            100,
            0.0,
            "mass_exceeds_max",
            id="mass_exceeds_max",
        ),
    ],
)
def test_starvation_mortality(
    lambda_max, J_st, zeta_st, mass_current, mass_max, expected_mortality, param_id
):
    """Test the calculation of starvation mortality based on body mass.

    Args:
        lambda_max (float): The maximum possible instantaneous fractional starvation
         mortality rate.
        J_st (float): Determines the inflection point of the logistic function
         describing the ratio of the realised mortality rate to the maximum rate.
        zeta_st (float): The scaling of the logistic function describing the ratio of
                         realised mortality rate to the maximum rate.
        mass_current (float): The current mass of the animal cohort.
        mass_max (float): The maximum body mass ever achieved by individuals of this
         type.
        expected_mortality (float): The expected mortality rate.
        param_id (str): Identifier for the test case.

    """
    from virtual_ecosystem.models.animals.scaling_functions import starvation_mortality

    # Diagnostics
    print(
        f"Testing with: lambda_max={lambda_max}, J_st={J_st}, zeta_st={zeta_st}, "
        f"mass_current={mass_current}, mass_max={mass_max}, param_id={param_id}"
    )

    # Call the function with provided parameters
    mortality_rate = starvation_mortality(
        lambda_max, J_st, zeta_st, mass_current, mass_max
    )

    # Assert that the returned mortality rate matches the expected mortality rate
    assert mortality_rate == pytest.approx(expected_mortality), (
        f"Test {param_id}: The calculated starvation mortality {mortality_rate} does"
        f" not match the expected value {expected_mortality}."
    )

    # Diagnostics
    print(
        f"Test {param_id} passed: Calculated mortality rate: {mortality_rate}, "
        f"Expected mortality rate: {expected_mortality}"
    )


@pytest.mark.parametrize(
    "alpha_0_herb, mass, expected_search_rate",
    [
        pytest.param(0.1, 1.0, 0.1, id="base_rate"),
        pytest.param(0.2, 5.0, 1.0, id="increased_rate"),
        pytest.param(0.05, 10.0, 0.5, id="decreased_rate"),
        pytest.param(0.0, 10.0, 0.0, id="zero_rate"),
        pytest.param(0.1, 0.0, 0.0, id="zero_mass"),
    ],
)
def test_alpha_i_k(alpha_0_herb, mass, expected_search_rate):
    """Testing effective search rate calculation for various herbivore body masses."""

    from virtual_ecosystem.models.animals.scaling_functions import alpha_i_k

    calculated_search_rate = alpha_i_k(alpha_0_herb, mass)
    assert calculated_search_rate == pytest.approx(expected_search_rate, rel=1e-6)


@pytest.mark.parametrize(
    "alpha_i_k, phi_herb_t, B_k_t, A_cell, expected_biomass",
    [
        pytest.param(0.1, 0.5, 1000, 1, 25000.0, id="standard_scenario"),
        pytest.param(0.2, 0.5, 1000, 1, 50000.0, id="increased_search_rate"),
        pytest.param(0.1, 1, 1000, 1, 100000.0, id="all_plant_stock_available"),
        pytest.param(0.1, 0.5, 2000, 1, 100000.0, id="increased_plant_biomass"),
        pytest.param(0.1, 0.5, 1000, 2, 6250.0, id="increased_cell_area"),
        pytest.param(0, 0.5, 1000, 1, 0.0, id="zero_search_rate"),
        pytest.param(0.1, 0, 1000, 1, 0.0, id="no_plant_stock_available"),
        pytest.param(0.1, 0.5, 0, 1, 0.0, id="zero_plant_biomass"),
    ],
)
def test_k_i_k(alpha_i_k, phi_herb_t, B_k_t, A_cell, expected_biomass):
    """Testing the potential biomass eaten calculation for various scenarios."""

    from virtual_ecosystem.models.animals.scaling_functions import k_i_k

    calculated_biomass = k_i_k(alpha_i_k, phi_herb_t, B_k_t, A_cell)
    assert calculated_biomass == pytest.approx(expected_biomass, rel=1e-6)


@pytest.mark.parametrize(
    "h_herb_0, M_ref, M_i_t, b_herb, expected_handling_time, expect_exception",
    [
        pytest.param(1.0, 10.0, 10.0, 0.75, 1.0, False, id="M_ref_equals_M_i_t"),
        pytest.param(1.0, 10.0, 5.0, 0.75, 1.6817928, False, id="M_i_t_half_of_M_ref"),
        pytest.param(
            1.0, 10.0, 20.0, 0.75, 0.5946035, False, id="M_i_t_double_of_M_ref"
        ),
        pytest.param(2.0, 10.0, 10.0, 0.75, 2.0, False, id="increased_h_herb_0"),
        pytest.param(1.0, 10.0, 10.0, 1.0, 1.0, False, id="increased_b_herb"),
        pytest.param(1.0, 10.0, 10.0, 0.0, 1.0, False, id="b_herb_zero"),
        pytest.param(
            1.0, 10.0, 0.0, 0.75, None, True, id="M_i_t_zero_expect_exception"
        ),
    ],
)
def test_H_i_k(
    h_herb_0, M_ref, M_i_t, b_herb, expected_handling_time, expect_exception
):
    """Testing the handling time calculation for various herbivore masses."""
    from virtual_ecosystem.models.animals.scaling_functions import H_i_k

    if expect_exception:
        with pytest.raises(ZeroDivisionError):
            H_i_k(h_herb_0, M_ref, M_i_t, b_herb)
    else:
        calculated_handling_time = H_i_k(h_herb_0, M_ref, M_i_t, b_herb)
        assert calculated_handling_time == pytest.approx(
            expected_handling_time, rel=1e-6
        )


@pytest.mark.parametrize(
    "theta_opt_min_f, theta_opt_f, sigma_opt_f, random_value, expected",
    [
        pytest.param(
            0.1, 0.2, 0.05, 0.15, 0.15, id="random_value_between_min_f_and_opt_f"
        ),
        pytest.param(0.1, 0.2, 0.05, 0.05, 0.1, id="random_value_less_than_min_f"),
        pytest.param(0.1, 0.2, 0.05, 0.25, 0.25, id="random_value_greater_than_opt_f"),
    ],
)
def test_theta_opt_i(
    mocker, theta_opt_min_f, theta_opt_f, sigma_opt_f, random_value, expected
):
    """Testing the optimum predator-prey mass ratio calculation with randomness."""

    import numpy as np

    # Mock np.random.normal to return a controlled random value
    mocker.patch.object(np.random, "normal", return_value=random_value)

    from virtual_ecosystem.models.animals.scaling_functions import theta_opt_i

    result = theta_opt_i(theta_opt_min_f, theta_opt_f, sigma_opt_f)
    assert result == expected


@pytest.mark.parametrize(
    (
        "mass_predator, mass_prey, theta_opt_i, "
        "sigma_opt_pred_prey, expected_output, expect_exception"
    ),
    [
        pytest.param(10.0, 5.0, 2.0, 0.1, None, False, id="predator_twice_prey"),
        pytest.param(5.0, 10.0, 0.5, 0.1, None, False, id="prey_twice_predator"),
        pytest.param(10.0, 10.0, 1.0, 0.1, None, False, id="equal_mass_optimal_ratio"),
        pytest.param(
            10.0, 10.0, 1.0, 0.5, None, False, id="increased_standard_deviation"
        ),
        pytest.param(0.0, 10.0, 1.0, 0.1, None, True, id="zero_mass_predator"),
        pytest.param(10.0, 0.0, 1.0, 0.1, None, True, id="zero_mass_prey"),
    ],
)
def test_w_bar_i_j(
    mass_predator,
    mass_prey,
    theta_opt_i,
    sigma_opt_pred_prey,
    expected_output,
    expect_exception,
):
    """Testing the success probability for various predator-prey mass ratios."""
    from virtual_ecosystem.models.animals.scaling_functions import w_bar_i_j

    if expect_exception:
        with pytest.raises((ZeroDivisionError, ValueError)):
            w_bar_i_j(mass_predator, mass_prey, theta_opt_i, sigma_opt_pred_prey)
    else:
        result = w_bar_i_j(mass_predator, mass_prey, theta_opt_i, sigma_opt_pred_prey)
        assert (
            0.0 <= result <= 1.0
        ), "Result is outside the expected probability range [0.0, 1.0]"


@pytest.mark.parametrize(
    "alpha_0_pred, mass, w_bar_i_j, expected_search_rate",
    [
        pytest.param(0.1, 10.0, 0.5, 0.5, id="basic_scenario"),
        pytest.param(0.2, 5.0, 0.75, 0.75, id="different_values"),
        pytest.param(0.0, 10.0, 0.5, 0.0, id="zero_alpha_0_pred"),
        pytest.param(0.1, 0.0, 0.5, 0.0, id="zero_mass"),
        pytest.param(0.1, 10.0, 0.0, 0.0, id="zero_w_bar_i_j"),
        pytest.param(0.1, 10.0, 1.0, 1.0, id="w_bar_i_j_is_1"),
    ],
)
def test_alpha_i_j(alpha_0_pred, mass, w_bar_i_j, expected_search_rate):
    """Testing the effective search rate calculation for various inputs."""
    from virtual_ecosystem.models.animals.scaling_functions import alpha_i_j

    calculated_search_rate = alpha_i_j(alpha_0_pred, mass, w_bar_i_j)
    assert calculated_search_rate == pytest.approx(expected_search_rate, rel=1e-6)


@pytest.mark.parametrize(
    "alpha_i_j, N_i_t, A_cell, theta_i_j, expected_output",
    [
        pytest.param(0.1, 100, 1.0, 0.5, 5.0, id="basic_scenario"),
        pytest.param(0.2, 50, 2.0, 0.75, 3.75, id="varied_parameters"),
        pytest.param(0.0, 100, 1.0, 0.5, 0.0, id="zero_search_rate"),
        pytest.param(0.1, 0, 1.0, 0.5, 0.0, id="zero_predator_population"),
        pytest.param(
            0.1, 100, 0.0, 0.5, float("inf"), id="zero_cell_area_expect_inf_or_error"
        ),
        pytest.param(0.1, 100, 1.0, 0.0, 0.0, id="zero_theta_i_j"),
    ],
)
def test_k_i_j(alpha_i_j, N_i_t, A_cell, theta_i_j, expected_output):
    """Testing the calculation of potential prey items eaten."""
    from virtual_ecosystem.models.animals.scaling_functions import k_i_j

    # Handle special case where division by zero might occur
    if A_cell == 0:
        with pytest.raises(ZeroDivisionError):
            k_i_j(alpha_i_j, N_i_t, A_cell, theta_i_j)
    else:
        calculated_output = k_i_j(alpha_i_j, N_i_t, A_cell, theta_i_j)
        assert calculated_output == pytest.approx(expected_output, rel=1e-6)


@pytest.mark.parametrize(
    "h_pred_0, M_ref, M_i_t, b_pred, expected_handling_time",
    [
        pytest.param(1.0, 10.0, 10.0, 0.75, 10.0, id="basic_scenario"),
        pytest.param(1.0, 10.0, 5.0, 0.75, 8.4089641, id="M_i_t_half_of_M_ref"),
        pytest.param(1.0, 10.0, 20.0, 0.75, 11.892071, id="M_i_t_double_of_M_ref"),
        pytest.param(2.0, 10.0, 10.0, 0.75, 20.0, id="increased_h_pred_0"),
        pytest.param(1.0, 10.0, 10.0, 1.0, 10.0, id="increased_b_pred"),
        pytest.param(1.0, 10.0, 0.0, 0.75, float("inf"), id="zero_M_i_t_expect_inf"),
        pytest.param(1.0, 0.0, 10.0, 0.75, 0.0, id="zero_M_ref_leads_to_zero"),
    ],
)
def test_H_i_j(h_pred_0, M_ref, M_i_t, b_pred, expected_handling_time):
    """Testing the handling time calculation for various predator-prey interactions."""
    from virtual_ecosystem.models.animals.scaling_functions import H_i_j

    # Handle special case where division by zero might occur
    if M_i_t == 0:
        with pytest.raises(ZeroDivisionError):
            H_i_j(h_pred_0, M_ref, M_i_t, b_pred)
    else:
        calculated_handling_time = H_i_j(h_pred_0, M_ref, M_i_t, b_pred)
        assert calculated_handling_time == pytest.approx(
            expected_handling_time, rel=1e-6
        )


@pytest.mark.parametrize(
    "current_mass, V_disp, M_disp_ref, o_disp, expected_speed",
    [
        pytest.param(1.0, 10.0, 1.0, 1.0, 10.0, id="reference_mass"),
        pytest.param(0.5, 10.0, 1.0, 1.0, 5.0, id="half_reference_mass"),
        pytest.param(2.0, 10.0, 1.0, 1.0, 20.0, id="double_reference_mass"),
        pytest.param(1.0, 20.0, 1.0, 1.0, 20.0, id="double_speed"),
        pytest.param(1.0, 10.0, 1.0, 0.5, 10.0, id="sqrt_scaling"),
        pytest.param(
            4.0, 10.0, 2.0, 0.5, 14.142135, id="sqrt_scaling_with_different_ref"
        ),
        pytest.param(0.0, 10.0, 1.0, 1.0, 0.0, id="zero_mass"),
    ],
)
def test_juvenile_dispersal_speed(
    current_mass, V_disp, M_disp_ref, o_disp, expected_speed
):
    """Testing the juvenile dispersal speed calculation for various scenarios."""
    from virtual_ecosystem.models.animals.scaling_functions import (
        juvenile_dispersal_speed,
    )

    calculated_speed = juvenile_dispersal_speed(
        current_mass, V_disp, M_disp_ref, o_disp
    )
    assert calculated_speed == pytest.approx(expected_speed, rel=1e-6)
