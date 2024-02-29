"""The `models.animals.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_ecosystem.models.animals` module

The near-future intention is to rework the relationship between these constants and the
AnimalCohort objects in which they are used such that there is a FunctionalType class
in-between them. This class will hold the specific scaling, rate, and conversion
parameters required for determining the function of a specific AnimalCohort and will
avoid frequent searches through this constants file for values.
"""  # noqa: D205, D415

from dataclasses import dataclass, field

from virtual_ecosystem.core.constants_class import ConstantsDataclass
from virtual_ecosystem.models.animals.animal_traits import (
    DietType,
    MetabolicType,
    TaxaType,
)


@dataclass(frozen=True)
class AnimalConsts(ConstantsDataclass):
    """Dataclass to store all constants related to metabolic rates.

    TODO: The entire constants fille will be reworked in this style after the energy to
    mass conversion.

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
        }
    )

    fat_mass_terms: dict[TaxaType, tuple[float, float]] = field(
        default_factory=lambda: {
            TaxaType.MAMMAL: (1.19, 0.02),  # Scaling of mammalian herbivore fat mass
            TaxaType.BIRD: (1.19, 0.05),  # Toy Values
            TaxaType.INSECT: (1.19, 0.05),  # Toy Values
        }
    )

    muscle_mass_terms: dict[TaxaType, tuple[float, float]] = field(
        default_factory=lambda: {
            TaxaType.MAMMAL: (1.0, 0.38),  # Scaling of mammalian herbivore muscle mass
            TaxaType.BIRD: (1.0, 0.40),  # Toy Values
            TaxaType.INSECT: (1.0, 0.40),  # Toy Values
        }
    )

    intake_rate_terms: dict[TaxaType, tuple[float, float]] = field(
        default_factory=lambda: {
            TaxaType.MAMMAL: (0.71, 0.63),  # Mammalian maximum intake rate
            TaxaType.BIRD: (0.7, 0.50),  # Toy Values
            TaxaType.INSECT: (0.7, 0.50),  # Toy Values
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
            MetabolicType.ECTOTHERMIC: {TaxaType.INSECT: (1.0, 1.0)},  # Toy values
        }
    )

    longevity_scaling_terms: dict[TaxaType, tuple[float, float]] = field(
        default_factory=lambda: {
            TaxaType.MAMMAL: (0.25, 0.02),  # Toy values
            TaxaType.BIRD: (0.25, 0.05),  # Toy values
            TaxaType.INSECT: (0.25, 0.05),  # Toy values
        }
    )

    birth_mass_threshold: float = 1.5  # Threshold for reproduction
    flow_to_reproductive_mass_threshold: float = (
        1.0  # Threshold of trophic flow to reproductive mass
    )
    dispersal_mass_threshold: float = 0.75  # Threshold for dispersal
    energy_percentile_threshold: float = 0.5  # Threshold for initiating migration
    decay_fraction_excrement: float = 0.5  # Decay fraction for excrement
    decay_fraction_carcasses: float = 0.2  # Decay fraction for carcasses


"""
METABOLIC_RATE_TERMS: dict[MetabolicType, dict[str, tuple[float, float]]] = {
    # Parameters from Madingley, mass based metabolic rates
    MetabolicType.ENDOTHERMIC: {
        "basal": (4.19e10, 0.69),
        "field": (9.08e11, 0.7),
    },
    MetabolicType.ECTOTHERMIC: {
        "basal": (4.19e10, 0.69),
        "field": (1.49e11, 0.88),
    },
}

DAMUTHS_LAW_TERMS: dict[TaxaType, dict[DietType, tuple[float, float]]] = {
    TaxaType.MAMMAL: {
        DietType.HERBIVORE: (-0.75, 4.23),
        # Mammalian herbivore population density, observed allometry (Damuth 1987).
        # [assumes kg mass]
        DietType.CARNIVORE: (-0.75, 1.00),
        # Toy values.
    },
    TaxaType.BIRD: {
        DietType.HERBIVORE: (-0.75, 5.00),
        # Toy values.
        DietType.CARNIVORE: (-0.75, 2.00),
        # Toy values.
    },
    TaxaType.INSECT: {
        DietType.HERBIVORE: (-0.75, 5.00),
        # Toy values.
        DietType.CARNIVORE: (-0.75, 2.00),
        # Toy values.
    },
}

