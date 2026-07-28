---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.5
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
language_info:
  codemirror_mode:
    name: ipython
    version: 3
  file_extension: .py
  mimetype: text/x-python
  name: python
  nbconvert_exporter: python
  pygments_lexer: ipython3
  version: 3.11.9
---

# Functional group data preparation

## The concept of functional groups

The animal communities in  animal module are represented by functional groups (FGs)
rather than individual species. Functional groups are defined by combinations of
ecological traits and life-history strategies that influence how organisms interact with
resources, predators, and their environment. Functional traits are measurable
characteristics that influence organism growth, survival, and reproduction
{cite:t}`violle_let_2007`. By focusing on traits rather than species, ecological
patterns can be generalised across communities and ecosystems
{cite:t}`lavorel_predicting_2002,funk_revisiting_2017`. Therefore, functional groups
represent **ecologically similar organisms that perform comparable roles in
ecosystems**. For example, multiple canopy herbivorous insects may be represented by a
single FG describing small arboreal herbivorous invertebrates. This approach captures
ecological function without modelling every species individually.

## Functional group definitions

The functional group definitions for a simulation need to be stored in a CSV file: each
functional group must have a unique name and each row then provides the functional
traits for that group. A path to this CSV file must then be provided as part of the
animal model configuration as shown below:

```toml
[animal]
functional_group_definitions_path = '../data/animal_functional_groups.csv'
```

The functional group file needs to include the following fields defining its name and
values for all of the traits:

```{csv-table}
:header: >
: "Field name","Description","Optional","Examples"

"‍name", "The name you would like to call your functional group", "No","carnivorous_bird,
herbivorous_bird, or even something more specific like dung_beetle."
"‍taxa", "The taxa of the functional group", "No", "mammal, bird, invertebrate,
amphibian, reptile"
"‍diet", "The diet of the functional group. Users are required to provide one or more
diet types below with a lowercase underscore-separated string such as
flowers_fruit_fish.", "No", "algae, detritus, flowers, foliage, fruit, seeds, nectar,
wood, blood, invertebrates, fish, vertebrates, carcasses, waste, mushrooms, fungi,
waste, POM, bacteria"
"‍metabolic_type", "The metabolic types of the animals. Endotherms (e.g. birds and
mammals) are warm blooded animals that generate their own heat to maintain a constant
body temperature while ectotherms (e.g. reptiles, insects) are cold blooded animals
whose body temperature and metabolic rate fluctuate with the
environment.", "No", "endothermic, ectothermic"
"‍reproductive_environment", "The environment where reproduction
happens.", "No", "terrestrial, aquatic"
"‍reproductive_type", "The reproductive strategy of the functional group. Semelparous
describes cohorts that reproduce only once during their lifetime, after which death is
inevitable. Iteroparous describes cohorts that reproduce multiple times throughout its
lifetime, often able to produce offspring in successive reproductive cycles.
Non-reproductive describes cohorts that are not involved, do not relate to, or are
incapable of reproduction.", "No", "semelparous, iteroparous, nonreproductive"
"‍development_type", "Is the transition from larval to adult stages direct or indirect?
Indirect development cohorts have metamorphosis in their development stage from larvae
to adult. Direct development cohorts have no metamorphosis and therefore direct
transition from larvae to adult.", "No", "direct, indirect"
"‍offspring_functional_group", "The offpspring type produced by this functional group in
reproduction or metamorphosis. For functional groups without metamorphosis, the same
functional group is recommended. For functional groups with metamorphosis such as the
butterfly, the larval form, caterpillar is recommended. Note that this should be a
functional group existing as a row.", "No", "[name of existing functional group]"
"‍excretion_type", "Animals have evolved different strategies for excretion, the removal
of waste from the body. Uricotelic cohorts like reptiles, birds and insects excrete uric
acid waste while ureotelic cohorts like mammals and adult amphibians on land excrete
urea as nitrogenous waste.", "No", "ureotelic, uricoletic"
"‍migration_type", "This attribute determines whether the cohort is migratory. If
seasonal, the cohort performs migration behaviour once a year.", "No", "none, seasonal"
"‍vertical_occupancy", "This attributes determines which vertical structure the cohort
occupies. The input is a similar parse string we see in diet.", "No", "soil, ground,
canopy or a combination of any three structures using lowercase underscore-separated
string such as ground_canopy, soil_ground_canopy"
"‍birth_mass", "The mass of the functional group at birth in kilograms.", "No", "0.1"
"‍adult_mass", "The mass of the functional group at adulthood in kilograms.", "No", "1"
"‍density_individuals_m2", "The density of individuals of functional group in meter
square. If set as none, densities will be set following madingley or damuth
equations", "Yes", "0.5"
"‍t_opt", "Optimal activity temperature for terrestrial ectotherms in degree celsius. If
set as none, the value will be calculated using diurnal temperature range and mean and
standard deviation annual temperature.", "Yes", "35"
"‍t_max_crit", "Upper critical temperature for terrestrial ectotherms in degree celsius.
If set as none, the value will be calculated using diurnal temperature range and mean
and standard deviation annual temperature.", "Yes", "42"
"‍t_min_crit", "Lower critical temperature  for terrestrial ectotherms in degree celsius.
If set as none, the value will be calculated using diurnal temperature range and mean
and standard deviation annual temperature.", "Yes", "30"

```

