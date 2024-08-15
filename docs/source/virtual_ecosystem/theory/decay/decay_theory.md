# Theory of biomass decay

The decay of dead biomass is one of the key processes that the `virtual_ecosystem` aims
to capture. Understanding this process is vital to understanding both the long term fate
of carbon in the system and understanding the recycling of nutrients which sustains the
system as a whole.

In the virtual ecosystem, we split biomass decay between two separate models. The
[litter model](./litter_theory.md) handles the breakdown of biomass that's still in an
identifiable form, the [soil model](./soil_theory.md) then handles the subsequent stages
of decay.

The litter model is significantly simpler than the soil model. This is a conscious
design choice to help to keep the complexity of the whole system model within reasonable
limits. There are major unknowns for both litter breakdown and nutrient transformations
within the soil. The two biggest uncertainties for the soil model are the long term
fate of soil carbon and the impact of plant-microbe interactions on uptake rates of
nutrients by plants. The biggest uncertainty in the litter model is the rate at which
different types of litter decay. We believe that the soil related uncertainties are of
greater consequence so have decided to focus the main modelling effort on them. For the
litter model, we have adopted a fairly simplistic model which can be parameterised from
commonly collected empirical data. From this model, we want to obtain reasonably good
estimates of the standing stocks of litter and the rates at which carbon, nitrogen and
phosphorus enter the soil. It is quite possible that an alternative more detailed litter
model (e.g. one that explicitly models microbes) is added in the future, but for the
initial version of the Virtual Ecosystem we believe that a (relatively) simple model of
litter decay is sufficient.
