---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
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

# Creating new Virtual Ecosystem models

The Virtual Ecosystem initially contains a set of models defining core components of
an ecosystem, examples include the `abiotic`, `animal`, `plants` and `soil` models.
However, the simulation is designed to be modular:

* Different combinations of models can be configured for a particular simulation.
* New models can be defined in order to extend the simulation or alter the implemention:
  examples of new functionality might be `freshwater` or `disturbance` models.

This page sets out the steps needed to add a new model to the Virtual Ecosystem and
ensure that it can be accessed by the `core` processes in the simulation.

## Create a new submodule folder

Start by creating  a new folder for your model, within the `virtual_ecosystem/models/`
directory.

```bash
mkdir virtual_ecosystem/models/freshwater
```

You will need to create at least four files within this folder, although you may choose
to add other python modules containing different parts of the module functionality.

* An `__init__.py` file, which tells Python that the folder is a submodule within the
  `virtual_ecosystem` package.
* A python module  `{model_name}_model.py` that will contain the main model
  object.
* A JSON Schema file defining the model configuration, called `schema.json`.
* A python module  `constants.py` that will contain the constants relevant to the model.

For example:

```bash
touch virtual_ecosystem/models/freshwater/__init__.py
touch virtual_ecosystem/models/freshwater/freshwater_model.py
touch virtual_ecosystem/models/freshwater/schema.json
touch virtual_ecosystem/models/freshwater/constants.py
```

## Defining constants and their default values

The definition of 'constant' in the Virtual Ecosystem is basically a parameter of any
kind that should be held constant throughout a simulation. However, while some constants
are likely never to be varied, many constants are estimated with error and users
may want to explore the sensitivity of simulations to changes in those values. We
therefore use a framework for constants that allows constant values to be configured for
any given simulation.

Each model needs to define a `constants.py` module that will define  one or more
constants _dataclasses_. Dataclasses provide an simple way to define a class containing
a set of named constant attributes with default values. However, when an instance of a
dataclass is created, it can be provided with an alternative value for an attribute,
allowing default values to be overridden by the configuration for a particular
simulation. All constant dataclasses must be configured to be _frozen_: the resulting
dataclass instance can be configured when it is created, but cannot be altered while a
simulation is running.

The constants for a module can be stored in a single data class or spread over multiple
data classes. However, having a large number of data classes is likely to make the
downstream code messier, so constants should only be split across multiple classes when
there's a strong reason to do so.

Because dataclasses are widely used structures in Python, the Virtual Ecosystem defines
a specific {class}`~virtual_ecosystem.core.constants_class.ConstantsDataclass` base
class to uniquely identify _constants dataclasses_ from other dataclasses. This base
class also provides the
{meth}`~virtual_ecosystem.core.constants_class.ConstantsDataclass.from_config` methods,
which validates a configuration dictionary against the dataclass definition and returns
a configured dataclass instance.

Constants dataclasses can also provide truly universal constants that you explicitly do
not want users to be able to alter. This can be done by  typing a constants attribute as
a class variable. All instances of the constants dataclass will provide the value, but
it cannot be altered through configuration. Be aware that untyped attributes are also
treated as class attributes but we prefer that class attributes are explicitly typed.

Putting all of these components together, the contents of a `constants.py` file will
look like the following code:

```{code-block} python
from dataclasses import dataclass
from typing import ClassVar

from virtual_ecosystem.core.constants_class import ConstantsDataclass

# Dataclasses are frozen to prevent constants from changing during a simulation
@dataclass(frozen=True)
class FreshwaterConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `example_model` model."""

    # Constants must be typed, to make them configurable instance attributes.
    example_constant_1: float = -1.27
    """Details of source of constant and its units."""

    example_constant_2: ClassVar[float] = 5.4
    """A non-configurable global constants, with details and units."""
```

## Defining the new model class

The model file will define a new subclass of the
{mod}`~virtual_ecosystem.core.base_model.BaseModel` class.

### Required package imports

You may of course need to import other packages or package members to support your model
code, but the following imports are typically needed to create a new `BaseModel`
subclass.

