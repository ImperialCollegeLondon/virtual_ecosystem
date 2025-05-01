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

# Theory of the Animal Model

This page outlines the theoretical basis for the animal model within the Virtual
Ecosystem. It details the representation of functional groups and cohorts,
the processes governing their interactions with the environment, and their contributions
to ecosystem-level dynamics. The page also highlights the key state variables tracked
for each cohort and the links between animal processes and other ecosystem modules.

:::{admonition} In progress 🛠️

Much of the Animal Model follows the logic of the Madingley Model {cite}`harfoot_madingley_2014`
with modifications made for differences in spatial and temporal scale, trophic
resolution, multi-grid cell occupancy, and ecological stoichiometry.

The theoretical framework for animal stoichiometric cycling and water balance is still
being refined. As such, some sections are relatively brief and will be expanded as the
model evolves.

:::

## Functional Groups

Instead of modeling species individually, the animal model uses **functional groups**
to define cohort types. Functional groups aggregate species based on shared ecological
roles and traits, enabling scalable simulations while maintaining ecological fidelity.

This approach has several advantages:

- **Trait-based generalization**: Functional groups are defined by traits such as body
size, diet, metabolic rate, reproductive strategy, and excretory type, rather than
specific taxonomic identity.
- **Scalability**: Simplifies the representation of biodiversity, allowing the model to
simulate large ecosystems with diverse communities without overwhelming computational
resources.
- **Focus on ecosystem function**: Prioritizes the ecological roles of organisms (e.g.,
herbivores, scavengers, predators) and their impacts on ecosystem dynamics over
species-specific details.

### Traits Defining Functional Groups

Functional groups in the animal model are constructed based on a combination of core
traits that capture the diversity of ecological roles and physiological strategies. These
traits include:

#### **Metabolic Type**

The primary strategy for thermoregulation:

- **Endothermic**: Animals that regulate their body temperature internally (e.g., mammals,
  birds).
- **Ectothermic**: Animals whose body temperature is influenced by the external environment
  (e.g., reptiles, amphibians, insects).

#### **Diet Type**

The primary dietary habits:

- **Herbivore**: Consumes plant material as the primary food source.
- **Carnivore**: Consumes other animals as the primary food source.

Additional dietary categories under development:

- **Scavenger**: Consumes dead animals or carrion as a primary food source.
- **Omnivore**: Consumes a mix of plant and animal materials.
- **Detritivore**: Consumes decomposing organic material, including soil.
- **Coprophage**: Consumes feces as a significant food source.
- **Ectoparasite**: Feeds on the external surfaces of a host organism.

#### **Taxa Type**

A broad classification based on taxonomic group:

- **Mammal**
- **Bird**
- **Insect**

Additional taxa categories under development:

- **Reptile**
- **Amphibian**

#### **Reproductive Type**

The reproductive strategy:

- **Semelparous**: Reproduces once in a lifetime, often producing many offspring (e.g., some
  insects, salmon).
- **Iteroparous**: Reproduces multiple times over a lifetime, typically with fewer offspring
  per event.
- **Nonreproductive**: Does not engage in reproduction (e.g., non-reproductive life stages).

#### **Development Type**

The path of development:

- **Direct**: Development involves no major morphological transformation; juveniles resemble
  adults (e.g., mammals, birds).
- **Indirect**: Development involves significant morphological changes (e.g., metamorphosis
  in insects or amphibians).

#### **Development Status**

The life stage of the cohort:

- **Larval**: Juvenile stage, morphologically distinct from the adult form in indirect
developers.
- **Adult**: Mature stage, typically capable of reproduction.

#### **Excretion Type**

The strategy for nitrogen waste excretion:

- **Ureotelic**: Excretes nitrogen primarily as urea (e.g., mammals).
- **Uricotelic**: Excretes nitrogen primarily as uric acid (e.g., birds, reptiles).

## Representation of Animal Cohorts

In the animal model, **cohorts** represent groups of individuals within a functional group
that are of the same age and were produced in the same reproductive event by a parent
cohort. This age-specific approach simplifies tracking population dynamics while
maintaining biological realism.

### Key Features of Animal Cohorts

Animal cohorts are the fundamental agents in the animal model, designed to simulate the
growth, movement, reproduction, and survival of populations. Each cohort tracks a set of
state variables that evolve through ecological processes:

- **Functional Group**: Each cohort belongs to a functional group, which defines its
  ecological role, such as herbivore or carnivore, along with its physiological and
  behavioral traits.
- **Mass**: Represents the average body mass of individuals in the cohort (in kilograms),
  which changes dynamically as individuals grow or lose biomass.
- **Age**: Tracks the cohort's age in days.
- **Number of Individuals**: The population size of the cohort.
- **Reproductive Mass**: A dedicated biomass pool for reproduction, which accumulates as
  individuals allocate resources to reproductive efforts.
- **Location and Territory**: Cohorts occupy specific territories on the simulation grid,
  interacting with local resources and environmental conditions. Their **territory size**
  is determined by their functional group’s traits, such as adult body mass.
- **Occupancy Proportion**: Tracks how much of a cohort occupies a specific grid cell
  within its territory.

## Key Animal Processes

The animal model incorporates several processes that determine cohort dynamics and their
influence on the ecosystem:

### Foraging and Consumption

- **Diet specificity**: Determines what resources a cohort consumes (e.g., plants, other
animals, detritus).
- **Mass and stoichiometry**: Tracks the intake of carbon, nitrogen, and phosphorus and
their allocation to different pools (e.g., body mass, reproductive mass).

### Metabolism and Maintenance

- **Energy and nutrient use**: Models the metabolic cost of maintaining body functions.
- **Waste production**: Generates excretory and respiratory byproducts, linking animal
processes to soil nutrient dynamics.

### Growth and Reproduction

- **Somatic growth**: Simulates the conversion of consumed resources into body mass.
- **Reproductive allocation**: Tracks resource allocation to offspring production, with
reproduction resulting in new cohorts.

### Mortality and Carcass Dynamics

- **Mortality causes**: Includes predation, background mortality, starvation, and old age.
- **Carcass generation**: Links the fate of animal biomass to scavenger activity,
decomposition, and soil nutrient inputs.

### Migration and Movement

- **Resource tracking**: Animals move across grid cells based on resource availability
and reproductive events.
- **Home range dynamics**: Simulates spatial patterns of movement and habitat use.

## Links to Ecosystem Dynamics

The animal model is tightly integrated with other modules in the Virtual Ecosystem
platform:

- **Vegetation**: Herbivores affect plant biomass directly through consumption and
indirectly through nutrient cycling.
- **Litter**: Animals contribute to litter through unconsumed plant material produced
during foraging.
- **Soil**: Animal wastes and carcasses feed into soil pools through decomposition.
- **Microclimate**: Animal metabolic rates are influenced by local microclimates.

## Scaling and Challenges

- **Scaling individual processes to ecosystems**: Balancing fine-scale detail with
computational efficiency for large landscapes.
- **Trait diversity**: Representing the wide range of animal functional traits within a
cohesive framework.
- **Temporal and spatial dynamics**: Capturing short-term behaviors and long-term
ecosystem impacts within the same model.

:::

Both animal carcasses and excrement are important resources for animals to scavenge
from, as such their decay is tracked as part of the animal model. How they are tracked
is explained [here](./carcasses_and_excrement.md).
