"""The `models.animals.constants` module contains a set of dictionaries containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.animals` module

The near-future intention is to rework the relationship between these constants and the
AnimalCohort objects in which they are used such that there is a FunctionalType class
in-between them. This class will hold the specific scaling, rate, and conversion
parameters required for determining the function of a specific AnimalCohort and will
avoid frequent searches through this constants file for values.
"""  # noqa: D205, D415


ENDOTHERM_METABOLIC_RATE_TERMS: dict[str, tuple[float, float]] = {
    "mammal": (0.75, 0.047),
    # Mammalian herbivore population density, observed allometry (Damuth 1987). [kg]
    "bird": (0.75, 0.05),
    # Toy values.
}

DAMUTHS_LAW_TERMS: dict[str, dict[str, tuple[float, float]]] = {
    "mammal": {
        "herbivore": (-0.75, 4.23),
        # Mammalian herbivore population density, observed allometry (Damuth 1987). [kg]
        "carnivore": (-0.75, 1.00),
        # Toy values.
    },
    "bird": {
        "herbivore": (-0.75, 5.00),
        # Toy values.
        "carnivore": (-0.75, 2.00),
        # Toy values.
    },
}

FAT_MASS_TERMS: dict[str, tuple[float, float]] = {
    "mammal": (1.19, 0.02),
    # Scaling of mammalian herbivore fat mass (citation from Rallings). [g]
    "bird": (1.19, 0.05),
    # Toy Values
}

MUSCLE_MASS_TERMS: dict[str, tuple[float, float]] = {
    "mammal": (1.0, 0.38),
    # Scaling of mammalian herbivore muscle mass (citation from Rallings).[g]
    "bird": (1.0, 0.40),
    # Toy Values
}

INTAKE_RATE_TERMS: dict[str, tuple[float, float]] = {
    "mammal": (0.71, 0.63),
    # Mammalian maximum intake rate (g/min) from (Shipley 1994).
    "bird": (0.7, 0.50),
    # Toy Values
}


ENERGY_DENSITY: dict[str, float] = {
    "meat": 7000.0,
    # The energy of a unit mass of mammal meat (check citation from Rallings). [J/g]
    "plant": 18200000.0
    # Temporary realistic plant food value: Alfalfa ¬ 18,200,000 J/kg DM.
}

CONVERSION_EFFICIENCY: dict[str, float] = {
    "herbivore": 0.1,
    # Toy value [unitless].
    "carnivore": 0.25,
    # Toy value [unitless].
}