```{code-block} python

# The BaseModel.from_config factory method returns an instance of the class, and
# annotations is required to allow typing to understand this return value.
from __future__ import annotations

# To support the kwargs argument to BaseModel.__init__
from typing import Any

# Data in the Virtual Ecosystem is stored as xarray.DataArrays and array calculations
# typically use numpy.
import numpy as np
import xarray
from pint import Quantity

# These are the main imports required to set up a BaseModel instance:
# - the BaseModel itself
# - a Config , used to configure a BaseModel instance.
# - the load_constants helper function to configure model constants.
# - the Data class, used as a central data store within the simulation
# - an custom exception to cover model initalisation failure
# - the global LOGGER, used to report information to users.
from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER

# You will likely also have a set of imports of model specific code such as constants
# classes and other classes and functions. For example:
from virtual_ecosystem.models.freshwater.constants import FreshwaterConsts
from virtual_ecosystem.models.freshwater.streamflow import calculate_streamflow
```

### Defining the new class and class attributes

Now create a new class, that derives from the
{mod}`~virtual_ecosystem.core.base_model.BaseModel`. To begin with, choose a class name
for the model and define the following class attributes.

The {attr}`~virtual_ecosystem.core.base_model.BaseModel.model_name` attribute
: This is a string providing the name that is used to refer to this model class in
configuration files. This **must** match the chosen submodule name for the model, so the
module `virtual_ecosystem.models.freshwater` must use `freshwater` as the model name.

The {attr}`~virtual_ecosystem.core.base_model.BaseModel.vars_required_for_init` attribute
: This is a tuple that sets which variables must be present in the data used to create a
new instance of the model. Each entry should provide a variable name and then another
tuple that sets any required axes for the variable. For example:

```{code-block} ipython3
()  # no required variables
(("temperature", ()),)  # temperature must be present, no core axes
(("temperature", ("spatial",)),)  # temperature must be present and on the spatial axis
```

The {attr}`~virtual_ecosystem.core.base_model.BaseModel.vars_updated` attribute : This
is a tuple that provides information about which data object variables are updated by
this model. Entries should simply be variable names. The information contained here is
used to determine which variables to include in the continuous output. So, it is
important to ensure that this information is up to date.

The {attr}`~virtual_ecosystem.core.base_model.BaseModel.model_update_bounds`
attribute :

This class attribute defines two time intervals that define a lower and upper bound
on the update frequency that can reasonably be used with a model. Models updated
more often than the lower bound may fail to capture transient dynamics and models
updated more slowly than the upper bound may fail to capture important temporal
patterns. Each attribute is a string that can be parsed by {class}`pint.Quantity`
into a time period

These values are set as class attributes by providing them as arguments to the class
signature. You will end up with something like the following:

```{code-block} ipython3

class FreshWaterModel(
    BaseModel,
    model_name="freshwater",
    model_update_bounds=("1 day", "1 month"),
    vars_required_for_init=(("temperature", ("spatial",)),),
    vars_updated=("average_P_concentration",),
):
    """Docstring describing model.

    Args:
        Describe arguments here
    """
```

### Defining the model `__init__` method

The next step is to define the `__init__` method for the class. This needs to do a few
things.

1. It should define any specific instance attributes of the new model class. For
  example, the class might require that the user set a number of ponds. These should be
  added to the signature of the `__init__` method, alongside the required parameters of
  the base class, and then stored as attributes of the instance.

1. It _must_ call the {meth}`~virtual_ecosystem.core.base_model.BaseModel.__init__`
   method of the {meth}`~virtual_ecosystem.core.base_model.BaseModel` parent class,
   also known as the superclass:

```{code-block} ipython3
super().__init__(data, update_interval, **kwargs)
```

   Calling this method runs all of the shared functionality across models, such as
   setting the update intervals and validating the input data.

1. The method should check that the provided initialisation values are sane, for example
  that the number of ponds is not negative.

1. The {meth}`~virtual_ecosystem.core.base_model.BaseModel` provides a basic `__repr__`
   to provide a simple text representation of a class object. This just prints the class
   name and a set of properties. You can add some or all of your custom model properties
   to the `__repr` property to include them in the representation.

You should end up with something like this:

```{code-block} ipython3
def __init__(
    self,
    data: Data,
    update_interval: pint.Quantity,
    no_of_ponds: int,
    constants: FreshwaterConsts,
    **kwargs: Any,
):

    # Sanity checking of input variables goes here
    if no_of_ponds < 0:
        to_raise = InitialisationError(
            "There has to be at least one pond in the freshwater model!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    # Call the __init__() method of the base class
    super().__init__(data, update_interval, **kwargs)

    # Store model specific details as attributes.
    self.no_of_ponds = int(no_of_ponds)

    # Store the constants relevant to the freshwater model
    self.constants = constants

    # Save attribute names to be used by the __repr__
    self._repr.append("no_of_ponds")
```

## Model configuration

The arguments to the model `__init__` method define the **model configuration**: a
collection of settings that set how the model runs. To allow the model to be defined and
run from a set of configuration files, the model now needs to define two things:

1. The model configuration schema, which is a JSONSchema document that defines the
   structure of the model configuration and can also be used to validate an input
   configuration.

1. A `from_config` factory method, which should take a dictionary containing
   configuration data and return an instance of the class configured using that data.

### The model configuration schema

The [JSONSchema](https://json-schema.org/) document in the module root directory defines
the configuration options for the model. A detailed description of the configuration
system works can be found [here](../../using_the_ve/configuration/config.md) but the
schema definition is used to validate configuration files for a Virtual Ecosystem
simulation that uses your model. Essentially, it defines all of the `__init__` arguments
that are unique to your model.

Writing JSONSchema documents can be very tedious. The following tools may be of use:

* [https://www.jsonschema.net/app](https://www.jsonschema.net/app): this is a web
  application that takes a data document - which is what the configuration file - and
  automatically generates a JSON schema to validate it. You will need to then edit it
  but you'll be starting with a valid schema!
* [https://jsonschemalint.com/](https://jsonschemalint.com/) works the other way. It
  takes a data document and a schema and checks whether the data is compliant. This can
  be useful for checking errors.

Both of those tools take data documents formatted as JSON as inputs, where we use TOML
configuration files, but there are lots of web tools to convert TOML to JSON and back.

As an example, the `FreshwaterModel` above might need two configuration options.

```toml
[freshwater]
update_interval = "1 month"
no_of_ponds = 3
```

The JSON Schema document generated from the JSON Schema app above is shown below. Some
of the fields - such as the `title` and `examples` entries - are not required in the
Virtual Ecosystem configuration and so can be deleted. You may also need to edit which
properties are required and which provide defaults that will be used to fill missing
properties.

```json
{
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "$id": "http://example.com/example.json",
    "type": "object",
    "default": {},
    "title": "Root Schema",
    "required": [
        "update_interval",
        "no_of_ponds"
    ],
    "properties": {
        "update_interval": {
            "type": "string",
            "default": "",
            "title": "The update_interval Schema",
            "examples": [
                "1 month"
            ]
        },
        "no_of_ponds": {
            "type": "integer",
            "default": 0,
            "title": "The no_of_ponds Schema",
            "examples": [
                3
            ]
        }
    },
    "examples": [{
        "update_interval": "1 month",
        "no_of_ponds": 3
    }]
}
```

#### Model dependencies

Your model may depend on a particular execution order for other models. For example, the
`freshwater` model might rely on data set up by the `hydrology` model, and so the
`hydrology` model needs to be initialised and updated before the `freshwater` model.
This is controlled using model configuration: although these dependencies may be
strong, it is more flexible to set them up through the configuration process than by
hard coding dependencies into the model objects themselves.

Your JSON Schema document therefore needs to include the following at the root level, so
that the model configuration includes a `[freshwater.depends]` section:

```json
"depends": {
    "type": "object",
    "default": {},
    "properties": {
        "init": {
            "type": "array",
            "default": ["hydrology"],
            "items": {
            "type": "string"
            }
        },
        "update": {
            "type": "array",
            "default": ["hydrology"],
            "items": {
            "type": "string"
            }
        }
    }
}
```

Note that this schema provides **default dependencies**, which set which models should
run before your model. There is no guarantee that users will necessarily include all of
these models in their configuration and the dependencies can always be overridden by
users. Configurations that do this may well not work, but that is for users to tackle.

### The `from_config` factory method

Configuration files are used to create a configuration object (see
{class}`~virtual_ecosystem.core.config.Config`), which contains details of the
configuration process but also provides a dictionary interface to the configuration
data. So, the example above might result in a `Config` object with the following model
specific data.

```{code-block} ipython3
{"freshwater": {"update_interval": "1 month", "no_of_ponds": 3}}
```

The job of the `from_config` method for a model is to take that configuration, along
with the shared `data` and `start_time` inputs, and then do any processing and
validating to convert the configuration into the arguments required by the `__init__`
method.

The method then uses those parsed arguments to actually call the `__init__` method and
return an initialised instance of the model using the settings. The `from_config`
method should raise an `InitialisationError` if the configuration fails.

The `from_config` method should also generate the required constants classes from the
config. At least one constants class should be created, but it's fine to split constants
across more classes if that makes for clearer code. For each constants class the
{func}`~virtual_ecosystem.core.constants_loader.load_constants` utility function can be
used to construct the class with the default values replaced if they are overwritten in
the config.

As an example:

```{code-block} ipython3
@classmethod
def from_config(
    cls, data: Data, config: Config, update_interval: Quantity
) -> FreshWaterModel:
    """Factory function to initialise the freshwater model from configuration.

    This function unpacks the relevant information from the configuration file, and
    then uses it to initialise the model. If any information from the config is
    invalid rather than returning an initialised model instance an error is raised.

    Args:
        data: A :class:`~virtual_ecosystem.core.data.Data` instance.
        config: A validated Virtual Ecosystem model configuration object.
        update_interval: Frequency with which all models are updated
    """

    # Non-timing details now extracted
    no_of_pools = config["freshwater"]["no_of_pools"]

    # Load in the relevant constants
    constants = load_constants(config, "freshwater", "FreshwaterConsts")

    LOGGER.info(
        "Information required to initialise the soil model successfully extracted."
    )
    return cls(data, update_interval, no_pools, constants)
```

## Other model steps

There are four functions that must be included as part of the model class. The names and
roles of these functions might well change as the Virtual Ecosystem model develops, but
that kind of API change is something that would require significant discussion. Only the
`update` function is used at present. The other functions need to be included, but
there's no need to include any particular content within them (i.e. they can just be
function definitions with docstrings).

```{code-block} ipython3
def setup(self) -> None:
    """Placeholder function to set up the freshwater model."""


def spinup(self) -> None:
    """Placeholder function to spin up the freshwater model."""


# While model updates have to take time_index as an argument, they do not necessarily
# have to use it anywhere
def update(self, time_index: int) -> None:
    """Function to update the freshwater model.

    Args:
        time_index: The index representing the current time step in the data object.
    """

    # Model simulation + update steps go in here.


def cleanup(self) -> None:
    """Placeholder function for freshwater model cleanup."""
```

## Setting up the model `__init__.py` file

Lastly, you will need to set up the `__init__.py` file in the submodule directory. This
file is used to tell Python that the directory contains a package submodule, but can
also be used to supply code that is automatically run when a module is imported.

In the Virtual Ecosystem, we use the `__init__.py` file in model submodules to:

* provide a brief overview of the module, and
* import the model object into the module root to make it easier to import.

The file will look something like:

```{code-block} python
"""This is the freshwater model module. The module level docstring should contain a
short description of the overall model design and purpose, and link to key components
and how they interact.
"""  # noqa: D204, D415

from virtual_ecosystem.models.freshwater.freshwater_model import (  # noqa: F401
    FreshwaterModel,
)
```

Under the hood, when a given model is used in a simulation, then the configuration
process automatically loads all of the model components for that model using the
{func}`~virtual_ecosystem.core.registry.register_module` function. This automatically
loads and validates the model schema, discovers any
{class}`~virtual_ecosystem.core.constants_class.ConstantsDataclass` in the `constants`
submodule and then adds those, along with the BaseModel subclass to a central
{data}`~virtual_ecosystem.core.registry.MODULE_REGISTRY` object, which is used to allow
the simulation code to easily access model components.
