"""Test module for scaling_functions.py."""

import pytest

from virtual_ecosystem.models.animal.scaling_functions import DietType


@pytest.mark.parametrize(
    "mass, terms",
    [
        (100000.0, (-0.75, 4.23)),
        (0.07, (-0.75, 4.23)),
        (1.0, (-0.75, 4.23)),
        (15.5, (-0.75, 4.23)),
        (0.001, (-0.75, 4.23)),
    ],
    ids=[
        "very_large_mass",
        "very_small_mass",
        "unit_mass",
        "medium_mass",
        "tiny_mass",
    ],
)
def test_damuths_law_computes_expected_value(mass, terms):
    """Test damuth's law returns the expected value with correct unit conversion."""
    from virtual_ecosystem.models.animal.scaling_functions import damuths_law

    # Convert mass to g for Damuth scaling
    mass_g = mass * 1000
    expected_km2 = terms[1] * mass_g ** terms[0]
    expected_m2 = expected_km2 / 1e6

    actual = damuths_law(mass, terms)

    assert actual == pytest.approx(expected_m2), (
        f"Expected {expected_m2} for mass {mass} and terms {terms}, got {actual}"
    )


@pytest.mark.parametrize(
    "mass, terms, expected_behavior",
    [
        # Normal test cases
        (100000.0, (0.6, 300000.0), "compute"),  # very large mass
        (0.07, (0.6, 300000.0), "compute"),  # very small mass
        (1.0, (0.6, 300000.0), "compute"),  # unit mass
        (15.5, (0.6, 300000.0), "compute"),  # medium mass
        (0.001, (0.6, 300000.0), "compute"),  # tiny mass
    ],
    ids=[
        "very_large_mass",
        "very_small_mass",
        "unit_mass",
        "medium_mass",
        "tiny_mass",
    ],
)
def test_madingley_individuals_density_value(mass, terms, expected_behavior):
    """Test madingley_individuals_density with normal and edge case inputs."""
    from virtual_ecosystem.models.animal.scaling_functions import (
        madingley_individuals_density,
    )

    exponent, scalar = terms

    if expected_behavior == "compute":
        # Expected calculation
        mass_g = mass * 1000
        expected_km2 = scalar * mass_g ** (exponent - 1)
        expected_m2 = expected_km2 / 1e6

        actual = madingley_individuals_density(mass, terms)
        assert actual == pytest.approx(expected_m2), (
            f"Expected {expected_m2} for mass {mass} and terms {terms}, got {actual}"
        )

    elif expected_behavior == "error":
        with pytest.raises(ValueError):
            madingley_individuals_density(mass, terms)


@pytest.mark.parametrize(
    "mass, temperature, terms, metabolic_type, sigma_f_t, met_rate",
    [
        # Symmetric terms (basal == field) — sigma does not affect output
        pytest.param(
            0.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "endothermic",
            1.0,
            0.0,
            id="endothermic_zero_mass",
        ),
        pytest.param(
            1.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "endothermic",
            1.0,
            2.3264417757316824e-16,
            id="endothermic_small_mass",
        ),
        pytest.param(
            1000.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "endothermic",
            1.0,
            3.218786623537764e-16,
            id="endothermic_large_mass",
        ),
        pytest.param(
            0.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "ectothermic",
            1.0,
            0.0,
            id="ectothermic_zero_mass",
        ),
        pytest.param(
            1.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "ectothermic",
            1.0,
            9.116692117764761e-17,
            id="ectothermic_small_mass",
        ),
        pytest.param(
            1000.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "ectothermic",
            1.0,
            1.261354870157637e-16,
            id="ectothermic_large_mass",
        ),
        # Asymmetric terms (basal != field) — exercises the sigma FMR/BMR split
        pytest.param(
            1.0,
            25,
            {"basal": (0.5, 0.02), "field": (0.9, 0.08)},
            "endothermic",
            1.0,
            2.316717571445662e-16,
            id="endothermic_fully_active",
        ),
        pytest.param(
            1.0,
            25,
            {"basal": (0.5, 0.02), "field": (0.9, 0.08)},
            "endothermic",
            0.0,
            1.9480521887285538e-16,
            id="endothermic_fully_inactive",
        ),
        pytest.param(
            1.0,
            25,
            {"basal": (0.5, 0.02), "field": (0.9, 0.08)},
            "ectothermic",
            1.0,
            9.078585349134391e-17,
            id="ectothermic_fully_active",
        ),
        pytest.param(
            1.0,
            25,
            {"basal": (0.5, 0.02), "field": (0.9, 0.08)},
            "ectothermic",
            0.0,
            7.633886097261398e-17,
            id="ectothermic_fully_inactive",
        ),
    ],
)
def test_metabolic_rate(mass, temperature, terms, metabolic_type, sigma_f_t, met_rate):
    """Testing metabolic rate for various body-masses and activity window fractions."""
    from virtual_ecosystem.models.animal.animal_traits import MetabolicType
    from virtual_ecosystem.models.animal.scaling_functions import metabolic_rate

    testing_rate = metabolic_rate(
        mass, temperature, terms, MetabolicType(metabolic_type), sigma_f_t
    )
    assert testing_rate == pytest.approx(met_rate, rel=1e-6)


