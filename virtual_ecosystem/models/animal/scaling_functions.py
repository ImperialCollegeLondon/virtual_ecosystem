"""The `models.animal.scaling_functions` module contains a set of functions containing
scaling equations" (relationships between body-mass and a trait) required by the broader
:mod:`~virtual_ecosystem.models.animal` module

"""  # noqa: D205, D415

from collections.abc import Sequence
from math import asin, ceil, exp, isnan, log, pi

import numpy as np
from scipy.special import expit

from virtual_ecosystem.core.grid import Grid
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


def raw_biomass_density_kg_m2(
    functional_group: FunctionalGroup,
    density_scaling_method: str,
) -> float:
    """Raw biomass density for a functional group before normalization.

    For functional groups with an empirical density override
    (``density_individuals_m2`` set in the CSV), biomass density is derived
    directly from that empirical value. For all other functional groups the
    appropriate allometric scaling law is used.

    The returned value is in kg m⁻² and represents the functional group's
    contribution to the heterotroph biomass budget before the cross-group
    normalization factor is applied.

    Args:
        functional_group: The functional group to evaluate.
        density_scaling_method: The allometric scaling method to use for groups
            without an empirical density override. Must be ``"madingley"`` or
            ``"damuth"``.

    Returns:
        Raw biomass density [kg m⁻²].

    Raises:
        ValueError: If ``density_scaling_method`` is not recognised.
    """
    override = functional_group.density_individuals_m2
    if override is not None and not isnan(override):
        # Empirical path: individuals/m² x kg/individual → kg/m²
        return override * functional_group.adult_mass

    terms = functional_group.population_density_terms

    if density_scaling_method == "madingley":
        exponent, scalar = terms
        mass_g = functional_group.adult_mass * 1000.0
        biomass_density_g_km2 = scalar * mass_g**exponent
        return biomass_density_g_km2 / 1e9  # g/km² → kg/m²

    if density_scaling_method == "damuth":
        # TODO: Damuth terms are calibrated for individual density so the biomass
        # density derived here is approximate. Revisit when Damuth is a primary
        # scaling method.
        return (
            damuths_law(functional_group.adult_mass, terms)
            * functional_group.adult_mass
        )

    raise ValueError(
        f"Unrecognised density_scaling_method: {density_scaling_method!r}. "
        "Expected 'madingley' or 'damuth'."
    )


def heterotroph_normalization_factor(
    functional_groups: list[FunctionalGroup],
    target_biomass_density_kg_m2: float,
    density_scaling_method: str,
) -> float:
    """Normalization factor scaling all functional groups to a fixed biomass budget.

    In Madingley, total heterotroph biomass density is constrained to a target
    value regardless of how many functional groups are defined. This function
    computes the single multiplicative factor applied uniformly to every functional
    group's raw individual count so that the sum of normalized biomass densities
    equals ``target_biomass_density_kg_m2``.

    Each functional group's share of the budget is proportional to its raw biomass
    density, whether derived from an empirical override or an allometric scaling
    law. The same factor is applied to all groups.

    Args:
        functional_groups: All functional groups in the simulation.
        target_biomass_density_kg_m2: Target total heterotroph biomass density
            [kg m⁻²].
        density_scaling_method: Allometric scaling method (``"madingley"`` or
            ``"damuth"``).

    Returns:
        Normalization factor (dimensionless).

    Raises:
        ValueError: If the sum of raw biomass densities across all functional
            groups is zero, indicating a degenerate configuration.
    """
    total_raw = sum(
        raw_biomass_density_kg_m2(fg, density_scaling_method)
        for fg in functional_groups
    )
    if total_raw == 0.0:
        raise ValueError(
            "Sum of raw biomass densities across all functional groups is zero. "
            "Check that adult_mass and density parameters are correctly set."
        )
    return target_biomass_density_kg_m2 / total_raw


