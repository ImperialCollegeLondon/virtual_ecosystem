---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
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
mystnb:
  render_markdown_format: myst
---

# Configuring science models in the Virtual Ecosystem

```{code-cell} ipython3
:tags: [remove-input]

import tomli_w
import json
from config_display import (
    dump_config_toml,
    model_config_to_deflist,
)
from virtual_ecosystem.core.configuration import Configuration
from virtual_ecosystem.core.registry import get_model_configuration_class
from IPython.display import display, Markdown, HTML
from importlib import import_module
```

Each of the science models in the Virtual Ecosystem has its own configuration section.
For some models, the configuration may only consist of a set of model-specific constant
values. In other cases, the science model may require additional configuration details,
such as paths to data files providing configuration data or initialisation values.

In all cases, your TOML configuration files only need to specify values that do not have
a default value (typically file paths) or where you want to change a default. To include
a model using only the default values, it is enough just to include the model name as a
header section. So for example:

```{code-block} toml
# This is sufficient to configure the abiotic model with default settings
[abiotic]
```

## Validation of science model configurations

As with the core configuration, each science model configuration option has specific
validation settings that are enforced when a configuration is loaded. These constraints
should be described in the documentation of each setting. If configuration data contains
invalid values, then the simulation will exit and the log will contain a detailed
breakdown of any configuration validation issues.

## Simple abiotic model

Configuration for the `abiotic_simple` model includes two sections:

* A small set of constants values (`[abiotic_simple.constants]`), and
* A set of upper and lower bounds on the predicted microclimate variables
  (`[abiotic_simple.bounds]`).

In both cases, these default configuration will probably be enough to get an initial
configuration running for your simulation but may then need to be adjusted for your
study system.

### Abiotic simple constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleConstants

dump_config_toml("abiotic_simple.constants", AbioticSimpleConstants)
model_config_to_deflist("abiotic_simple.constants", AbioticSimpleConstants)
```

### Abiotic simple bounds

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds

dump_config_toml("abiotic_simple.constants", AbioticSimpleBounds)
model_config_to_deflist("abiotic_simple.constants", AbioticSimpleBounds)
```

## Abiotic model

Configuration for the `abiotic` model includes three sections:

* An expanded set of constants values (`[abiotic.constants]`).
* A set of upper and lower bounds on the predicted microclimate variables
  (`[abiotic.bounds]`). This uses the same defaults as the simple abiotic model.
* The abiotic model uses the simple abiotic model to initialise the system state and
  also requires the simple constants used by that model (`[abiotic.simple_constants`).

