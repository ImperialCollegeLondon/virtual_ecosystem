"""The `models.animal.scaling_functions` module contains a set of functions containing
scaling equations" (relationships between body-mass and a trait) required by the broader
:mod:`~virtual_ecosystem.models.animal` module

To Do:
- streamline units of scaling functions [kg]->[kg] etc

"""  # noqa: D205, D415

from collections.abc import Sequence
from math import asin, exp, log, pi

import numpy as np
from scipy.special import expit

from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.animal.animal_traits import (
    DietType,
    MetabolicType,
)
from virtual_ecosystem.models.animal.functional_group import FunctionalGroup
from virtual_ecosystem.models.animal.model_config import AnimalConstants


def damuths_law(mass: float, terms: tuple) -> float:
    """The function set initial population densities .

        Currently, this function just employs Damuth's Law (Damuth 1987) for
        terrestrial herbivorous mammals. Later, it will be expanded to other types.
        Damuth assumes body mass in g and final density in indiv/km2.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        terms: The tuple of population density terms used, default to Damuth.

    Returns:
        The population density of that AnimalCohort [individuals/m2].

    """

    individual_density_km2 = terms[1] * (mass * 1000) ** terms[0]

    individual_density_m2 = individual_density_km2 / 1e6

    return individual_density_m2


def madingley_individuals_density(adult_mass: float, terms: tuple) -> float:
    """Estimate individual density from adult mass using Madingley biomass scaling.

    This converts biomass density scaling into individual density scaling by dividing
    biomass density by adult body mass.

        Biomass Density = B * Mass^A
        Individuals Density = Biomass Density / Mass = B * Mass^(A - 1)

    Args:
        adult_mass: Adult body mass of the cohort (kg).
        terms: A tuple (A, B) with exponent and scalar for the biomass scaling law.

    Returns:
        Estimated individual density (individuals/m²).
    """
    exponent, scalar = terms

    mass_g = adult_mass * 1000

    biomass_density_g_km2 = scalar * mass_g**exponent

    individual_density_km2 = biomass_density_g_km2 / mass_g

    individual_density_m2 = individual_density_km2 / 1e6

    return individual_density_m2


def metabolic_rate(
    mass: float,
    temperature: float,
    terms: dict,
    metabolic_type: MetabolicType,
    sigma_f_t: float,
    metabolic_scaling_coefficients: tuple[
        float, float
    ] = AnimalConstants().metabolic_scaling_coefficients,
    boltzmann_constant: float = CoreConstants().boltzmann_constant,
) -> float:
    r"""Calculates metabolic rate in grams of body mass per day.

    This follows the Madingley implementation, assuming a power-law relationship with
    mass and an exponential relationship with temperature.

    .. math::
        \Delta M_i^{metab} = E_S \left[
            \varsigma_{f(t)} \cdot I_{0,f}^{FMR}
                \cdot e^{-E_A / k_B T^{K,body}} \cdot M_{i(t)}^{b_f^{FMR}}
            + (1 - \varsigma_{f(t)}) \cdot I_0^{BMR}
                \cdot e^{-E_A / k_B T^{K,body}} \cdot M_{i(t)}^{b^{BMR}}
        \right] \Delta t_d

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        temperature: The temperature [Celsius] of the environment.
        terms: The tuple of metabolic rate terms used.
        metabolic_type: The metabolic type of the animal [ENDOTHERMIC or ECTOTHERMIC].
        sigma_f_t: Activity window fraction in [0, 1].
        metabolic_scaling_coefficients: A 2-tuple of - the energy-to-
            mass conversion constant and the aggregate activation energy of metabolic
            reactions.
        boltzmann_constant: The Boltzmann constant ($k_B$)

    Returns:
        The metabolic rate of a single individual [kg/day].
    """

    Es, Ea = metabolic_scaling_coefficients
    kB = boltzmann_constant
    mass_g = mass * 1000  # convert kg to g

    if metabolic_type == MetabolicType.ENDOTHERMIC:
        Ib, bf = terms["basal"]
        If, bb = terms["field"]
        Tk = 310.0  # fixed body temperature for endotherms [K]
    elif metabolic_type == MetabolicType.ECTOTHERMIC:
        Ib, bf = terms["basal"]
        If, bb = terms["field"]
        Tk = temperature + 274.15  # body temperature equals ambient [K]
    else:
        raise ValueError(f"Invalid metabolic type: {metabolic_type}")

    return (
        Es
        * (
            (sigma_f_t * If * exp(-(Ea / (kB * Tk)))) * mass_g**bf
            + ((1 - sigma_f_t) * Ib * exp(-(Ea / (kB * Tk)))) * mass_g**bb
        )
        / 1000  # convert g back to kg
    )