def test_herbivore_prey_group_selection(functional_group_list_instance):
    """Test for herbivore diet type selection."""
    from virtual_ecosystem.models.animal.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result = prey_group_selection(
        DietType.HERBIVORE, 10.0, (0.1, 1000.0), functional_group_list_instance
    )
    expected = {
        "plants": (0.0, 0.0),
        "litter": (0.0, 0.0),
    }
    assert result == expected


def test_carnivore_prey_group_selection(functional_group_list_instance):
    """Test for carnivore diet type selection."""
    from virtual_ecosystem.models.animal.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result = prey_group_selection(
        DietType.CARNIVORE, 10.0, (0.1, 1000.0), functional_group_list_instance
    )
    expected_output = {
        "herbivorous_mammal": (0.0001, 1000.0),
        "carnivorous_mammal": (0.0001, 1000.0),
        "herbivorous_bird": (0.0001, 1000.0),
        "carnivorous_bird": (0.0001, 1000.0),
        "herbivorous_insect_iteroparous": (0.0001, 1000.0),
        "carnivorous_insect_iteroparous": (0.0001, 1000.0),
        "herbivorous_insect_semelparous": (0.0001, 1000.0),
        "carnivorous_insect_semelparous": (0.0001, 1000.0),
        "caterpillar": (0.0001, 1000.0),
        "swallow": (0.0001, 1000.0),
        "frog": (0.0001, 1000.0),
        "earthworm": (0.0001, 1000.0),
        "butterfly": (0.0001, 1000.0),
        "detritivorous_insect": (0.0001, 1000.0),
        "dung_beetle": (0.0001, 1000.0),
        "scavenging_mammal": (0.0001, 1000.0),
        "fungivorous_mammal": (0.0001, 1000.0),
        "carcasses": (0.0, 0.0),
        "excrement": (0.0, 0.0),
    }
    assert result == expected_output


def test_fungivore_prey_group_selection(functional_group_list_instance):
    """Test for fungivore diet type selection."""
    from virtual_ecosystem.models.animal.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result = prey_group_selection(
        DietType.FUNGI, 10.0, (0.1, 1000.0), functional_group_list_instance
    )
    expected = {
        "fungi": (0.0, 0.0),
    }
    assert result == expected


@pytest.mark.parametrize(
    "diet_flag, expected",
    [
        # Pure scavengers
        (DietType.WASTE, {"excrement": (0.0, 0.0)}),
        (DietType.CARCASSES, {"carcasses": (0.0, 0.0)}),
        # Combined decay sources
        (
            DietType.WASTE | DietType.CARCASSES,
            {"excrement": (0.0, 0.0), "carcasses": (0.0, 0.0)},
        ),
        # Herbivory + scavenging
        (
            DietType.HERBIVORE | DietType.CARCASSES,
            {
                "plants": (0.0, 0.0),
                "litter": (0.0, 0.0),
                "carcasses": (0.0, 0.0),
            },
        ),
        # Herbivory + waste
        (
            DietType.HERBIVORE | DietType.WASTE,
            {
                "plants": (0.0, 0.0),
                "litter": (0.0, 0.0),
                "excrement": (0.0, 0.0),
            },
        ),
        # Detritivory only
        (
            DietType.DETRITUS,
            {"litter": (0.0, 0.0)},
        ),
    ],
)
def test_combined_diet_flags(diet_flag, expected, functional_group_list_instance):
    """Test combinations of dietary flags and expected prey/resource groups."""
    from virtual_ecosystem.models.animal.scaling_functions import prey_group_selection

    result = prey_group_selection(
        diet_flag,
        mass=10.0,
        terms=(0.1, 1000.0),
        functional_groups=functional_group_list_instance,
    )
    assert result == expected


