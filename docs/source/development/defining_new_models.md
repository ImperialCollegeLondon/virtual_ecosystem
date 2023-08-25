---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: vr_python3
  language: python
  name: vr_python3
---

# Creating new Virtual Rainforest models

The Virtual Rainforest initially contains a set of models defining four core components
of the rainforest: the `abiotic`, `animals`, `plants` and `soil` models. However, the
simulation is designed to be modular:

* Different combinations of models can be configured for a particular simulation, and
* New models can be defined in order to extend the simulation or alter the implemention:
  examples of new functionality might be `freshwater` or `disturbance` models.

This page sets out the steps needed to add a new model to the Virtual Rainforest and
ensure that it can be accessed by the `core` processes in the simulation.

## Create a new submodule folder

Start by creating  a new folder for your model, within the `virtual_rainforest/models/`
directory.

```bash
mkdir virtual_rainforest/models/freshwater
```

You will need to create at least four files within this folder, although you may choose
to add other python modules containing different parts of the module functionality.

* An `__init__.py` file, which tells Python that the folder is a submodule within the
  `virtual_rainforest` package.
* A python module  `{model_name}_model.py` that will contain the main model
  object.
* A JSON Schema file defining the model configuration, called `model_schema.json`.
* A python module  `constants.py` that will contain the constants relevant to the model.

For example:

```bash
touch virtual_rainforest/models/freshwater/__init__.py
touch virtual_rainforest/models/freshwater/freshwater_model.py
touch virtual_rainforest/models/freshwater/model_schema.json
touch virtual_rainforest/models/freshwater/constants.py
```

## Defining constants and their default values

Each model should define a `constants.py` module. Constants and their default values
should be defined in this module using {func}`dataclasses.dataclass`. These constants
can be stored in a single data class or spread over multiple data classes. However,
having a large number of data classes is likely to make the downstream code messier, so
constants should only be split across multiple classes when there's a strong reason to
do so.

It's also important that every constant is given an explicit type hint. If a type hint
is not provided then `dataclass` treats the constant as a class attribute rather than an
instance attribute. This means that its value cannot be changed when a new instance is
created.

An example `constants.py` file is shown below:

```python
from dataclasses import dataclass

# The dataclass must be frozen to prevent constants from being accidentally altered
# during runtime
@dataclass(frozen=True)
class ExampleConsts:
    """Dataclass to store all constants for the `example_model` model."""
    
    # Each constant must be given a type hint, otherwise its default value cannot be
    # changed
    example_constant_1: float = -1.27
    """Details of source of constant and its units."""

    example_constant_2: float = 5.4
    """Details of source of constant and its units."""
```

## Defining the new model class

The model file will define a new subclass of the
{mod}`~virtual_rainforest.core.base_model.BaseModel` class.

### Required package imports

Before you create this subclass, you will need to import some packages are required by
the `BaseModel` class. You may of course need to import other packages to support your
model code, but you will need the following:

```python
# One of the member functions of the Model class returns a class instance. mypy doesn't
# know how to handle this unless annotations are imported from __future__
from __future__ import annotations

# Any needed for type hints of the config dictionary as the values are of various types
from typing import Any

# pint.Quantity allows time units to be more easily interpreted
from pint import Quantity

# The core data storage object
from virtual_rainforest.core.data import Data

# Logging of relevant information handled by Virtual Rainforest logger module
from virtual_rainforest.core.logger import LOGGER

# New model class will inherit from BaseModel.
from virtual_rainforest.core.base_model import BaseModel

# InitialisationError is a custom exception, for case where a `Model` class cannot be
# properly initialised based on the data contained in the configuration
from virtual_rainforest.core.exceptions import InitialisationError
```

### Defining the new class and class attributes

Now create a new class, that derives from the
{mod}`~virtual_rainforest.core.base_model.BaseModel`. To begin with, choose a class name
for the model and define the following four class attributes.

The {attr}`~virtual_rainforest.core.base_model.BaseModel.model_name` attribute
: This is a string providing a shorter, lower case  name that is used to refer to this
model class in configuration files. It must be unique and model loading will fail if two
model classes share a `model_name`.

The {attr}`~virtual_rainforest.core.base_model.BaseModel.required_init_vars` attribute
: This is a tuple that sets which variables must be present in the data used to create a
new instance of the model. Each entry should provide a variable name and then another
tuple that sets any required axes for the variable. For example:

```python
()  # no required variables
(('temperature', ()),) # temperature must be present, no core axes
(('temperature', ('spatial',)),) # temperature must be present and on the spatial axis
```

The {attr}`~virtual_rainforest.core.base_model.BaseModel.vars_updated` attribute : This
is a tuple that provides information about which data object variables are updated by
this model. Entries should simply be variable names. The information contained here is
used to determine which variables to include in the continuous output. So, it is
important to ensure that this information is up to date.

The {attr}`~virtual_rainforest.core.base_model.BaseModel.lower_bound_on_time_scale`
attribute: This is the shortest time scale for which the model is a realistic
simulation. This attribute is a string, which should include units that can be parsed
using `pint`.

The {attr}`~virtual_rainforest.core.base_model.BaseModel.upper_bound_on_time_scale`
attribute: This is the longest time scale for which the model is a realistic simulation.
Again this attribute is a string, which should include units that can be parsed using
`pint`.

You will end up with something like the following:

```python
class FreshWaterModel(BaseModel):
    """Docstring describing model.

    Args:
        Describe arguments here
    """

    model_name = "freshwater"
    """The model name for use in registering the model and logging."""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that freshwater model can sensibly capture."""
    upper_bound_on_time_scale = "1 month"
    """Longest time scale that freshwater model can sensibly capture."""
    required_init_vars = (('temperature', ('spatial', )), )
    """The required variables and axes for the Freshwater Model"""
    vars_updated = ("average_P_concentration",)
    """Variables updated by the freshwater model."""
```

### Defining the model `__init__` method

The next step is to define the `__init__` method for the class. This needs to do a few
things.

1. It should define any specific attributes of the new model class. For example, the
  class might require that the user set a number of ponds. These should be added to the
  signature of the `__init__` method, alongside the required parameters of the base
  class, and then stored as attributes of the class.

1. It _must_ call the {meth}`~virtual_rainforest.core.base_model.BaseModel.__init__`
   method of the {meth}`~virtual_rainforest.core.base_model.BaseModel` parent class,
   also known as the superclass:

   ```python
   super().__init__(data, update_interval, **kwargs)
   ```

   Calling this method runs all of the shared functionality across models, such as
   setting the update intervals and validating the input data.

1. The method should check that the provided initialisation values are sane, for example
  that the number of ponds is not negative.

1. The {meth}`~virtual_rainforest.core.base_model.BaseModel` provides a basic `__repr__`
   to provide a simple text representation of a class object. This just prints the class
   name and a set of properties. You can add some or all of your custom model properties
   to the `__repr` property to include them in the representation.

You should end up with something like this:

```python
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
system works can be found [here](../virtual_rainforest/core/config.md) but the schema
definition is used to validate configuration files for a Virtual Rainforest simulation
that uses your model. Essentially, it defines all of the `__init__` arguments that are
unique to your model.

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
Virtual Rainforest configuration and so can be deleted. You may also need to edit which
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

### The `from_config` factory method

When a configuration file is read in, it is converted into a Python dictionary. So, the
example above might result in:

```python
{'freshwater': {'update_interval': "1 month",  "no_of_ponds": 3}}
```

The job of the `from_config` method is to take that dictionary, along with the shared
`data` and `start_time` inputs, and then do any processing and validating to convert the
configuration into the arguments required by the `__init__` method.

The method then uses those parsed arguments to actually call the `__init__` method and
return an initialised instance of the model using the settings. The `from_config`
method should raise an `InitialisationError` if the configuration fails.

The `from_config` method should also generate the required constants classes from the
config. At least one constants class should be created, but it's fine to split constants
across more classes if that makes for clearer code. For each constants class the
{func}`~virtual_rainforest.core.constants.load_constants` utility function can be used
to construct the class with the default values replaced if they are overwritten in the
config.

As an example:

```python
@classmethod
def from_config(
    cls, data: Data, config: dict[str, Any], update_interval: Quantity
) -> FreshWaterModel:
    """Factory function to initialise the freshwater model from configuration.

    This function unpacks the relevant information from the configuration file, and
    then uses it to initialise the model. If any information from the config is
    invalid rather than returning an initialised model instance an error is raised.

    Args:
        data: A :class:`~virtual_rainforest.core.data.Data` instance.
        config: The complete (and validated) Virtual Rainforest configuration.
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
roles of these functions might well change as the Virtual Rainforest model develops, but
that kind of API change is something that would require significant discussion. Only the
`update` function is used at present. The other functions need to be included, but
there's no need to include any particular content within them (i.e. they can just be
function definitions with docstrings).

```python
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

Lastly, you will need to set up the `__init__.py` file. The simple presence of the
`__init__.py` file tells Python that the directory content should be treated as module,
but then the file needs to contain code to do three things:

1. It also needs to import the main BaseModel subclass. So for example, it should import
    `FreshwaterModel` from the `virtual_rainforest.models.freshwater.freshwater_model`
    module. This gives a shorter reference for a commonly used object
    (`virtual_rainforest.models.freshwater.FreshwaterModel`) but it also means
    that the BaseModel class is always imported when the model module
    (`virtual_rainforest.models.freshwater`) is imported.

    When the package is loaded, all of the submodules `virtual_rainforest.models` are
    loaded. This automatically triggers the registration of each model class in the
    {data}`~virtual_rainforest.core.base_model.MODEL_REGISTRY`, under the
    {attr}`~virtual_rainforest.core.base_model.BaseModel.model_name` attribute for the class.

1. The `__init__.py` file also needs to register the JSONSchema file for the module, and
   also add any constants classes to the registry. Both of these things are handled by
   the {func}`~virtual_rainforest.core.base_model.register_model` helper function. This
   function checks that the schema file can be loaded and is valid JSONSchema, and then
   adds the schema to the {data}`~virtual_rainforest.core.config.SCHEMA_REGISTRY`. It
   also automatically discovers constants classes and adds them to the
   {data}`~virtual_rainforest.core.constants.CONSTANTS_REGISTRY`.

The resulting `__init__.py` file should then look something like this:

```python
"""This is the freshwater model module. The module level docstring should contain a 
short description of the overall model design and purpose.
"""  # noqa: D204, D415

from virtual_rainforest.core.base_model import register_model
from virtual_rainforest.models.freshwater.freshwater_model import FreshwaterModel


register_model(__name__, FreshwaterModel)
```