def prey_group_selection(
    diet_type: DietType,
    mass: float,
    terms: tuple,
    functional_groups: Sequence[FunctionalGroup],
) -> dict[str, tuple[float, float]]:
    """Selects prey groups available to a consumer based on diet and available groups.

    Args:
        diet_type: Consumer's DietType flag(s).
        mass: Mass of the consumer (currently unused).
        terms: Placeholder for mass-scaling logic.
        functional_groups: All functional groups in the model.

    Returns:
        A dictionary mapping prey/resource group names to mass ranges.
    """
    from virtual_ecosystem.models.animal.animal_traits import TaxaType

    result: dict[str, tuple[float, float]] = {}

    # Living animal prey filtering
    for fg in functional_groups:
        # Vertebrate prey (birds, mammals, amphibians)
        if diet_type & (
            DietType.VERTEBRATES | DietType.BLOOD | DietType.FISH
        ) and fg.taxa in {
            TaxaType.BIRD,
            TaxaType.MAMMAL,
            TaxaType.AMPHIBIAN,
            TaxaType.REPTILE,
        }:
            result[fg.name] = (0.0001, 1000.0)

        # Invertebrate prey
        elif diet_type & DietType.INVERTEBRATES and fg.taxa == TaxaType.INVERTEBRATE:
            result[fg.name] = (0.0001, 1000.0)

    # Plant-based resources
    if diet_type & (
        DietType.FOLIAGE
        | DietType.FLOWERS
        | DietType.FRUIT
        | DietType.SEEDS
        | DietType.NECTAR
    ):
        result["plants"] = (0.0, 0.0)

    # Scavenging resources
    if diet_type & DietType.CARCASSES:
        result["carcasses"] = (0.0, 0.0)
    if diet_type & DietType.WASTE:
        result["excrement"] = (0.0, 0.0)
    if diet_type & DietType.DETRITUS:
        result["litter"] = (0.0, 0.0)
    if diet_type & DietType.MUSHROOMS:
        # mushroom pool
        result["fungal_fruiting_bodies"] = (0.0, 0.0)
    if diet_type & DietType.FUNGI:
        # Soil fungi pool
        result["fungi"] = (0.0, 0.0)
    if diet_type & DietType.POM:
        result["pom"] = (0.0, 0.0)
    if diet_type & DietType.BACTERIA:
        result["bacteria"] = (0.0, 0.0)

    if not result:
        raise ValueError(f"No prey groups matched for diet type: {diet_type}")

    return result


def background_mortality(u_bg: float) -> float:
    """Constant background rate of wastebasket mortality.

    This function does nothing but return a constant at the moment.
    I am leaving it in so there is a clear way to alter the assumptions about
    background mortality as we move into testing and validation.

    Madingley

    Args:
        u_bg: The constant of background mortality [day^-1].

    Returns:
        The background rate of mortality faced by a cohort [day^-1].

    """

    return u_bg