def test_prey_group_selection_invalid_diet_type(functional_group_list_instance):
    """Test for an invalid diet type input (wrong type)."""
    from virtual_ecosystem.models.animal.scaling_functions import prey_group_selection

    with pytest.raises(TypeError):
        prey_group_selection(
            "omnivore", 10.0, (0.1, 1000.0), functional_group_list_instance
        )


def test_prey_group_selection_mass_and_terms_impact(functional_group_list_instance):
    """Test to ensure `mass` and `terms` don't affect output."""
    from virtual_ecosystem.models.animal.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result_default = prey_group_selection(
        DietType.CARNIVORE, 10.0, (0.1, 1000.0), functional_group_list_instance
    )
    result_diff_mass = prey_group_selection(
        DietType.CARNIVORE, 50.0, (0.1, 1000.0), functional_group_list_instance
    )
    result_diff_terms = prey_group_selection(
        DietType.CARNIVORE, 10.0, (0.5, 500.0), functional_group_list_instance
    )

    assert result_default == result_diff_mass == result_diff_terms


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
    from virtual_ecosystem.models.animal.scaling_functions import background_mortality

    assert background_mortality(input_value) == expected_output, (
        "The mortality rate returned did not match the expected value."
    )


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

    from virtual_ecosystem.models.animal.scaling_functions import senescence_mortality

    if t_to_maturity == 0:
        with pytest.raises(ZeroDivisionError):
            senescence_mortality(lambda_se, t_to_maturity, t_since_maturity)
    else:
        result = senescence_mortality(lambda_se, t_to_maturity, t_since_maturity)
        assert result == pytest.approx(expected_mortality), (
            "The calculated mortality did not match the expected value."
        )


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
    """Test the calculation of starvation mortality based on body mass."""
    from virtual_ecosystem.models.animal.scaling_functions import starvation_mortality

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

    from virtual_ecosystem.models.animal.scaling_functions import alpha_i_k

    calculated_search_rate = alpha_i_k(alpha_0_herb, mass)
    assert calculated_search_rate == pytest.approx(expected_search_rate, rel=1e-6)


@pytest.mark.parametrize(
    "alpha_i_k, B_k_t, A_cell, expected_biomass",
    [
        pytest.param(0.1, 1000, 1, 100000.0, id="standard_scenario"),
        pytest.param(0.2, 1000, 1, 200000.0, id="increased_search_rate"),
        pytest.param(0.1, 2000, 1, 400000.0, id="increased_plant_biomass"),
        pytest.param(0.1, 1000, 2, 25000.0, id="increased_cell_area"),
        pytest.param(0, 1000, 1, 0.0, id="zero_search_rate"),
        pytest.param(0.1, 0, 1, 0.0, id="zero_plant_biomass"),
    ],
)
def test_k_i_k(alpha_i_k, B_k_t, A_cell, expected_biomass):
    """Testing the potential biomass eaten calculation for various scenarios."""
    from virtual_ecosystem.models.animal.scaling_functions import k_i_k

    calculated_biomass = k_i_k(alpha_i_k, B_k_t, A_cell)
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
    from virtual_ecosystem.models.animal.scaling_functions import H_i_k

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

    from virtual_ecosystem.models.animal.scaling_functions import theta_opt_i

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
    from virtual_ecosystem.models.animal.scaling_functions import w_bar_i_j

    if expect_exception:
        with pytest.raises((ZeroDivisionError, ValueError)):
            w_bar_i_j(mass_predator, mass_prey, theta_opt_i, sigma_opt_pred_prey)
    else:
        result = w_bar_i_j(mass_predator, mass_prey, theta_opt_i, sigma_opt_pred_prey)
        assert 0.0 <= result <= 1.0, (
            "Result is outside the expected probability range [0.0, 1.0]"
        )


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
    from virtual_ecosystem.models.animal.scaling_functions import alpha_i_j

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
    from virtual_ecosystem.models.animal.scaling_functions import k_i_j

    # Handle special case where division by zero might occur
    if A_cell == 0:
        with pytest.raises(ZeroDivisionError):
            k_i_j(alpha_i_j, N_i_t, A_cell, theta_i_j)
    else:
        calculated_output = k_i_j(alpha_i_j, N_i_t, A_cell, theta_i_j)
        assert calculated_output == pytest.approx(expected_output, rel=1e-6)


