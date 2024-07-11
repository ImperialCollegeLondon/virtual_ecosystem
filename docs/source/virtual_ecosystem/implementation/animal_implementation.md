
# The Animal Model implementation

The Animal Model simulates the animal consumers for the Virtual Ecosystem. We follow the
Madingley Model {cite}`harfoot_madingley_2014` to provide the foundational structure
as well as some of the dynamics. The key processes of the model are:

- foraging and trophic dynamics
- migration
- birth
- metamorphosis
- metabolism
- natural mortality

## Functional Groups

Animals within the Animal Model are sorted into functional groups, not biological
species. Functional groups share functional traits and body-mass ranges and
so behave similarly within the ecosystem. Defining a functional group within the
Animal Model requires the following traits:

- name
- taxa: mammal, bird, insect
- diet: herbivore, carnivore
- metabolic type: endothermic, ectothermic
- reproductive type: semelparous, iteroparous, nonreproductive
- development type: direct, indirect
- development status: adult, larval
- offspring functional group
- excretion type: ureotelic, uricotelic
- birth mass (kg)
- adult mass (kg)

A set of these functional groups are used to define an instance of the Animal Model.

## Animal Cohorts

Animals are represented as age-specific cohorts, containing many individuals of the
same functional type. The key Animal Model processes are run at the cohort level.
We track the internal state of the average individual of that cohort over time to
determine the resulting dynamics, such that events like starvation and metamorphosis
occur based on that cohort's internal state. Predator-prey interactions, likewise, occur
between animal cohorts as part of foraging system.
