# The theory of the Virtual Ecosystem

Ecosystems are complex systems that arise from the interplay between animals, plants,
and microbles with their abiotic environment. Many of these interactions are non-linear
and happen across a wide range of spatial and temporal scales which makes ecosystem
dynamics and emergent phenomena such as resilience to environmental stressors
challenging to understand and predict.

The Virtual Ecosystem is a holistic ecosystem model that aims to replicate the many
connections among individual organisms and their complex interactions with the abiotic
environment with the goal to explicitly reveal ecosystem-level emergent phenomena.
The model represents fundamental physiological processes governing the birth, growth,
reproduction, and survival of microbes, plants, and animals. Additionally, it simulates
physical processes such as microclimate and hydrology, which both influence and are
influenced by the biotic components of the ecosystem. Simultaneously, the Virtual
Ecosystem aims to balance energy, water, carbon, nitrogen, and phosphorus
levels by simulating how these flow through plants, animals, and microbes. (Figure 1).

**FIGURE HERE**
*Figure 1. The key processes in the Virtual Ecosystem (reference here).
The model replicates ecosystem dynamics across four ecological domains, each represented
by a separate module that generates the dynamics of plants, animals, soil, and the
abiotic environment. The essential metabolic processes operating at the scale of
individual organisms—plants, animals, and microbes—are incorporated into the plant,
faunal, and soil modules, respectively. These modules are dynamically connected through
the transfer of matter and energy.*

The biotic domains of the model are driven by organismal physiology, including the
dependence of vital rates (e.g. birth, death, metabolism) on temperature and body size
(Gillooly et al. 2001, White et al. 2006), and stoichiometry – the balance of carbon,
nitrogen and phosphorus within organisms
(Sterner and Elser 2002, Agren 2008, Cherif and Loreau 2013). The physical domain of the
model is based on fundamental principles of physics (Maclean and Klinges 2021).

To serve a diverse range of user strories, the model attempts to replicate processes
across wide spatial and temporal scales. Simulations can run with spatial extents from
the typical area of natural area management that range from 1 to 40,000 ha
(UNEP-WCMC and IUCN 2024), and time scales range from short-term management periods
(one year or more) to long-term data series spanning decades, essential for accurately
detecting changes in ecosystem resilience (Boulton et al. 2022).

```{admonition} User Stories
User stories serve as a project management tool that outlines the criteria for project
success. Below, we present eight example user stories as outlined in Ewers et al.,
each equally vital in defining the success of a holistic ecosystem model. Fulfilling
the requirements of all user stories is necessary for the model to achieve complete
success.

* As a systems ecologist, I will be able to identify any core components and
sub-networks that exert strong control over the full system dynamics, so that I can
understand the mechanisms underlying ecosystem stability.
* As a disturbance ecologist, I will be able to track the attenuation of external
perturbations through the system, so that I can understand the mechanisms underlying
ecosystem resilience.
* As a sustainability scientist, I will be able to calculate the rate at which ecosystem
services are provided, so that I can make predictions about the long-term sustainability
of the ecosystem.
* As a biogeochemist, I will be able to track the flow of carbon, nitrogen and
phosphorus through the ecosystem, so that I can quantify elemental balances and
residence times.
* As a hydrologist, I will be able to predict the frequency and magnitude of flood
events, so that I can design downstream flood defences.
* As a field ecologist, I will be able to identify knowledge gaps that significantly
impair our ability to predict ecosystem dynamics, so that I can prioritise future data
collection activities. As an applied ecologist, I will be able to examine the impact of
climate change and extreme climatic events on ecosystem dynamics, so that I can predict
the likely future state of the ecosystem.
* As a resource manager, I will be able to predict the outcomes of competing sets of
management strategies, so that I can make informed decisions about implementing
cost-effective management actions.
```