def senescence_mortality(
    lambda_se: float, t_to_maturity: float, t_since_maturity: float
) -> float:
    """Age-based mortality.

    Madingley describes the equation as exp(time_to_maturity/time_since_maturity) but I
    suspect this is an error and that it should be inverted. If, for example, it took
    1000 days to reach maturity and the cohort had been mature for 1 day, then the
    instantaneous rate of senescence mortality would be lambda_se * exp(1000/1). This
    would also mean that the rate of senescence would decrease over time. Therefore, I
    have inverted the relationship below.

    TODO: Check Madingley code for function implementation

    Args:
        lambda_se: The instantaneous rate of senescence mortality at point of maturity
                    [day^-1].
        t_to_maturity: The time it took the cohort to reach maturity [days].
        t_since_maturity: The time elapsed since the cohort reached maturity [days].

    Returns:
        The rate of senescence mortality faced by an animal cohort [day^-1].

    """

    t_pm = t_to_maturity  # time it took to reach maturity
    t_bm = t_since_maturity  # time since maturity

    u_se = lambda_se * exp(t_bm / t_pm)

    return u_se


def starvation_mortality(
    lambda_max: float, J_st: float, zeta_st: float, mass_current: float, mass_max: float
) -> float:
    """Mortality from body-mass loss.

    There is a error in the madingley paper that does not follow their source code. The
    paper uses exp(k) instead of exp(-k).

    Args:
        lambda_max: The maximum possible instantaneous fractional starvation mortality
            rate. [day^-1]
        J_st: Determines the inflection point of the logistic function describing ratio
            of the realised mortality rate to the maximum rate. [unitless]
        zeta_st:The scaling of the logistic function describing the ratio of the
            realised mortality rate to the maximum rate. [unitless]
        mass_current: The current mass of the animal cohort [kg].
        mass_max: The maximum body mass ever achieved by individuals of this type [kg].

    Returns:
        The rate of mortality from starvation based on current body-mass. [day^-1]

    """

    M_i_t = mass_current
    M_i_max = mass_max
    k = -(M_i_t - J_st * M_i_max) / (zeta_st * M_i_max)  # extra step to follow source
    u_st = lambda_max * expit(k)

    return u_st


def alpha_i_k(alpha_0_herb: float, mass: float) -> float:
    """Effective rate at which an individual herbivore searches its environment.

    This is linear scaling of herbivore search times with current body mass.

    TODO: Update name

    Madingley

    Args:
        alpha_0_herb: Effective rate per unit body mass at which a herbivore searches
          its environment in m2/(day*g).
        mass: The current body mass of the foraging herbivore in g.

    Returns:
        A float of the effective search rate in [m2/day].

    """

    return alpha_0_herb * mass


def k_i_k(alpha_i_k: float, B_k_t: float, A_cell: float) -> float:
    """The potential biomass (g) of plant k eaten by cohort i, per day.

    TODO: update name

    Madingley

    Args:
        alpha_i_k: Effective rate at which an individual herbivore searches its
          environment.
        B_k_t: Plant resource bool biomass.
        A_cell: The area of one cell [standard = 1 ha]

    Returns:
        A float of The potential biomass (g) of plant k eating by cohort i, per day
        [g/day]

    """

    return alpha_i_k * ((B_k_t) / A_cell) ** 2


def H_i_k(h_herb_0: float, M_ref: float, M_i_t: float, b_herb: float) -> float:
    """Handling time of plant resource k by cohort i.

    Time (days) for an individual of cohort i to handle 1 gram of plant resource.

    TODO: update name

    Madingley

    Args:
        h_herb_0: Time in days that it would take a herbivore of mass = M_ref to handle
          1g of autotroph mass.
        M_ref: Reference body mass.
        M_i_t: Current herbivore mass
        b_herb: Exponent of the power-law function relating the handling time of
          autotroph matter to herbivore mass

    Returns:
        A float of the handling time (days).

    """

    return h_herb_0 * (M_ref / M_i_t) ** b_herb


def theta_opt_i(
    theta_opt_min_f: float, theta_opt_f: float, sigma_opt_f: float
) -> float:
    """Optimum predator-prey mass ratio.

    TODO: update name

    Madingley

    Args:
        theta_opt_min_f: The minimum optimal prey-predator body mass ratio.
        theta_opt_f: The mean optimal prey-predator body mass ratio, from which actual
            cohort optima are drawn.
        sigma_opt_f: The standard deviation of optimal predator-prey mass ratios among
          cohorts.

    Returns:
        A float measure of the optimum ratio.

    """

    return max(theta_opt_min_f, np.random.normal(theta_opt_f, sigma_opt_f))