To compile this ecological trait information a large number of sources must be drawn
from, including species-level ecological literature, trait databases (e.g., [Elton
Traits](https://opentraits.org/datasets/elton-traits.html)), regional field guides,
species accounts, and relevant ecological syntheses. Key information typically includes
body size metrics (such as adult body mass or birth mass), life-history traits (e.g.,
reproductive strategy and developmental type), physiological traits (e.g., metabolic and
excretion type), population metrics and ecological traits (e.g., diet composition,
habitat use, and vertical occupancy). However, trait data for many tropical taxa remain
incomplete, and therefore trait estimation and ecological inference are often required.

For our preparation of site-specific simulations such as the Maliau simulation, we used
commonly found species as representatives for each functional group to estimate
parameters such as adult body mass. In the case where adult body mass is unavailable,
particularly for taxa where body mass is rarely reported and body dimensions are more
commonly used (e.g., shell height for molluscs or snout–vent length for amphibians and
reptiles), body mass may be estimated from body length using published allometric
relationships (e.g., {cite:t}`sohlstrom_applying_2018` for invertebrates). Another
example where information is lacking, such as birth mass, which is rarely reported in
ecological literature. In such cases, birth mass is estimated using proportional
relationships relative to adult mass or taxonomic generalisations (e.g.,
{cite:t}`hendriks_scaling_2008`), and then all body mass values are converted to
kilograms to match the unit requirements of the model.

Metabolic type currently assigned based on taxonomic classification, with mammals and
birds treated as endotherms and reptiles, amphibians, and most invertebrates treated as
ectotherms. Diet descriptions from literature sources are translated into trophic
categories compatible with the model, while habitat use and vertical occupancy are
assigned based on ecological descriptions of species behaviour and typical habitat
associations reported in the literature.

```{note}
Vertical occupancy is tricky to define, as some groups overlap between strata. When groups
are assigned to multiple strata they are assumed to spend equal amounts of "active"
time in each strata. In reality, some groups will move between strata depending on the
time of year or their condition (e.g., canopy frogs may move down to the mid-canopy for
breeding but otherwise stay in the upper canopy). This equal allocation of time between
strata means that they must be chosen carefully for each functional group.
```

Population density information is often unavailable for many taxa included in ecosystem
models. When empirical estimates are lacking, density may be approximated using
macroecological scaling relationships such as body mass–density relationships (e.g.,
Damuth’s Law) or abundance scaling approaches used in ecosystem models such as
Madingley. These provide approximate initialisation values when site-specific data are
not available.

Optimal activity temperatures, upper critical temperature and lower critical temperature
of functional group can be obtained from literature when available.

## Limitations and Assumptions

The process set out above relies on several simplifying assumptions. Ecological trait
information for many tropical species remains incomplete, requiring the estimation of
parameters such as birth mass or population density. Scaling relationships introduce
additional uncertainty when empirical measurements are unavailable.

Functional group-based modelling also simplifies species diversity by representing
groups of organisms with shared traits rather than modelling individual species. While
this approach improves computational efficiency and captures major ecosystem processes,
the decisions may overlook some ecological variability and species-specific
interactions.

## Example file

The dropdown below shows the example version of the animal functional group definitions:

````{dropdown} animal_functional_groups.csv
```{literalinclude} ../../../../../virtual_ecosystem/example_data/data/animal_functional_groups.csv
```
````