def biomass_density_to_individuals(
    biomass_density_kg_m2: float,
    adult_mass_kg: float,
    total_area_m2: float,
) -> int:
    """Convert a biomass density to a total individual count.

    A scaling-law-agnostic conversion used after the heterotroph normalization
    factor has been applied. Dividing normalized biomass density by adult mass
    gives individual density; multiplying by total area gives the headcount.

    Args:
        biomass_density_kg_m2: Biomass density [kg m⁻²].
        adult_mass_kg: Adult body mass of the functional group [kg].
        total_area_m2: Total simulation area [m²].

    Returns:
        Total number of individuals, rounded up to the nearest integer.

    Raises:
        ValueError: If ``adult_mass_kg`` is not positive.
    """
    if adult_mass_kg <= 0.0:
        raise ValueError(f"adult_mass_kg must be positive, got {adult_mass_kg}.")
    return ceil(biomass_density_kg_m2 / adult_mass_kg * total_area_m2)


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
        Ib, bb = terms["basal"]
        If, bf = terms["field"]
        Tk = 310.0  # fixed body temperature for endotherms [K]
    elif metabolic_type == MetabolicType.ECTOTHERMIC:
        Ib, bb = terms["basal"]
        If, bf = terms["field"]
        Tk = temperature + 273.15  # body temperature equals ambient [K]
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

    Linear scaling of herbivore search rate with current body mass (Madingley).
    The native Madingley constant ``alpha_0_herb`` is in ha day^-1 g^-1, so the
    kg body mass is converted to grams before applying it; the returned search
    rate is therefore in native ha/day. Area is not converted here -- it enters
    the functional response in ``k_i_k``, where ``A_cell`` is the normaliser.

    TODO: Update name

    Args:
        alpha_0_herb: Native Madingley effective search rate per unit body mass
            [ha day^-1 g^-1], value 1e-11.
        mass: Current body mass of the foraging herbivore [kg].

    Returns:
        Effective search rate [ha/day].
    """
    mass_g = mass * 1000.0  # kg -> g, native Madingley unit for alpha_0_herb
    return alpha_0_herb * mass_g


def k_i_k(alpha_i_k: float, B_k_t: float, A_cell: float) -> float:
    """Potential biomass of plant k eaten by one herbivore per day.

    TODO: check madingley code implementation is the same as the paper

    This is Madingley's Holling Type III herbivory response (Harfoot et al. 2014,
    eq. 30): ``K_i,k = alpha_i,k * (phi_herb,f * B_k,t / A_cell)**2``. Squaring the
    stock biomass density (``B_k,t / A_cell``) is the Type III density-squared
    encounter term, saturated downstream by the ``1 + sum(K_i,l . H_i,l)`` handling
    denominator. ``phi_herb,f`` is the proportion of stock k experienced by the
    cohort; it is 1.0 in our system because each cohort experiences the whole
    available pool, so it does not appear below.

    Madingley parameterises ``alpha_i,k`` as a linear area-swept-per-day search rate
    [ha/day], so applying it to the squared density leaves one factor of area
    uncancelled: the published form is empirical and not dimensionally homogeneous as
    written, and the residual is absorbed by calibration at native units rather than by
    the constants' formal dimensions. The interpreted unit, biomass per day per
    herbivore, is realised in ``F_i_k``, where ``N_i,t`` scales to the whole herbivore
    cohort and one factor of ``B_k,t`` cancels algebraically against the ``1/B_k,t``
    divisor. That leaves the fraction eaten per day rising with stock biomass, so total
    consumption scales with ``B_k,t**2`` before saturation -- the Type III signature.

    Biomass is native grams and cell area native hectares, so the kg biomass and m^2
    area are converted here, at the point they enter the equation.

    TODO: Update name

    Args:
        alpha_i_k: Herbivore search rate [ha/day].
        B_k_t: Plant resource biomass [kg].
        A_cell: Area of one cell [m^2].

    Returns:
        Potential biomass eaten by one herbivore per day [g/day].
    """

    B_k_t_g = B_k_t * 1000.0  # kg -> g
    A_cell_ha = A_cell / 10000.0  # m^2 -> ha
    return alpha_i_k * (B_k_t_g / A_cell_ha) ** 2


def H_i_k(h_herb_0: float, M_ref: float, M_i_t: float, b_herb: float) -> float:
    """Handling time for a herbivore of cohort i to handle 1 g of plant resource k.

    ``H_i,k = h_herb_0 * (M_ref / M_i_t)^b_herb`` in native Madingley units. The
    ratio M_ref/M_i_t only cancels its unit if both masses match, so the kg
    herbivore mass is converted to grams to sit against the native gram M_ref --
    this is the fractional-power term, safe because b_herb acts on a dimensionless
    ratio. M_ref stays in its native grams.

    (Madingley)

    TODO: update name

    Args:
        h_herb_0: Native time for a reference-mass herbivore to handle 1 g of
            autotroph mass [days].
        M_ref: Native herbivore reference mass [g].
        M_i_t: Current herbivore mass [kg].
        b_herb: Exponent of the power-law relating handling time of autotroph
            matter to herbivore mass [-].

    Returns:
        Handling time to handle 1 g of plant resource [days].
    """
    M_i_t_g = M_i_t * 1000.0  # kg -> g, to match native gram M_ref in ratio
    return h_herb_0 * (M_ref / M_i_t_g) ** b_herb


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

    Linear scaling of predator search rate with current body mass (Madingley),
    weighted by capture success. The native constant ``alpha_0_pred`` is in
    ha day^-1 g^-1, so the kg body mass is converted to grams before applying it;
    the returned rate is native ha/day. Area is not converted here -- it enters the
    functional response in ``k_i_j``.

    TODO: Update name

    Args:
        alpha_0_pred: Native Madingley search rate per unit body mass
            [ha day^-1 g^-1], value 1e-6.
        mass: Current body mass of the foraging predator [kg].
        w_bar_i_j: Probability of successfully capturing a prey item [0-1].

    Returns:
        Effective search-and-kill rate [ha/day].
    """
    mass_g = mass * 1000.0  # kg -> g, native Madingley unit for alpha_0_pred
    return alpha_0_pred * mass_g * w_bar_i_j