def w_bar_i_j(
    mass_predator: float,
    mass_prey: float,
    theta_opt_i: float,
    sigma_opt_pred_prey: float,
) -> float:
    """The probability of successfully capturing a prey item.

    TODO: update name

    Madingley

    Args:
        mass_predator: Current mass of the predator..
        mass_prey: Current mass of the prey.
        theta_opt_i: The optimum predator-prey mass ratio.
        sigma_opt_pred_prey: The standard deviation of the mass ratio.

    Returns:
        A float probability [0.0-1.0] that a predation encounter is successful.

    """

    return exp(
        -(
            ((log(mass_prey / mass_predator) - log(theta_opt_i)) / sigma_opt_pred_prey)
            ** 2
        )
    )


def alpha_i_j(alpha_0_pred: float, mass: float, w_bar_i_j: float) -> float:
    """Rate at which an individual predator searches its environment and kills prey.

    This is linear scaling of herbivore search times with current body mass.

    TODO: update name

    Madingley


    Args:
        alpha_0_pred: Constant describing effective rate per unit body mass at which any
          predator searches its environment in m2/(day*g).
        mass: The current body mass of the foraging herbivore.
        w_bar_i_j: The probability of successfully capturing a prey item.

    Returns:
        A float of the effective search rate in [m2/day]

    """

    return alpha_0_pred * mass * w_bar_i_j


def k_i_j(
    alpha_i_j: float, N_i_t: float, intersection_area: float, theta_i_j: float
) -> float:
    """Potential number of prey items eaten off j by i.

    TODO: update name

    Madingley

    Args:
        alpha_i_j: Rate at which an individual predator searches its environment and
            kills prey in m2/(day*g).
        N_i_t: Number of consumer individuals.
        intersection_area: The overlapping area between predator and prey territories
          in m2.
        theta_i_j: The cumulative density of organisms with a mass lying within the
            same predator specific mass bin.

    Returns:
        Potential number of prey items eaten off j by i [integer number of individuals]
    """
    return alpha_i_j * (N_i_t / intersection_area) * theta_i_j


def H_i_j(
    h_pred_0: float, M_ref: float, M_i_t: float, b_pred: float, prey_mass: float
) -> float:
    """Handling time of prey cohort j by cohort i.

    Time (days) for an individual of cohort i to handle 1 individual of cohort j.

    TODO: update name

    Madingley

    Args:
        h_pred_0: Time that it would take a predator of body mass equal to the reference
          mass, to handle a prey individual of body mass equal to one gram.
        M_ref: Reference body mass.
        M_i_t: Current predator mass.
        b_pred: Exponent of the power-law function relating the handling time of
          prey to predator mass.
        prey_mass: the mass of prey being handled.

    Returns:
        A float of the handling time (days).

    """

    return h_pred_0 * ((M_ref / M_i_t) ** b_pred) * prey_mass


def juvenile_dispersal_speed(
    current_mass: float, V_disp: float, M_disp_ref: float, o_disp: float
) -> float:
    """Dispersal speed of cohorts during diffusive natal dispersal event [km/month].

    Madingley

    Args:
        current_mass: The mass of an individual of the cohort during the current time
            step [kg].
        V_disp: Diffusive dispersal speed on an individual with reference body-mass.
        M_disp_ref: A reference body-mass.
        o_disp: The power-law exponent for the mass-dispersal speed scaling
          relationship.

    Returns:
        The dispersal speed of a juvenile cohort in km/month.

    """

    return V_disp * (current_mass / M_disp_ref) ** o_disp


