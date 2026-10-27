"""Necessary microbial parametrisation for `ve_run` example.

This script generates the microbial parametrisation required as part of the example
dataset. The parameter choices are best guesses, but in many cases these guesses are
really big stretches, and should not be treated as "good" parameter estimates. This
script gives the logic for selection for each parameter value, you should read these
carefully before making your own parameter choices.
"""

import csv

# N.B. Values taken from Wang et al. often have to be transformed from the (mg C/g soil)
# units used in that paper into the (kg C/m^3) units we use, by multiplying by an
# estimated bulk density of 1400.0 kg/m^3

microbial_group_definitions = [
    {
        "name": "bacteria",
        "taxonomic_group": "bacteria",
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "max_uptake_rate_labile_C": 0.04,
        # Mean value from Wang et al. Ecological Applications (2013)
        "activation_energy_uptake_rate": 47000,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "half_sat_labile_C_uptake": 0.364,
        # Mean value from Wang et al. Ecological Applications (2013)
        "activation_energy_uptake_saturation": 30000,
        # Complete guess
        "max_uptake_rate_ammonium": 5e-3,
        # Complete guess
        "half_sat_ammonium_uptake": 0.02275,
        # Complete guess
        "max_uptake_rate_nitrate": 5e-4,
        # Complete guess
        "half_sat_nitrate_uptake": 0.02275,
        # Complete guess
        "max_uptake_rate_labile_p": 0.0025,
        # Complete guess
        "half_sat_labile_p_uptake": 0.02275,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "turnover_rate": 0.005,
        # Mean value from Wang et al. Ecological Applications (2013)
        "activation_energy_turnover": 20000,
        "reference_temperature": 12.0,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "c_n_ratio": 5.2,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "c_p_ratio": 16,
        # Complete guess
        "enzyme_production_pom": 0.005,
        # Complete guess
        "enzyme_production_maom": 0.005,
        # Has to be zero by definition
        "reproductive_allocation": 0.0,
        # Has to be zero by definition
        "symbiote_nitrogen_uptake_fraction": 0.0,
        # Has to be zero by definition
        "symbiote_phosphorus_uptake_fraction": 0.0,
    },
    {
        "name": "saprotrophic_fungi",
        "taxonomic_group": "fungi",
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "max_uptake_rate_labile_C": 0.02,
        # Assumed same as bacteria (bad assumption)
        "activation_energy_uptake_rate": 47000,
        # Assumed lower than bacteria
        "half_sat_labile_C_uptake": 0.150,
        # Assumed same as bacteria (terrible assumption)
        "activation_energy_uptake_saturation": 30000,
        # Assumed lower than bacteria
        "max_uptake_rate_ammonium": 2.5e-3,
        # Assumed lower than bacteria
        "half_sat_ammonium_uptake": 0.01,
        # Assumed lower than bacteria
        "max_uptake_rate_nitrate": 2.5e-4,
        # Assumed lower than bacteria
        "half_sat_nitrate_uptake": 0.01,
        # Assumed lower than bacteria
        "max_uptake_rate_labile_p": 0.001,
        # Assumed lower than bacteria
        "half_sat_labile_p_uptake": 0.01,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "turnover_rate": 0.002,
        # Assumed same as bacteria (bad assumption)
        "activation_energy_turnover": 20000,
        "reference_temperature": 12.0,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "c_n_ratio": 6.5,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "c_p_ratio": 40.0,
        # Complete guess
        "enzyme_production_pom": 0.005,
        # Complete guess
        "enzyme_production_maom": 0.005,
        # Complete guess
        "reproductive_allocation": 0.1,
        # Has to be zero by definition
        "symbiote_nitrogen_uptake_fraction": 0.0,
        # Has to be zero by definition
        "symbiote_phosphorus_uptake_fraction": 0.0,
    },
    {
        "name": "arbuscular_mycorrhiza",
        "taxonomic_group": "fungi",
        # Assumed worse (i.e. lower) than saprotrophic fungi
        "max_uptake_rate_labile_C": 0.01,
        # Assumed same as bacteria (bad assumption)
        "activation_energy_uptake_rate": 47000,
        # Assumed worse (i.e. higher) than saprotrophic fungi
        "half_sat_labile_C_uptake": 0.4,
        # Assumed same as bacteria (terrible assumption)
        "activation_energy_uptake_saturation": 30000,
        # Assumed higher than saprotrophic fungi
        "max_uptake_rate_ammonium": 5e-3,
        # Assumed lower than saprotrophic fungi
        "half_sat_ammonium_uptake": 0.005,
        # Assumed higher than saprotrophic fungi
        "max_uptake_rate_nitrate": 5e-4,
        # Assumed lower than saprotrophic fungi
        "half_sat_nitrate_uptake": 0.005,
        # Assumed higher than saprotrophic fungi
        "max_uptake_rate_labile_p": 0.0025,
        # Assumed lower than saprotrophic fungi
        "half_sat_labile_p_uptake": 0.005,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "turnover_rate": 0.0012,
        # Assumed same as bacteria (bad assumption)
        "activation_energy_turnover": 20000,
        "reference_temperature": 12.0,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "c_n_ratio": 18.0,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "c_p_ratio": 120.0,
        # Assume that AMF do no produce enzymes at all (needs to be double checked)
        "enzyme_production_pom": 0.0,
        # Assume that AMF do no produce enzymes at all (needs to be double checked)
        "enzyme_production_maom": 0.0,
        # Complete guess
        "reproductive_allocation": 0.1,
        # Complete guess
        "symbiote_nitrogen_uptake_fraction": 0.2,
        # Complete guess
        "symbiote_phosphorus_uptake_fraction": 0.2,
    },
    {
        "name": "ectomycorrhiza",
        "taxonomic_group": "fungi",
        # Assumed same as arbuscular_mycorrhiza
        "max_uptake_rate_labile_C": 0.01,
        # Assumed same as bacteria (bad assumption)
        "activation_energy_uptake_rate": 47000,
        # Assumed same as arbuscular_mycorrhiza
        "half_sat_labile_C_uptake": 0.4,
        # Assumed same as bacteria (bad assumption)
        "activation_energy_uptake_saturation": 30000,
        # Assumed same as arbuscular_mycorrhiza
        "max_uptake_rate_ammonium": 5e-3,
        # Assumed same as arbuscular_mycorrhiza
        "half_sat_ammonium_uptake": 0.005,
        # Assumed same as arbuscular_mycorrhiza
        "max_uptake_rate_nitrate": 5e-4,
        # Assumed same as arbuscular_mycorrhiza
        "half_sat_nitrate_uptake": 0.005,
        # Assumed same as arbuscular_mycorrhiza
        "max_uptake_rate_labile_p": 0.0025,
        # Assumed same as arbuscular_mycorrhiza
        "half_sat_labile_p_uptake": 0.005,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "turnover_rate": 0.0012,
        # Assumed same as bacteria (bad assumption)
        "activation_energy_turnover": 20000,
        "reference_temperature": 12.0,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "c_n_ratio": 18.0,
        # Fatichi et al. Global Biogeochemical Cycles (2019)
        "c_p_ratio": 120.0,
        # Complete guess
        "enzyme_production_pom": 0.02,
        # Complete guess
        "enzyme_production_maom": 0.02,
        # Complete guess
        "reproductive_allocation": 0.1,
        # Complete guess
        "symbiote_nitrogen_uptake_fraction": 0.2,
        # Complete guess
        "symbiote_phosphorus_uptake_fraction": 0.2,
    },
]


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

# With both sets of parameters defined write them out
microbial_group_fieldnames = [
    "name",
    "taxonomic_group",
    "max_uptake_rate_labile_C",
    "activation_energy_uptake_rate",
    "half_sat_labile_C_uptake",
    "activation_energy_uptake_saturation",
    "max_uptake_rate_ammonium",
    "half_sat_ammonium_uptake",
    "max_uptake_rate_nitrate",
    "half_sat_nitrate_uptake",
    "max_uptake_rate_labile_p",
    "half_sat_labile_p_uptake",
    "turnover_rate",
    "activation_energy_turnover",
    "reference_temperature",
    "c_n_ratio",
    "c_p_ratio",
    "enzyme_production_pom",
    "enzyme_production_maom",
    "reproductive_allocation",
    "symbiote_nitrogen_uptake_fraction",
    "symbiote_phosphorus_uptake_fraction",
]

with open("../data/example_microbial_groups.csv", "w", newline="") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=microbial_group_fieldnames)
    writer.writeheader()
    writer.writerows(microbial_group_definitions)

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