def k_i_j(
    alpha_i_j: float, N_j_t: float, intersection_area: float, theta_i_j: float
) -> float:
    """Potential number of prey eaten from cohort j by one predator per day.

    TODO: check madingley code to ensure their paper form is the same as their code

    This is Madingley's Holling Type III predation response (Harfoot et al. 2014,
    eq. 34): ``K_i,j = alpha_i,j * (N_j,t / A_cell) * Theta_i,j``. The product of the
    focal prey density (``N_j,t / A_cell``) and the bin density (``Theta_i,j``) is the
    Type III density-squared encounter term, saturated downstream by the
    ``1 + sum(K_i,m . H_i,m)`` handling denominator.

    Madingley parameterises ``alpha_i,j`` as a linear area-swept-per-day search rate
    [ha/day], so applying it to the squared density leaves one factor of area
    uncancelled: the published form is empirical and not dimensionally homogeneous as
    written, and the residual is absorbed by calibration at native units rather than by
    the constants' formal dimensions. The interpreted unit, prey per predator per day,
    is realised in ``F_i_j_individual``, where ``N_i,t`` scales to the whole predator
    cohort and the prey count ``N_j,t`` cancels algebraically.

    ``alpha_i_j`` arrives in ha/day and ``theta_i_j`` is already a native ha density
    (from ``_build_prey_bin_densities``), so the m^2 intersection is converted to ha
    here to match. ``N_j_t`` is the prey cohort abundance and is not converted.

    Args:
        alpha_i_j: Predator search-and-kill rate [ha/day].
        N_j_t: Abundance of the target prey cohort j [individuals].
        intersection_area: Overlap between predator and prey territories [m^2].
        theta_i_j: Cumulative prey density in j's mass bin [individuals/ha].

    Returns:
        Potential number of prey eaten by one predator [prey . predator^-1 . day^-1].
    """

    intersection_area_ha = intersection_area / 10000.0  # m^2 -> ha
    return alpha_i_j * (N_j_t / intersection_area_ha) * theta_i_j


