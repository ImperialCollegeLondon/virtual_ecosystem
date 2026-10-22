"""Necessary microbial parametrisation for `ve_run` example.

This script generates the microbial parametrisation required as part of the example
dataset. The parameter choices are best guesses, but in many cases these guesses are
really big stretches, and should not be treated as "good" parameter estimates. This
script gives the logic for selection for each parameter value, you should read these
carefully before making your own parameter choices.
"""

# TODO - MICROBIAL PARAMETERS NEED TO BE ADDED HERE TO IN A LATER PR

import csv

# N.B. Values taken from Wang et al. often have to be transformed from the (mg C/g soil)
# units used in that paper into the (kg C/m^3) units we use, by multiplying by an
# estimated bulk density of 1400.0 kg/m^3

soil_enzyme_definitions = [
    {
        "source": "bacteria",
        "substrate": "pom",
        # Mean value (for cellulose) from Wang et al. Ecological Applications (2013)
        "maximum_rate": 60.0,
        # Mean value from Wang et al. Ecological Applications (2013)
        "half_saturation_constant": 70.0,
        # Mean value from Wang et al. Ecological Applications (2013)
        "activation_energy_rate": 37000,
        # Mean value from Wang et al. Ecological Applications (2013)
        "activation_energy_saturation": 30000,
        # Mean value from Wang et al. Ecological Applications (2013)
        "reference_temperature": 12.0,
        # Mean value from Wang et al. Ecological Applications (2013)
        "turnover_rate": 2.4e-2,
        # Chosen to match the stoichiometry of bacteria
        "c_n_ratio": 5.2,
        # Chosen to match the stoichiometry of bacteria
        "c_p_ratio": 16,
    },
    {
        "source": "bacteria",
        "substrate": "maom",
        # Mean value from Wang et al. Ecological Applications (2013)
        "maximum_rate": 24.0,
        # Mean value from Wang et al. Ecological Applications (2013)
        "half_saturation_constant": 350.0,
        # Mean value from Wang et al. Ecological Applications (2013)
        "activation_energy_rate": 47000,
        # Mean value from Wang et al. Ecological Applications (2013)
        "activation_energy_saturation": 30000,
        "reference_temperature": 12.0,
        # Mean value from Wang et al. Ecological Applications (2013)
        "turnover_rate": 2.4e-2,
        # Chosen to match the stoichiometry of bacteria
        "c_n_ratio": 5.2,
        # Chosen to match the stoichiometry of bacteria
        "c_p_ratio": 16,
    },
    {
        "source": "fungi",
        "substrate": "pom",
        # Double bacteria case (so that fungal enzymes are "better")
        "maximum_rate": 120.0,
        # half bacteria case (so that fungal enzymes are "better")
        "half_saturation_constant": 35.0,
        # Assumed thermal responses are the same as for bacterial enzymes (shaky
        # assumption)
        "activation_energy_rate": 37000,
        # Assumed thermal responses are the same as for bacterial enzymes (shaky
        # assumption)
        "activation_energy_saturation": 30000,
        "reference_temperature": 12.0,
        # Assumed all enzymes have the same turnover rate regardless of source (dubious)
        "turnover_rate": 2.4e-2,
        # Chosen to match the stoichiometry of saprotrophic fungi
        "c_n_ratio": 6.5,
        # Chosen to match the stoichiometry of saprotrophic fungi
        "c_p_ratio": 40.0,
    },
    {
        "source": "fungi",
        "substrate": "maom",
        # Double bacteria case (so that fungal enzymes are "better")
        "maximum_rate": 48.0,
        # half bacteria case (so that fungal enzymes are "better")
        "half_saturation_constant": 175.0,
        # Assumed thermal responses are the same as for bacterial enzymes (shaky
        # assumption)
        "activation_energy_rate": 47000,
        # Assumed thermal responses are the same as for bacterial enzymes (shaky
        # assumption)
        "activation_energy_saturation": 30000,
        "reference_temperature": 12.0,
        # Assumed all enzymes have the same turnover rate regardless of source (dubious)
        "turnover_rate": 2.4e-2,
        # Chosen to match the stoichiometry of saprotrophic fungi
        "c_n_ratio": 6.5,
        # Chosen to match the stoichiometry of saprotrophic fungi
        "c_p_ratio": 40.0,
    },
]

soil_enzyme_fieldnames = [
    "source",
    "substrate",
    "maximum_rate",
    "half_saturation_constant",
    "activation_energy_rate",
    "activation_energy_saturation",
    "reference_temperature",
    "turnover_rate",
    "c_n_ratio",
    "c_p_ratio",
]

with open("../data/example_enzyme_parameters.csv", "w", newline="") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=soil_enzyme_fieldnames)
    writer.writeheader()
    writer.writerows(soil_enzyme_definitions)
