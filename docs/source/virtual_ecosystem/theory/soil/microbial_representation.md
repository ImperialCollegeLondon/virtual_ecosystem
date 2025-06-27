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

# Microbial representation

The microbial groups we include are represented as separate carbon pools. These pools
can produce enzymes which drive many of the key processes in the soil model. Most of the
parameters related to the activity of each microbial group can be configured separately.
This includes their uptake rates for different resources, their turnover rates, their
stoichiometric ratios, their thermal responses, and details of the enzymes they produce.
The processes that microbial groups are involved in and the different functional groups
we represent in the model will now be explained in more detail.

## Microbial processes

Microbial activity is one of the biggest drivers of soil organic matter turnover, so it
is important to capture the underlying processes in detail. In our model, microbes take
up carbon, nitrogen and phosphorus (in organic and inorganic forms). This is then used
to synthesis new biomass, which can be used to replace lost biomass (from cell death and
cellular maintenance), to grow, to produce externally secreted enzymes or (in the case
of fungi) to produce reproductive bodies.

### Nutrient uptake and growth

TODO - EXPLAIN, WITH THE RELEVANT EQUATIONS HOW MICROBIAL UPTAKE WORKS

### Enzyme production

TODO - FILL OUT ALL THE RELEVANT DETAIL HERE
TODO - NEED TO TALK ABOUT HOW ENZYME ARE PARAMETRISED

## Microbial functional groups

TODO - INTRO JUSTIFYING WHY WE CHOSE THE 4 GROUPS WE DID + WHY WE DIDN'T INCLUDE
NITROGEN FIXERS, NITRIFIERS ETC
TODO - SEGUE INTO, THESE ARE THE SPECIAL PROCESSES AND WHY WE INCLUDE THEM

### Fungal fruiting

TODO - EXPLAIN HOW FUNGAL FRUITING WORKS (THIS NEEDS TO WAIT UNTIL IT'S ACTUALLY
IMPLEMENTED)

### Mycorrhiza

TODO - EXPLAIN HOW MYCORRHIZAL FUNGI DIFFER