def H_i_j(
    h_pred_0: float, M_ref: float, M_i_t: float, b_pred: float, prey_mass: float
) -> float:
    """Handling time of one prey individual of cohort j by cohort i.

    ``H_i,j = h_pred_0 * (M_ref / M_i_t)^b_pred * prey_mass`` in native units. The
    ratio M_ref/M_i_t only cancels its unit if both masses match, so the kg predator
    mass is converted to grams to sit against the native gram M_ref -- this is the
    fractional-power term, safe because b_pred acts on a dimensionless ratio.
    prey_mass is a power-1 factor in native grams, so it converts by a clean kg -> g.

    TODO: Update name

    Args:
        h_pred_0: Native time for a reference-mass predator to handle a 1 g prey
            individual [days], default value 0.5.
        M_ref: Native predator reference mass [g].
        M_i_t: Current predator mass [kg].
        b_pred: Exponent of the handling-time power law [-].
        prey_mass: Mass of the prey individual being handled [kg].

    Returns:
        Handling time for one prey individual [days].
    """
    M_i_t_g = M_i_t * 1000.0  # kg -> g, to match native gram M_ref in ratio
    prey_mass_g = prey_mass * 1000.0  # kg -> g, native linear handling factor
    return h_pred_0 * (M_ref / M_i_t_g) ** b_pred * prey_mass_g


def dispersal_distance(
    current_mass: float,
    V_disp: float,
    M_disp_ref: float,
    o_disp: float,
    dt_days: float,
) -> float:
    """Distance a cohort can travel in a single timestep [m].

    Madingley eq. (diffusive natal dispersal). ``V_disp`` is the dispersal speed of
    an individual of reference body mass, expressed in the Madingley-native units of
    km/month, and ``M_disp_ref`` is that reference mass in grams. ``current_mass`` is
    supplied in kg and is converted to grams at the point it enters the mass ratio,
    and the km/month speed is converted to metres over the model timestep.

    Args:
        current_mass: Mass of an individual of the cohort in the current timestep [kg].
        V_disp: Dispersal speed of an individual of mass ``M_disp_ref`` [km/month].
        M_disp_ref: Reference body mass for the dispersal speed scaling [g].
        o_disp: Power-law exponent for the mass-dispersal speed scaling relationship.
        dt_days: Length of the model timestep [days].

    Returns:
        The distance the cohort can travel over the timestep [m].
    """

    # mass_g -> current_mass * 1000.0  kg -> g, to match the native gram M_disp_ref
    speed_km_month = V_disp * ((current_mass * 1000.0) / M_disp_ref) ** o_disp

    # km/month -> m/timestep: 1000 m per km, Madingley month taken as 30 days.
    return speed_km_month * 1000.0 * (dt_days / 30.0)


def cells_within_distance(
    grid: Grid,
    centroid_key: int,
    distance_m: float,
) -> list[int]:
    """Grid cells whose centroids lie within a travel distance of a centroid.

    Reachability is Euclidean centroid-to-centroid, read directly from the grid's
    pre-populated distance matrix (see
    :meth:`~virtual_ecosystem.core.grid.Grid.populate_distances`), using the same
    ``<=`` metric as :meth:`~virtual_ecosystem.core.grid.Grid.set_neighbours`.

    The distance is clamped to a minimum of one cell side so that a triggered dispersal
    always has at least the orthogonal neighbours available, even for a cohort too slow
    to clear a single cell.

    Args:
        grid: The simulation grid, with its distance matrix already populated.
        centroid_key: The grid cell key anchoring the move.
        distance_m: The distance the cohort can travel this timestep [m].

    Returns:
        The keys of all in-bounds cells within reach, excluding the centroid itself.
    """

    if grid._distances is None:
        raise ValueError(
            "grid distance matrix not populated;call grid.populate_distances() at setup"
        )

    # Clamp to at least one cell side. Uses <= below, matching set_neighbours, so the
    # orthogonal neighbours at exactly sqrt(cell_area) are retained.
    distance_m = max(
        distance_m, np.sqrt(grid.cell_area) + 0.001
    )  # 1 mm greater to avoid floating point issues

    reachable = np.where(grid._distances[centroid_key, :] <= distance_m)[0].tolist()
    reachable.remove(centroid_key)

    return reachable


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
