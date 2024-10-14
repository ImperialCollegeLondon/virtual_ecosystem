# Theory of biomass decay

The decay of dead biomass is one of the key processes to capture in the Virtual
Ecosystem, in order to understand both the long term fate of carbon in the system and
the recycling of nutrients which sustains the system as a whole.

In the Virtual Ecosystem, we split biomass decay between two separate models. The
[litter model](./litter_theory.md) handles the breakdown of biomass that's still in an
identifiable form, while the [soil model](./soil_theory.md) handles the subsequent
stages of decay.

The litter model is significantly simpler than the soil model. The biggest uncertainty
in this model are the rates at which different types of litter decay, and this can be
parameterised relatively well from commonly collected empirical data. The model
providese reasonably good estimates of the standing stocks of litter and the rates at
which carbon, nitrogen and phosphorus enter the soil.

In contrast, the soil model is more detailed in order to address deeper uncertainties
about litter breakdown and nutrient transformations within the soil. The two biggest
uncertainties for the soil model are the long term fate of soil carbon and the impact of
plant-microbe interactions on uptake rates of nutrients by plants. We believe that the
soil related uncertainties are of greater consequence so have made the conscious choice
to focus more detailed modelling effort soil processes than the litter model.

:::{admonition} Future directions :telescope:

There are ecologically explicit extensions to the litter model - such as
modelling of litter microbes and invertebrates - that could increase the realism of
litter model, but the current model is expected to be sufficient in the short term.

:::