def territory_size(
    mass_kg: float,
    terms: tuple[float, float],
) -> float:
    """Allometric scaling of territory size from body mass.

    TODO: Decide whether to use current mass or adult mass.

    Args:
        mass_kg: Body mass of the animal [kg].
        terms: A tuple (intercept, exponent) for the log-log scaling relationship,
            where intercept and exponent act on ln(BM_g).

    Returns:
        Territory size [m²].
    """

    intercept, exponent = terms
    ln_territory_ha = intercept + exponent * log(mass_kg * 1000)
    return exp(ln_territory_ha) * 10_000


def bfs_territory(
    centroid_key: int, target_cell_number: int, cell_nx: int, cell_ny: int
) -> list[int]:
    """Performs breadth-first search (BFS) to generate a list of territory cells.

    BFS does some slightly weird stuff on a grid of squares but behaves properly on a
    graph. As we are talking about moving to a graph anyway, I can leave it like this
    and make adjustments for diagonals if we decide to stay with squares/cells.

    TODO: Revise for diagonals if we stay on grid squares/cells.
    TODO: might be able to save time with an ifelse for small territories
    TODO: scaling territories is a temporary home while i rework territories
    TODO: replace pop with collections.deque

    Args:
        centroid_key: The community key anchoring the territory.
        target_cell_number: The number of grid cells in the territory.
        cell_nx: Number of cells along the x-axis.
        cell_ny: Number of cells along the y-axis.

    Returns:
        A list of grid cell keys representing the territory.
    """

    centroid_key = int(centroid_key)
    target_cell_number = int(target_cell_number)
    cell_nx = int(cell_nx)
    cell_ny = int(cell_ny)

    # Convert centroid key to row and column indices
    row, col = divmod(centroid_key, cell_nx)

    # Initialize the territory cells list with the centroid key
    territory_cells = [centroid_key]

    # Define the possible directions for BFS traversal: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Set to keep track of visited cells to avoid revisiting
    visited = set(territory_cells)

    # Queue for BFS, initialized with the starting position (row, col)
    queue = [(row, col)]

    # Perform BFS until the queue is empty or we reach the target number of cells
    while queue and len(territory_cells) < target_cell_number:
        # Dequeue the next cell to process
        r, c = queue.pop(0)

        # Explore all neighboring cells in the defined directions
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # Check if the new cell is within grid bounds
            if 0 <= nr < cell_ny and 0 <= nc < cell_nx:
                new_cell = nr * cell_nx + nc
                # If the cell hasn't been visited, mark it as visited and add to the
                # territory
                if new_cell not in visited:
                    visited.add(new_cell)
                    territory_cells.append(new_cell)
                    queue.append((nr, nc))
                    # If we have reached the target number of cells, exit the loop
                    if len(territory_cells) >= target_cell_number:
                        break

    return territory_cells


def t_opt_ectotherm(
    annual_mean_temp: float,
    annual_temp_sd: float,
    m_tsm: float,
    c_tsm: float,
) -> float:
    r"""Optimal activity temperature for a terrestrial ectothermic functional group.

    Implements Madingley eq. 47:

    .. math::

        T_{opt} = m_{tsm} \\cdot \\sigma_{T_{Annual}^C} + c_{tsm} + T_{Annual}^C

    Args:
        annual_mean_temp: Annual mean ambient temperature $T_{Annual}^C$ [°C].
        annual_temp_sd: Standard deviation of monthly temperatures across the
            climatological year $\\sigma_{T_{Annual}^C}$ [°C].
        m_tsm: Slope of the variability-optimal temperature relationship.
        c_tsm: Intercept of the variability-optimal temperature relationship [°C].

    Returns:
        Optimal activity temperature [°C].
    """

    return m_tsm * annual_temp_sd + c_tsm + annual_mean_temp