The last two sections are defined identically to the abiotic simple above and so follow
the structure for the [bounds](#abiotic-simple-bounds) and [simple
constants](#abiotic-simple-constants) shown above. The only difference is that the
should use the section names for the abiotic model.

### Abiotic constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic.model_config import AbioticConstants

dump_config_toml("abiotic.constants", AbioticConstants)
model_config_to_deflist("abiotic.constants", AbioticConstants)
```

## Litter model

```{eval-rst}
..
    This is needed to allow sphinx to resolve the :attr: links for litter constants
.. currentmodule:: virtual_ecosystem.models.litter.model_config
```

The litter model only requires one configuration section:

* The litter model constants (`[litter.constants]`)

### Litter constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.litter.model_config import LitterConstants

dump_config_toml("litter.constants", LitterConstants)
model_config_to_deflist("litter.constants", LitterConstants)
```

## Hydrology model

The hydrology model requires two simple initialisation values and then a set of
hydrology constants one configuration section:

* the initial soil moisture,
* the initial groundwater saturation, and
* the hydrology model constants (`[hydrology.constants]`)

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.hydrology.model_config import HydrologyConfiguration

dump_config_toml("hydrology", HydrologyConfiguration)
model_config_to_deflist("hydrology", HydrologyConfiguration)
```

## Soil model

```{eval-rst}
..
    This is needed to allow sphinx to resolve the :attr: links for soils config objects
.. currentmodule:: virtual_ecosystem.models.soil.model_config
```

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue
from typing import get_args
from virtual_ecosystem.models.soil.model_config import (
    REQUIRED_MICROBIAL_GROUPS,
    REQUIRED_ENZYMES,
)

glue("soil_required_enzymes", ", ".join([str(pair) for pair in REQUIRED_ENZYMES]))
glue("soil_required_groups", ", ".join([*get_args(REQUIRED_MICROBIAL_GROUPS)]))
```

The Soil model configuration is used to provide:

* Trait data on the microbial groups required for the soil model. The soil model
  requires a defined set of these groups, currently: {glue:text}`soil_required_groups`.

  These are currently configured directly in the TOML file using the
  `soil.microbial_group_definition` configuration option but this may move to loading
  from a CSV file using the `soil.microbial_group_definition_path` setting.

* Enzyme kinetics data for the enzymes produced by the taxonomic groups. Data is
  required for each pair of the higher taxonomic groups of microbes (fungi or bacteria)
  and the enzyme substrates targeted in the model (particulate organic matter or mineral
  associated organic matter): {glue:text}`soil_required_enzymes`

  These are currently configured directly in the TOML file using the
  `soil.enzyme_class_definition` configuration option but this may move to loading from
  a CSV file using the `soil.enzyme_class_definition_path` setting.

* A set of soil model constants using the `soil.constants` configuration.

### Soil microbial groups

The soil microbial groups are defined as a set of traits associated with each of the
required groups.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.soil.model_config import SoilMicrobialGroup

dump_config_toml("soil.microbial_group_definition", SoilMicrobialGroup)
model_config_to_deflist("soil.microbial_group_definition", SoilMicrobialGroup)
```

### Soil enzyme classes

The soil enzyme classes are defined as a set of traits associated with each pair of
higher taxon and substrate

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.soil.model_config import SoilEnzymeClass

dump_config_toml("soil.enzyme_class_definition", SoilEnzymeClass)
model_config_to_deflist("soil.enzyme_class_definition", SoilEnzymeClass)
```

### Soil constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.soil.model_config import SoilConstants

dump_config_toml("soil.constants", SoilConstants)
model_config_to_deflist("soil.constants", SoilConstants)
```

## Plants model

Configuration for the `plants` model includes four sections:

* A path to a CSV file defining the plant functional types to be used in the model
  (`[plants.pft_definitions_path]`)
* A path to another CSV file defining the size-structured communities of plant
  functional types found in each cell (`[plants.cohort_data_path]`).
* Configuration details for the export of plant community data at each time step
  (`[plants.community_data_export]`).
* A set of constants values used within the model (`[plants.constants]`)

### Plant functional types

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue
from pyrealm.demography.flora import Flora
from virtual_ecosystem.models.plants.functional_types import ExtraTraitsPFT

glue("pft_traits", ", ".join([*Flora.array_attrs, *ExtraTraitsPFT.array_attrs]))
```

The `plants.pft_definitions_path` configuration setting must point to a CSV defining
the plant functional types to be used in a simulation. Each row in the CSV must provide
a unique PFT name and then a set of plant functional trait values for that PFT. The file
in the example data is a good template to use for preparing this file. The required
trait fields are:

{glue:text}`pft_traits`.

### Plant cohort data

The `plants.cohort_data_path` configuration setting must point to a CSV file defining
the cohorts in each cell. Again, the file in the example data is a good template but the
basic structure is that each row must provide size-structured cohort data as:

* the name of a PFT,
* a cell ID value,
* the size of the individuals in the cohort as diameter at breast height, and
* the number of individuals in the cohort.

### Plants community data export

The plants model holds a large amount of detailed data on the plant communities growing
in each cell, on the community-wide canopy structure within each cell and the canopy
properties of individual stems within each cohort. This data is not required by other
science models and so is not shared through the central data store. If you want to look
at plant community data within a simulation, you will need to configure export of plant
community data using the following configuration settings.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue
from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

glue(
    "cohort_attributes",
    ", ".join(CommunityDataExporter.available_attributes["cohort_attributes"]),
)

glue(
    "community_canopy_attributes",
    ", ".join(
        CommunityDataExporter.available_attributes["community_canopy_attributes"]
    ),
)

glue(
    "stem_canopy_attributes",
    ", ".join(CommunityDataExporter.available_attributes["stem_canopy_attributes"]),
)
```

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.plants.model_config import PlantsExportConfig

dump_config_toml("plants.community_data_export", PlantsExportConfig)
model_config_to_deflist("plants.community_data_export", PlantsExportConfig)
```

There are three possible data files that can be exported - you select one or more by
including them in `[plants.community_data_export.required]` and can then select which
attributes you want exported using the appropriate attributes configuration option.

The choices are:

* If `cohorts` is included in `required` then the file `plants_cohorts_data.csv`
  will be exported for each time step. The available attributes for plant cohort data
  are: {glue:text}`cohort_attributes`.

* If `community_canopy` is included in `required` then the file
  `plants_community_canopy_data.csv` will be exported for each time step. The available
  attributes for plant cohort data are: {glue:text}`community_canopy_attributes`.

* If `stem_canopy` is included in `required` then the file `plants_stem_canopy_data.csv`
  will be exported for each time step. The available attributes for plant cohort data
  are: {glue:text}`stem_canopy_attributes`.

### Plants constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.plants.model_config import PlantsConstants

dump_config_toml("plants.constants", PlantsConstants)
model_config_to_deflist("plants.constants", PlantsConstants)
```

## Animal model