FAT_MASS_TERMS: dict[TaxaType, tuple[float, float]] = {
    TaxaType.MAMMAL: (1.19, 0.02),
    # Scaling of mammalian herbivore fat mass (citation from Rallings). [assumes g mass]
    TaxaType.BIRD: (1.19, 0.05),
    # Toy Values
    TaxaType.INSECT: (1.19, 0.05),
    # Toy Values
}

MUSCLE_MASS_TERMS: dict[TaxaType, tuple[float, float]] = {
    TaxaType.MAMMAL: (1.0, 0.38),
    # Scaling of mammalian herbivore muscle mass (citation from Rallings).
    # [assumes g mass]
    TaxaType.BIRD: (1.0, 0.40),
    # Toy Values
    TaxaType.INSECT: (1.0, 0.40),
    # Toy Values
}

INTAKE_RATE_TERMS: dict[TaxaType, tuple[float, float]] = {
    TaxaType.MAMMAL: (0.71, 0.63),
    # Mammalian maximum intake rate (g/min) from (Shipley 1994). [assumes kg mass]
    TaxaType.BIRD: (0.7, 0.50),
    # Toy Values
    TaxaType.INSECT: (0.7, 0.50),
    # Toy Values
}


ENERGY_DENSITY: dict[str, float] = {
    "meat": 7000.0,
    # The energy of a unit mass of mammal meat (check citation from Rallings). [J/g]
    "plant": 18200000.0
    # Temporary realistic plant food value: Alfalfa ¬ 18,200,000 J/kg DM.
}

CONVERSION_EFFICIENCY: dict[DietType, float] = {
    DietType.HERBIVORE: 0.1,
    # Toy value [unitless].
    DietType.CARNIVORE: 0.25,
    # Toy value [unitless].
}

MECHANICAL_EFFICIENCY: dict[DietType, float] = {
    DietType.HERBIVORE: 0.9,
    # Toy value [unitless].
    DietType.CARNIVORE: 0.8,
    # Toy Value [unitless]
}

PREY_MASS_SCALING_TERMS: dict[MetabolicType, dict[TaxaType, tuple[float, float]]] = {
    MetabolicType.ENDOTHERMIC: {
        TaxaType.MAMMAL: (1.0, 1.0),
        # Toy values.
        TaxaType.BIRD: (1.0, 1.0),
        # Toy values.
    },
    MetabolicType.ECTOTHERMIC: {
        TaxaType.INSECT: (1.0, 1.0)
        # Toy values.
    },
}

LONGEVITY_SCALING_TERMS: dict[TaxaType, tuple[float, float]] = {
    TaxaType.MAMMAL: (0.25, 0.02),
    # Toy values
    TaxaType.BIRD: (0.25, 0.05),
    # Toy Values
    TaxaType.INSECT: (0.25, 0.05),
    # Toy Values
}

BOLTZMANN_CONSTANT: float = 8.617333262145e-5  # Boltzmann constant [eV/K]

TEMPERATURE: float = 37.0  # Toy temperature for setting up metabolism [C].

BIRTH_MASS_THRESHOLD: float = 1.5  # Toy value for thresholding reproduction.

FLOW_TO_REPRODUCTIVE_MASS_THRESHOLD: float = (
    1.0  # Toy value for threshold of trophic flow to reproductive mass.
)

DISPERSAL_MASS_THRESHOLD: float = 0.75  # Toy value for thesholding dispersal.

ENERGY_PERCENTILE_THRESHOLD: float = 0.5  # Toy value for initiating migration
"""
DECAY_FRACTION_EXCREMENT: float = 0.5
"""Fraction of excrement that is assumed to decay rather than be consumed [unitless].

TODO - The number given here is very much made up. In future, we either need to find a
way of estimating this from data, or come up with a smarter way of handling this
process.
"""

DECAY_FRACTION_CARCASSES: float = 0.2
"""Fraction of carcass biomass that is assumed to decay rather than be consumed.

[unitless]. TODO - The number given here is very much made up, see
:attr:`DECAY_FRACTION_EXCREMENT` for details of how this should be changed in future.
"""
BOLTZMANN_CONSTANT: float = 8.617333262145e-5  # Boltzmann constant [eV/K]

TEMPERATURE: float = 37.0  # Toy temperature for setting up metabolism [C].