def t_max_crit_ectotherm(
    annual_mean_temp: float,
    annual_temp_sd: float,
    m_tol: float,
    c_tol: float,
) -> float:
    r"""Upper critical temperature for a terrestrial ectothermic functional group.

    Implements Madingley eq. 45:

    .. math::

        T_{\\max,f}^{crit} = m_{tol,terrestrial} \\cdot \\sigma_{T_{Annual}^C}
            + c_{tol,terrestrial} + T_{Annual}^C

    Args:
        annual_mean_temp: Annual mean ambient temperature $T_{Annual}^C$ [°C].
        annual_temp_sd: Standard deviation of monthly temperatures across the
            climatological year $\\sigma_{T_{Annual}^C}$ [°C].
        m_tol: Slope of the variability-upper-critical-temperature relationship.
        c_tol: Intercept of the variability-upper-critical-temperature
            relationship [°C].

    Returns:
        Upper critical temperature [°C].
    """
    return m_tol * annual_temp_sd + c_tol + annual_mean_temp


def t_min_crit_ectotherm(t_max_crit: float, t_opt: float) -> float:
    r"""Lower critical temperature for a terrestrial ectothermic functional group.

    Implements Madingley eq. 46:

    .. math::

        T_{\\min,f}^{crit} = T_{opt,f}
            - 4 \\cdot \\frac{T_{\\max,f}^{crit} - T_{opt,f}}{12}

    Args:
        t_max_crit: Upper critical temperature $T_{\\max,f}^{crit}$ [°C].
        t_opt: Optimal activity temperature $T_{opt,f}$ [°C].

    Returns:
        Lower critical temperature [°C].
    """
    return t_opt - 4.0 * (t_max_crit - t_opt) / 12.0


def p_above_t_max(
    temperature: float,
    diurnal_temp_range: float,
    t_max_crit: float,
) -> float:
    r"""Proportion of the day during which temperature exceeds the upper critical limit.

    Models the daily temperature cycle as a sine wave centred on the monthly mean
    ``temperature`` with amplitude ``diurnal_temp_range / 2``. Returns the fraction
    of the period for which that cycle exceeds ``t_max_crit`` (Madingley eq. 43).

    .. math::

        p_{Above,f} = \\frac{\\pi/2 - \\sin^{-1}
            \\left[\\text{clamp}\\left(
                \\frac{2(T_{\\max,f}^{crit} - T_C)}{\\Delta T_{Diurnal}^C},
                -1, 1\\right)\\right]}{\\pi}

    The piecewise clamping ensures the arcsin receives a valid argument when the
    threshold lies entirely outside the daily temperature range, which is equivalent
    to the explicit ``if`` branches in the original Madingley formulation.

    Args:
        temperature: Monthly mean ambient temperature $T_C$ [°C].
        diurnal_temp_range: Monthly mean diurnal temperature range
            $\\Delta T_{Diurnal}^C$ [°C].
        t_max_crit: Upper critical temperature $T_{\\max,f}^{crit}$ [°C].

    Returns:
        Proportion of the day that is too hot for activity [0, 1].
    """
    if diurnal_temp_range <= 0.0:
        # With no diurnal variation the day is fully on one side of the threshold.
        return 1.0 if temperature > t_max_crit else 0.0

    arg = max(-1.0, min(1.0, 2.0 * (t_max_crit - temperature) / diurnal_temp_range))
    return (pi / 2.0 - asin(arg)) / pi


def p_below_t_min(
    temperature: float,
    diurnal_temp_range: float,
    t_min_crit: float,
) -> float:
    r"""Proportion of the day during which temperature is below the lower limit.

    Mirrors :func:`p_above_t_max` for the cold end of the activity window (Madingley
    eq. 44). The :math:`1 - {\\ldots}` flip converts "proportion of the day above
    ``t_min_crit``" into "proportion of the day below ``t_min_crit``".

    .. math::

        p_{Below,f} = 1 - \\frac{\\pi/2 - \\sin^{-1}
            \\left[\\text{clamp}\\left(
                \\frac{2(T_{\\min,f}^{crit} - T_C)}{\\Delta T_{Diurnal}^C},
                -1, 1\\right)\\right]}{\\pi}

    Args:
        temperature: Monthly mean ambient temperature $T_C$ [°C].
        diurnal_temp_range: Monthly mean diurnal temperature range
            $\\Delta T_{Diurnal}^C$ [°C].
        t_min_crit: Lower critical temperature $T_{\\min,f}^{crit}$ [°C].

    Returns:
        Proportion of the day that is too cold for activity [0, 1].
    """
    if diurnal_temp_range <= 0.0:
        # With no diurnal variation the day is fully on one side of the threshold.
        return 1.0 if temperature < t_min_crit else 0.0

    arg = max(-1.0, min(1.0, 2.0 * (t_min_crit - temperature) / diurnal_temp_range))
    return 1.0 - (pi / 2.0 - asin(arg)) / pi


