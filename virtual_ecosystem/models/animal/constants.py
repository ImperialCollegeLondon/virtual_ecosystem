"""The `models.animal.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_ecosystem.models.animal` module

"""  # noqa: D205, D415

from dataclasses import dataclass, field

from virtual_ecosystem.core.constants_class import ConstantsDataclass
from virtual_ecosystem.models.animal.animal_traits import (
    DietType,
    MetabolicType,
    TaxaType,
)


@dataclass(frozen=True)
class AnimalConsts(ConstantsDataclass):
    """Dataclass to store all constants related to animals.

    TODO: Remove unused constants.

    """

    metabolic_rate_terms: dict[MetabolicType, dict[str, tuple[float, float]]] = field(
        default_factory=lambda: {
            # Parameters from Madingley, mass-based metabolic rates
            MetabolicType.ENDOTHERMIC: {
                "basal": (4.19e10, 0.69),
                "field": (9.08e11, 0.7),
            },
            MetabolicType.ECTOTHERMIC: {
                "basal": (4.19e10, 0.69),
                "field": (1.49e11, 0.88),
            },
        }
    )

    damuths_law_terms: dict[TaxaType, dict[DietType, tuple[float, float]]] = field(
        default_factory=lambda: {
            TaxaType.MAMMAL: {
                DietType.HERBIVORE: (-0.75, 4.23),
                DietType.CARNIVORE: (-0.75, 1.00),
            },
            TaxaType.BIRD: {
                DietType.HERBIVORE: (-0.75, 5.00),
                DietType.CARNIVORE: (-0.75, 2.00),
            },
            TaxaType.INSECT: {
                DietType.HERBIVORE: (-0.75, 5.00),
                DietType.CARNIVORE: (-0.75, 2.00),
            },
            TaxaType.AMPHIBIAN: {
                DietType.HERBIVORE: (-0.75, 5.00),
                DietType.CARNIVORE: (-0.75, 2.00),
            },
        }
    )

    energy_density: dict[str, float] = field(
        default_factory=lambda: {
            "meat": 7000.0,  # Energy of mammal meat [J/g]
            "plant": 18200000.0,  # Energy of plant food [J/g]
        }
    )

    conversion_efficiency: dict[DietType, float] = field(
        default_factory=lambda: {
            DietType.HERBIVORE: 0.1,  # Toy value
            DietType.CARNIVORE: 0.25,  # Toy value
        }
    )

    mechanical_efficiency: dict[DietType, float] = field(
        default_factory=lambda: {
            DietType.HERBIVORE: 0.9,  # Toy value
            DietType.CARNIVORE: 0.8,  # Toy value
        }
    )

    prey_mass_scaling_terms: dict[
        MetabolicType, dict[TaxaType, tuple[float, float]]
    ] = field(
        default_factory=lambda: {
            MetabolicType.ENDOTHERMIC: {
                TaxaType.MAMMAL: (1.0, 1.0),  # Toy values
                TaxaType.BIRD: (1.0, 1.0),  # Toy values
            },
            MetabolicType.ECTOTHERMIC: {
                TaxaType.INSECT: (1.0, 1.0),
                TaxaType.AMPHIBIAN: (1.0, 1.0),
            },  # Toy values
        }
    )

    cnp_proportion_terms: dict[TaxaType, dict[str, float]] = field(
        default_factory=lambda: {
            TaxaType.MAMMAL: {"carbon": 0.5, "nitrogen": 0.3, "phosphorus": 0.2},
            TaxaType.BIRD: {"carbon": 0.4, "nitrogen": 0.3, "phosphorus": 0.3},
            TaxaType.INSECT: {"carbon": 0.4, "nitrogen": 0.2, "phosphorus": 0.4},
            TaxaType.AMPHIBIAN: {"carbon": 0.4, "nitrogen": 0.2, "phosphorus": 0.4},
        }
    )

    birth_mass_threshold: float = 1.5  # Threshold for reproduction
    flow_to_reproductive_mass_threshold: float = (
        1.0  # Threshold of trophic flow to reproductive mass
    )
    dispersal_mass_threshold: float = 0.8  # Threshold for dispersal
    energy_percentile_threshold: float = 0.5  # Threshold for initiating migration

    # Madingley Foraging Parameters

    tau_f = 0.5  # tau_f
    """Proportion of time for which functional group is active."""
    sigma_f_t = 0.5  # sigma_f(t) - TODO: find real value
    """Proportion of the time step in which it's suitable to be active for functional
    group f."""

    # Trophic paramters

    alpha_0_herb = 1.0e-11  # alpha_herb_0 [Madingley] ha/(day*g)
    """Effective rate per unit mass at which a herbivore searches its environment."""
    alpha_0_pred = 1.0e-6  # alpha_pred_0 [Madingley] ha/(day*g)
    """Effective rate per unit mass at which a predator searches its environment."""

    phi_herb_t = 0.1  # phi_herb_t
    """Fraction of the resource stock that is available to any one herbivore cohort."""

    b_herb = 0.7  # ( ),b_herb)
    """Herbivore exponent of the power-law function relating the handling time of
      autotroph matter to herbivore mass."""

    b_pred = 0.05  # Toy Values
    """Carnivore exponent of the power-law relationship between the handling time of
      prey and the ratio of prey to predator body mass."""

    M_herb_ref = 1.0  # M_herb_ref [Madingley] g
    """Reference mass for herbivore handling time."""
    M_herb_0 = 0.7  # M_herb_0 [Madingley] (days)
    """Time that it would take a herbivore of body mass equal to the reference mass,
    to handle one gram of autotroph biomass."""
    h_herb_0 = 0.7  # h_pred_0 [Madingley]
    """Time that it would take a herbivore of body mass equal to the reference mass,
    to handle one gram of autotroph biomass"""

    M_pred_ref = 1.0  # toy value TODO: find real value
    """The reference value for predator mass."""
    sigma_opt_pred_prey = 0.7  # sigma_opt_pred-prey [Madingley]
    """Standard deviation of the normal distribution describing realized attack rates
    around the optimal predator-prey body mass ratio."""
    theta_opt_min_f = 0.01  # theta_opt_min_f [Madingley]
    """The minimum optimal prey-predator body mass ratio."""
    theta_opt_f = 0.1  # theta_opt_f [Madingley]
    """The mean optimal prey-predator body mass ratio, from which actual cohort optima
    are drawn."""
    sigma_opt_f = 0.02  # sigma_opt_f [Madingley]
    """The standard deviation of optimal predator-prey mass ratios among cohorts."""
    N_sigma_opt_pred_prey = 3.0  # N_sigma_opt_pred-prey [Madingley]
    """The standard deviations of the realized attack rates around the optimal
    predator-prey body mass ratio for which to calculate predator specific cumulative
    prey densities."""
    h_pred_0 = 0.5  # h_pred_0 [Madingley]
    """Time that it would take a predator of body mass equal to the reference mass,
    to handle a prey individual of body mass equal to one gram."""

    # Activity parameters
    m_tol = 1.6  # m_tol_terrestrial [Madingley]
    """Slope of the relationship between monthly temperature variability and the upper
    critical temperature limit relative to annual mean temperature, for terrestrial
    ectothermic functional groups."""

    c_tol = 6.61  # c_tol_terrestrial [Madingley] (degrees C)
    """Intercept of the relationship between monthly temperature variability and the
    upper critical temperature limit relative to annual mean temperature, for
    terrestrial ectothermic functional groups."""

    m_tsm = 1.53  # m_tsm [Madingley]
    """Slope of the relationship between monthly temperature variability and the optimal
    temperature relative to annual mean temperature, for terrestrial ectothermic
    functional groups."""

    c_tsm = 1.51  # c_tsm [Madingley] (degrees C)
    """Intercept of the relationship between monthly temperature variability and the
    optimal temperature relative to annual mean temperature, for terrestrial
    ectothermic functional groups."""

    # Madingley dispersal parameters

    M_disp_ref = 1.0  # M_disp_ref [Madingley] [g]
    """The reference mass for calculating diffusive juvenile dispersal in grams."""

    V_disp = 0.0278  # V_disp [Madingley] [km/month]
    """Diffusive dispersal speed on an individual of body-mass equal to M_disp_ref
      in km/month."""

    o_disp = 0.48  # o_disp [Madingley] [unitless]
    """Power law exponent for the scaling relationship between body-mass and dispersal
    distance as mediated by a reference mass, M_disp_ref."""

    beta_responsive_bodymass = 0.8  # Beta_responsive_bodymass [unitless]
    """Ratio of current body-mass to adult body-mass at which starvation-response
    dispersal is attempted."""

    # Madingley reproductive parameters
    semelparity_mass_loss = 0.5  # chi [Madingley] [unitless]
    """The proportion of non-reproductive mass lost in semelparous reproduction."""

    # Madingley mortality parameters
    u_bg = 10.0**-3.0  # u_bg [Madingley] [day^-1]
    """The constant background mortality faced by all animal."""

    lambda_se = 3.0 * 10.0**-3.0  # lambda_se [Madingley] [day^-1]
    """The instantaneous rate of senescence mortality at the point of maturity."""

    lambda_max = 1.0  # lambda_max [Madingley] [day^-1]
    """The maximum possible instantaneous fractional starvation mortality rate."""

    J_st = 0.6  # J_st [Madingley] [unitless]
    """Determines the inflection point of the logistic function describing ratio of the
    realised mortality rate to the maximum rate."""

    zeta_st = 0.05  # zeta_st [Madingley] [unitless]
    """The scaling of the logistic function describing the ratio of the realised
    mortality rate to the maximum rate."""

    metamorph_mortality = 0.1  # toy [unitless]
    """The mortality proportion inflicted on a larval cohort undergoing
    metamorphosis. """

    carbon_excreta_proportion = 0.9  # toy [unitless]
    """The proportion of metabolic wastes that are carbonaceous. This is a temporary
    fix to facilitate building the machinery and will be updated with stoichiometry."""

    nitrogen_excreta_proportion = 0.1  # toy [unitless]
    """The proportion of metabolic wastes that are nitrogenous. This is a temporary
    fix to facilitate building the machinery and will be updated with stoichiometry."""

    decay_rate_excrement: float = 0.25
    """Rate at which excrement decays due to microbial activity [day^-1].
    
    In reality this should not be constant, but as a simplifying assumption it is.
    """

    scavenging_rate_excrement: float = 0.25
    """Rate at which excrement is scavenged by animals [day^-1].

    Used along with :attr:`decay_rate_excrement` to calculate the split of excrement
    between scavengable excrement and flow into the soil. In reality this should be a
    constant, but as a simplifying assumption it is.
    """

    decay_rate_carcasses: float = 0.0625
    """Rate at which carcasses decay due to microbial activity [day^-1].
    
    In reality this should not be constant, but as a simplifying assumption it is.
    """

    scavenging_rate_carcasses: float = 0.25
    """Rate at which carcasses are scavenged by animals [day^-1].

    Used along with :attr:`decay_rate_carcasses` to calculate the split of carcass
    biomass between scavengable carcass biomass and flow into the soil. In reality this
    should be a constant, but as a simplifying assumption it is.
    """

    migration_mortality: float = 0.1  # toy
    """Proportion of mortality that occurs on return from a migration [unitless]."""

    aquatic_mortality: float = 0.1  # toy
    """Proportion of mortality that occurs on return from aquatic status [unitless]."""

    aquatic_residence_time: float = 60.0  # toy
    """Amount of time a new cohort spends living in aquatic environment [days]."""

    migration_residence_time: float = 60.0  # toy
    """Amount of time a migrated cohort spends away [days]."""

    seasonal_migration_probability: float = 0.083  # approx 1 seasonal migration per yr.
    """The probability a seasonal migration event occurs per time step (month)."""


BOLTZMANN_CONSTANT: float = 8.617333262145e-5  # Boltzmann constant [eV/K]

TEMPERATURE: float = 37.0  # Toy temperature for setting up metabolism [C].