@pytest.mark.parametrize(
    "h_pred_0, M_ref, M_i_t, b_pred, prey_mass, expected_handling_time",
    [
        pytest.param(1.0, 10.0, 10.0, 0.75, 1.0, 1.0, id="basic_scenario"),
        pytest.param(1.0, 10.0, 5.0, 0.75, 1.0, 1.6817928, id="M_i_t_half_of_M_ref"),
        pytest.param(1.0, 10.0, 20.0, 0.75, 1.0, 0.5946036, id="M_i_t_double_of_M_ref"),
        pytest.param(2.0, 10.0, 10.0, 0.75, 1.0, 2.0, id="increased_h_pred_0"),
        pytest.param(1.0, 10.0, 10.0, 1.0, 1.0, 1.0, id="increased_b_pred"),
        pytest.param(
            1.0, 10.0, 10.0, 0.75, 5.0, 5.0, id="larger_prey_mass_scales_linearly"
        ),
        pytest.param(1.0, 10.0, 10.0, 0.75, 0.0, 0.0, id="zero_prey_mass_returns_zero"),
        pytest.param(1.0, 0.0, 10.0, 0.75, 1.0, 0.0, id="zero_M_ref_leads_to_zero"),
        pytest.param(
            1.0, 10.0, 0.0, 0.75, 1.0, float("inf"), id="zero_M_i_t_expect_inf"
        ),
    ],
)
def test_H_i_j(h_pred_0, M_ref, M_i_t, b_pred, prey_mass, expected_handling_time):
    """Test handling time calculation for various predator mass and prey mass inputs."""
    from virtual_ecosystem.models.animal.scaling_functions import H_i_j

    if M_i_t == 0:
        with pytest.raises(ZeroDivisionError):
            H_i_j(h_pred_0, M_ref, M_i_t, b_pred, prey_mass)
    else:
        result = H_i_j(h_pred_0, M_ref, M_i_t, b_pred, prey_mass)
        assert result == pytest.approx(expected_handling_time, rel=1e-6)


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
    from virtual_ecosystem.models.animal.scaling_functions import (
        juvenile_dispersal_speed,
    )

    calculated_speed = juvenile_dispersal_speed(
        current_mass, V_disp, M_disp_ref, o_disp
    )
    assert calculated_speed == pytest.approx(expected_speed, rel=1e-6)


@pytest.mark.parametrize(
    "mass_kg, terms, expected_m2",
    [
        pytest.param(0.01, (-6.09, 1.13), 305.6, id="small"),
        pytest.param(1.0, (-6.09, 1.13), 55_610.0, id="medium"),
        pytest.param(50.0, (-6.09, 1.13), 4_625_000.0, id="large"),
        pytest.param(0.01, (3.60, 0.48), 1_105_249.0, id="small_open"),
        pytest.param(1.0, (3.60, 0.48), 10_079_991.0, id="medium_open"),
        pytest.param(50.0, (3.60, 0.48), 65_912_189.0, id="large_open"),
    ],
)
def test_territory_size(mass_kg, terms, expected_m2):
    """Test territory_size returns expected m² and scales correctly with body mass."""
    from virtual_ecosystem.models.animal.scaling_functions import territory_size

    assert territory_size(mass_kg, terms) == pytest.approx(expected_m2, rel=1e-3)
    assert territory_size(2 * mass_kg, terms) / territory_size(mass_kg, terms) == (
        pytest.approx(2 ** terms[1], rel=1e-6)
    )
    assert territory_size(mass_kg, terms) < territory_size(mass_kg * 10, terms)


@pytest.mark.parametrize(
    "annual_mean_temp, annual_temp_sd, m_tsm, c_tsm, expected",
    [
        pytest.param(20.0, 5.0, 1.53, 1.51, 29.16, id="standard"),
        pytest.param(0.0, 0.0, 1.53, 1.51, 1.51, id="zero_mean_and_sd"),
    ],
)
def test_t_opt_ectotherm(annual_mean_temp, annual_temp_sd, m_tsm, c_tsm, expected):
    """Test optimal activity temperature calculation for terrestrial ectotherms."""
    from virtual_ecosystem.models.animal.scaling_functions import t_opt_ectotherm

    assert t_opt_ectotherm(
        annual_mean_temp, annual_temp_sd, m_tsm, c_tsm
    ) == pytest.approx(expected)