def activity_window(
    metabolic_type: MetabolicType,
    temperature: float,
    diurnal_temp_range: float,
    annual_mean_temp: float,
    annual_temp_sd: float,
    t_opt: float | None = None,
    t_max_crit: float | None = None,
    t_min_crit: float | None = None,
    constants: AnimalConstants = AnimalConstants(),
) -> float:
    r"""Proportion of the timestep suitable for a cohort to be active.

    Implements Madingley eqs. 41-47:

    * Endotherms are active for the full timestep (eq. 41).
    * Terrestrial ectotherms are limited to the fraction of the day within their
      thermal tolerance window, derived from the diurnal temperature cycle and
      climatological statistics (eq. 42).

    .. math::

        \\varsigma_{f(t)} = \\begin{cases}
            1 & \\text{if } f \\text{ is endotherm} \\\\
            1 - (p_{Above,f} + p_{Below,f}) & \\text{if } f \\text{ is ectotherm}
        \\end{cases}

    The result is clamped to [0, 1] to guard against floating-point cases where
    ``p_above + p_below`` marginally exceeds 1.

    If ``t_opt``, ``t_max_crit``, and ``t_min_crit`` are all provided they are
    used directly, bypassing the toy-parameter derivation from climate statistics.
    If any are ``None`` the full derivation from ``annual_mean_temp`` and
    ``annual_temp_sd`` is used instead.

    Args:
        metabolic_type: Whether the cohort is endothermic or ectothermic.
        temperature: Monthly mean ambient temperature $T_C$ [°C].
        diurnal_temp_range: Monthly mean diurnal temperature range
            $\\Delta T_{Diurnal}^C$ [°C].
        annual_mean_temp: Annual mean ambient temperature $T_{Annual}^C$ [°C].
        annual_temp_sd: Standard deviation of monthly temperatures across the
            climatological year $\\sigma_{T_{Annual}^C}$ [°C].
        t_opt: Optional optimal activity temperature [°C]. If provided alongside
            ``t_max_crit`` and ``t_min_crit``, overrides the toy-parameter
            derivation.
        t_max_crit: Optional upper critical temperature [°C]. See ``t_opt``.
        t_min_crit: Optional lower critical temperature [°C]. See ``t_opt``.
        constants: Animal constants supplying the four activity window parameters,
            used only when ``t_opt``, ``t_max_crit``, and ``t_min_crit`` are not
            all provided.

    Returns:
        Activity window fraction in [0, 1].
    """
    if metabolic_type == MetabolicType.ENDOTHERMIC:
        return 1.0

    if t_opt is not None and t_max_crit is not None and t_min_crit is not None:
        t_opt_val = t_opt
        t_max_val = t_max_crit
        t_min_val = t_min_crit
    else:
        t_opt_val = t_opt_ectotherm(
            annual_mean_temp, annual_temp_sd, constants.m_tsm, constants.c_tsm
        )
        t_max_val = t_max_crit_ectotherm(
            annual_mean_temp, annual_temp_sd, constants.m_tol, constants.c_tol
        )
        t_min_val = t_min_crit_ectotherm(t_max_val, t_opt_val)

    p_above = p_above_t_max(temperature, diurnal_temp_range, t_max_val)
    p_below = p_below_t_min(temperature, diurnal_temp_range, t_min_val)

    return max(0.0, 1.0 - (p_above + p_below))
