"""The `models.animal.scaling_functions` module contains a set of functions containing
scaling equations" (relationships between body-mass and a trait) required by the broader
:mod:`~virtual_ecosystem.models.animal` module

To Do:
- streamline units of scaling functions [kg]->[kg] etc

"""  # noqa: D205, D415

from collections.abc import Sequence
from math import exp, log

import numpy as np

from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.animal.animal_traits import DietType, MetabolicType
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
    metabolic_scaling_coefficients: tuple[
        float, float, float
    ] = AnimalConstants().metabolic_scaling_coefficients,
    boltzmann_constant: float = CoreConstants().boltzmann_constant,
) -> float:
    r"""Calculates metabolic rate in grams of body mass per day.

    This follows the Madingley implementation, assuming a power-law relationship with
    mass and an exponential relationship with temperature.

    TODO: Implement activity windows to properly parameterize sigma.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        temperature: The temperature [Celsius] of the environment.
        terms: The tuple of metabolic rate terms used.
        metabolic_type: The metabolic type of the animal [ENDOTHERMIC or ECTOTHERMIC].
        metabolic_scaling_coefficients: A tuple providing the $E_s, \sigma, E_a$
            coefficients of the Madingley metabolic rate model (see
            :attr:`~virtual_ecosystem.models.animal.model_config.AnimalConstants.metabolic_scaling_coefficients`)
        boltzmann_constant: The Boltzmann constant ($k_B$)

    Returns:
        The metabolic rate of an individual of the given cohort in [g/d].
    """

    Es, sig, Ea = metabolic_scaling_coefficients
    kB = boltzmann_constant
    mass_g = mass * 1000  # convert mass to grams

    if metabolic_type == MetabolicType.ENDOTHERMIC:
        Ib, bf = terms["basal"]  # field metabolic constant and exponent
        If, bb = terms["field"]  # basal metabolic constant and exponent
        Tk = 310.0  # body temperature of the individual (K)
        return (
            Es
            * (
                (sig * If * exp(-(Ea / (kB * Tk)))) * mass_g**bf
                + ((1 - sig) * Ib * exp(-(Ea / (kB * Tk)))) * mass_g**bb
            )
            / 1000  # convert back to kg
        )
    elif metabolic_type == MetabolicType.ECTOTHERMIC:
        Ib, bf = terms["basal"]  # field metabolic constant and exponent
        If, bb = terms["field"]  # basal metabolic constant and exponent
        Tk = temperature + 274.15  # body temperature of the individual (K)
        return (
            Es
            * (
                (sig * If * exp(-(Ea / (kB * Tk)))) * mass_g**bf
                + ((1 - sig) * Ib * exp(-(Ea / (kB * Tk)))) * mass_g**bb
            )
            / 1000  # convert back to kg
        )
    else:
        raise ValueError("Invalid metabolic type: {metabolic_type}")


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
        ) and fg.taxa in {TaxaType.BIRD, TaxaType.MAMMAL, TaxaType.AMPHIBIAN}:
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
    u_st = lambda_max / (1 + exp(-k))

    return u_st


def alpha_i_k(alpha_0_herb: float, mass: float) -> float:
    """Effective rate at which an individual herbivore searches its environment.

    This is linear scaling of herbivore search times with current body mass.

    TODO: Update name

    Madingley

    Args:
        alpha_0_herb: Effective rate per unit body mass at which a herbivore searches
          its environment.
        mass: The current body mass of the foraging herbivore.

    Returns:
        A float of the effective search rate in [ha/day]

    """

    return alpha_0_herb * mass


def k_i_k(alpha_i_k: float, phi_herb_t: float, B_k_t: float, A_cell: float) -> float:
    """The potential biomass (g) of plant k eaten by cohort i, per day.

    TODO: update name

    Madingley

    Args:
        alpha_i_k: Effective rate at which an individual herbivore searches its
          environment.
        phi_herb_t: Fraction of the total plant stock that is available to any one
          herbivore cohort (default 0.1)
        B_k_t: Plant resource bool biomass.
        A_cell: The area of one cell [standard = 1 ha]

    Returns:
        A float of The potential biomass (g) of plant k eating by cohort i, per day
        [g/day]

    """

    return alpha_i_k * ((phi_herb_t * B_k_t) / A_cell) ** 2


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
        sigma_opt_pred_prey: The standard deviation of the mass ration.

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
          predator searches its environment in ha/(day*g).
        mass: The current body mass of the foraging herbivore.
        w_bar_i_j: The probability of successfully capturing a prey item.

    Returns:
        A float of the effective search rate in [ha/day]

    """

    return alpha_0_pred * mass * w_bar_i_j


def k_i_j(alpha_i_j: float, N_i_t: float, A_cell: float, theta_i_j: float) -> float:
    """Potential number of prey items eaten off j by i.

    TODO: double check output needs to be float, might be int
    TODO: update name

    Madingley

    Args:
        alpha_i_j: Rate at which an individual predator searches its environment and
          kills prey.
        N_i_t: Number of consumer individuals.
        A_cell: The area of a grid cell.
        theta_i_j: The cumulative density of organisms with a mass lying within the
              same predator specific mass bin.

    Returns:
        Potential number of prey items eaten off j by i [integer number of individuals]


    """

    return alpha_i_j * (N_i_t / A_cell) * theta_i_j


def H_i_j(h_pred_0: float, M_ref: float, M_i_t: float, b_pred: float) -> float:
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

    Returns:
        A float of the handling time (days).

    """

    return h_pred_0 * ((M_ref / M_i_t) ** b_pred) * M_i_t


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


def territory_size(mass: float) -> float:
    """This function provides allometric scaling for territory size.

    TODO: Replace this toy scaling with a real allometry
    TODO: decide if this allometry will be based on current mass or adult mass

    Args:
        mass: The mass of the animal cohort

    Returns:
        The size of the cohort's territory in hectares
    """

    if mass < 10.0:
        territory = 1.0
    elif 10.0 <= mass < 25.0:
        territory = 2.0
    elif 25.0 <= mass < 50.0:
        territory = 5.0
    elif 50.0 <= mass < 100.0:
        territory = 10.0
    elif 100.0 <= mass < 200.0:
        territory = 15.0
    elif 200.0 <= mass < 500.0:
        territory = 20.0
    else:
        territory = 30.0

    return territory


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

    Args:
        centroid_key: The community key anchoring the territory.
        target_cell_number: The number of grid cells in the territory.
        cell_nx: Number of cells along the x-axis.
        cell_ny: Number of cells along the y-axis.

    Returns:
        A list of grid cell keys representing the territory.
    """

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
