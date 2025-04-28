---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.1
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

# Animal Model Implementation

## Model Overview

The animal model in the Virtual Ecosystem platform represents the dynamics of animal
communities. The implementation is structured
around three core classes, each playing a distinct role in managing animal agents, their
traits, and their interactions with the ecosystem. Together, these classes facilitate a
flexible and scalable approach to simulating complex animal processes across spatial
grids.

- [Functional Group](https://virtual-ecosystem.readthedocs.io/en/latest/api/models/animal/functional_group.html)
  - the organismal type and its traits
- [Animal Cohort](https://virtual-ecosystem.readthedocs.io/en/latest/api/models/animal/animal_cohorts.html)
  - the agent, a group of identical individuals of the same functional group and age
- [Animal Model](https://virtual-ecosystem.readthedocs.io/en/latest/api/models/animal/animal_model.html#virtual_ecosystem.models.animal.animal_model.AnimalModel)
  - the structural class, orchestrating the interactions between cohorts and their environment.

### Core Classes

#### **1. FunctionalGroup**

The `FunctionalGroup` class encapsulates the fixed traits of an organism, defining its
ecological role and life-history strategy. These traits include metabolic type, diet,
taxonomic classification, reproductive strategy, and developmental type. Functional
groups serve as templates for constructing animal cohorts and ensuring consistent trait
inheritance across simulations.

Key responsibilities:

- Encodes fixed traits shared by cohorts within the group.
- Provides scaling factors that scale processes like territory size and prey selection
  to the mass of individuals within a cohort
- Defines dietary and physiological constraints that influence cohort behavior.

#### **2. AnimalCohort**

The `AnimalCohort` class represents a group of identically sized individual animal agents
from a single functional group: a cohort. Each cohort is age-specific, meaning all
individuals in the cohort were produced in the same reproductive event and share the same
age. The class tracks dynamic state variables such as mass, age, reproductive biomass,
 and territory occupancy.

Key attributes:

- **Dynamic state variables**: Mass, age, individuals, reproductive mass, and more.
- **Territory management**: Tracks the spatial extent of a cohort's interactions with
  resources and other cohorts.
- **Lifecycle processes**: Handles maturity, mortality, and metamorphosis.

#### **3. AnimalModel**

The `AnimalModel` class orchestrates the animal community at the spatial grid level.
It contains methods for initialization, setup, and updating of the animal model as well as
communication with the core data object. The animal
model provides methods that loop over all cohorts in the simulation to simulate community
processes, along with methods to handle cohort movement, creation and death.

Key responsibilities:

- **Cohort management**: Initializes, updates, and removes animal cohorts.
- **Spatial dynamics**: Tracks cohort occupancy across grid cells and handles migration.
- **Community-level processes**: Foraging, mortality, birth, metamorphosis, and more.

### Code Structure

The `AnimalModel` is a subclass of `BaseModel`, integrating into the broader
Virtual Ecosystem framework. It extends the base functionality to include animal-specific
methods and attributes, ensuring compatibility with other ecosystem modules such as
vegetation, litter, and soil.

Key components:

- **Initialization**: Sets up the grid structure for animal movement, functional groups,
  and resource pools for excrement, carcasses, and leaf waste.
- **Cohort-level methods**: Implements functions to handle cohort-specific processes
  (e.g., `birth`, `metamorphose`, `forage`).
- **Community-level methods**: Manages collective processes for all cohorts in a grid cell
  (e.g., `migrate_community`, `metabolize_community`, `remove_dead_cohort_community`).
- **State updates**: Updates population densities, litter consumption, and nutrient
  contributions to the soil.

## Sequence of Operations in the Animal Model

The animal model follows a sequence of operations designed to simulate the dynamic
interactions of animal cohorts with their environment. The ordering of events may be
revised in the future.

1. **Initialize Litter Pools**
   Litter pools accessible to animals for consumption are populated using the
   `populate_litter_pools` method. These pools are referenced during foraging and
   consumption calculations.

2. **Foraging**
   Animal cohorts forage for resources within their communities using the
   `forage_community` method. Resource consumption is determined by cohort traits and
   resource availability.

3. **Migration**
   Cohorts migrate between grid cells based on birth events and resource
   availability using the `migrate_community` method. Migration updates the spatial
   distribution of cohorts.

4. **Birth**
   New cohorts are generated through reproduction using the `birth_community` method.
   Parent cohorts allocate biomass from their reproductive mass to create new cohorts.

5. **Metamorphosis**
   Larval cohorts transition into adult cohorts using the `metamorphose_community`
   method. This transition updates the cohort's traits and functional role.

6. **Metabolism**
   Cohorts metabolize consumed resources, processing consumed matter into waste and
   fueling internal processes. This is handled by the `metabolize_community` method,
   which considers the update interval duration.

7. **Mortality**
   Non-predation mortality is applied to cohorts using the
   `inflict_non_predation_mortality_community` method. Mortality may be caused by
   starvation, disease, aging, or background mortality.

8. **Remove Dead Cohorts**
   Cohorts that have no remaining individuals are removed from the simulation using the
   `remove_dead_cohort_community` method. Their biomass contributes to excrement or
   carcass pools.

9. **Increase Cohort Age**
   Cohorts are aged by the simulation time step using the `increase_age_community`
   method. This tracks the progression of cohorts toward maturity and mortality.

10. **Calculate Additions to Soil and Litter**
    The contributions of animal activities to the soil and litter models are calculated:
    - **Soil Additions**: Biomass from excrement, carcasses, and waste is transferred to
      the soil using the `calculate_soil_additions` method.
    - **Litter Consumption**: The total animal consumption of litter pools is calculated
      using the `calculate_total_litter_consumption` method.
    - **Litter Additions**: Biomass from herbivory (e.g., unconsumed plant material) is
      added to litter pools using the `calculate_litter_additions_from_herbivory` method.

11. **Update Simulation State**
    Updates to soil and litter pools are recorded in the data object. Population densities
    for each functional group in each grid cell are updated using the
    `update_population_densities` method.

This sequence allows the animal model to dynamically interact with other ecosystem
modules, such as soil and vegetation, while maintaining an organized computational flow.
The modular structure ensures that individual processes can be refined without disrupting
the overall simulation.

## Model Variables

### Initialisation, Generated, and Updated Variables

The following tables show the variables required to initialise and update the animal
model, the variables generated during the first update, and the variables updated at
each model step.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
from IPython.display import display_markdown
from var_generator import generate_variable_table

# Variables required for initialisation and update
display_markdown(
    generate_variable_table("AnimalModel", ["vars_required_for_update"]),
    raw=True,
)

# Variables generated during the first update
display_markdown(
    generate_variable_table("AnimalModel", ["vars_populated_by_first_update"]), raw=True
)

# Variables updated at each model step
display_markdown(generate_variable_table("AnimalModel", ["vars_updated"]), raw=True)
```