@pytest.mark.parametrize(
    "annual_mean_temp, annual_temp_sd, m_tol, c_tol, expected",
    [
        pytest.param(20.0, 5.0, 1.6, 6.61, 34.61, id="standard"),
        pytest.param(0.0, 0.0, 1.6, 6.61, 6.61, id="zero_mean_and_sd"),
    ],
)
def test_t_max_crit_ectotherm(annual_mean_temp, annual_temp_sd, m_tol, c_tol, expected):
    """Test upper critical temperature calculation for terrestrial ectotherms."""
    from virtual_ecosystem.models.animal.scaling_functions import t_max_crit_ectotherm

    assert t_max_crit_ectotherm(
        annual_mean_temp, annual_temp_sd, m_tol, c_tol
    ) == pytest.approx(expected)


@pytest.mark.parametrize(
    "t_max_crit, t_opt, expected",
    [
        pytest.param(34.61, 29.16, 27.343333333333334, id="standard"),
        pytest.param(10.0, 10.0, 10.0, id="equal_max_and_opt"),
    ],
)
def test_t_min_crit_ectotherm(t_max_crit, t_opt, expected):
    """Test lower critical temperature calculation for terrestrial ectotherms."""
    from virtual_ecosystem.models.animal.scaling_functions import t_min_crit_ectotherm

    assert t_min_crit_ectotherm(t_max_crit, t_opt) == pytest.approx(expected)


@pytest.mark.parametrize(
    "temperature, diurnal_temp_range, t_max_crit, expected",
    [
        pytest.param(20.0, 10.0, 40.0, 0.0, id="always_below_max"),
        pytest.param(20.0, 10.0, 10.0, 1.0, id="always_above_max"),
        pytest.param(20.0, 10.0, 22.0, 0.36901011956554536, id="partial_overlap"),
    ],
)
def test_p_above_t_max(temperature, diurnal_temp_range, t_max_crit, expected):
    """Test proportion of day above upper critical temperature."""
    from virtual_ecosystem.models.animal.scaling_functions import p_above_t_max

    assert p_above_t_max(temperature, diurnal_temp_range, t_max_crit) == pytest.approx(
        expected
    )


@pytest.mark.parametrize(
    "temperature, diurnal_temp_range, t_min_crit, expected",
    [
        pytest.param(20.0, 10.0, -5.0, 0.0, id="always_above_min"),
        pytest.param(20.0, 10.0, 30.0, 1.0, id="always_below_min"),
        pytest.param(20.0, 10.0, 18.0, 0.3690101195655454, id="partial_overlap"),
    ],
)
def test_p_below_t_min(temperature, diurnal_temp_range, t_min_crit, expected):
    """Test proportion of day below lower critical temperature."""
    from virtual_ecosystem.models.animal.scaling_functions import p_below_t_min

    assert p_below_t_min(temperature, diurnal_temp_range, t_min_crit) == pytest.approx(
        expected
    )


@pytest.mark.parametrize(
    "metabolic_type, temperature, diurnal_temp_range, expected",
    [
        pytest.param("endothermic", 0.0, 4.0, 1.0, id="endotherm_always_active"),
        pytest.param("ectothermic", 31.0, 4.0, 1.0, id="ectotherm_fully_within_window"),
        pytest.param("ectothermic", 10.0, 4.0, 0.0, id="ectotherm_always_too_cold"),
        pytest.param("ectothermic", 40.0, 4.0, 0.0, id="ectotherm_always_too_hot"),
        pytest.param(
            "ectothermic",
            30.0,
            10.0,
            0.5517546068733064,
            id="ectotherm_partial_overlap",
        ),
    ],
)
def test_activity_window(metabolic_type, temperature, diurnal_temp_range, expected):
    """Test activity window fraction across endotherm and ectotherm scenarios."""
    from virtual_ecosystem.models.animal.animal_traits import MetabolicType
    from virtual_ecosystem.models.animal.scaling_functions import activity_window

    result = activity_window(
        metabolic_type=MetabolicType(metabolic_type),
        temperature=temperature,
        diurnal_temp_range=diurnal_temp_range,
        annual_mean_temp=20.0,
        annual_temp_sd=5.0,
    )
    assert result == pytest.approx(expected)
