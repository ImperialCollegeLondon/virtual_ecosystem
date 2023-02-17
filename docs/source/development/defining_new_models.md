# How to add a new model to the Virtual Rainforest

The Virtual Rainforest is designed to be modular, meaning that the set of models to be
used in a particular run is configurable at the start of the simulation. We are starting
out by defining a core set of models (`abiotic`, `animals`, `plants` and `soil`), which
will generally all be included for the vast majority of simulations. In the future, it
might be desirable to include models for other aspects of rainforests (e.g.
`freshwater`, `disturbance`), or to include multiple modelling approaches for a process.
When this happens a new model should be created. This page will set out the process for
adding a new model to the Virtual Rainforest in a manner that allows it to be used
appropriately by the `core` simulation functionality.

## Define a new `Model` class

You should first start by defining a new folder for your model (within
`virtual_rainforest/models/`).

```bash
mkdir virtual_rainforest/models/freshwater
```

Within this folder a `python` script defining the model should be created. This script
should be called "{MODEL_NAME}_model.py".

```bash
touch virtual_rainforest/models/freshwater/freshwater_model.py
```

This script must import a number of things to be able to set up a new `Model` class
correctly.

```python
# One of the member functions of the Model class returns a class instance. mypy doesn't
# know how to handle this unless annotations are imported from __future__
from __future__ import annotations

# Any needed for type hints of the config dictionary as the values are of various types
from typing import Any

# Used by the timing loop to handle time units
import pint
# Used by timing loop to store date times, and time intervals, respectively
from numpy import datetime64, timedelta64

# Logging of relevant information handled by Virtual Rainforest logger module
from virtual_rainforest.core.logger import LOGGER
# New model class will inherit from BaseModel.
# InitialisationError is a custom exception, for case where a `Model` class cannot be
# properly initialised based on the data contained in the configuration
from virtual_rainforest.core.base_model import BaseModel, InitialisationError
```

The new model class is created using a class method, which means that the model is
automatically be added to the model registry when class inheritance occurs. The model is
added to the registry under the name set by the `model_name` attribute. This means that
this attribute should be populated (as a string) for every new model, and cannot be the
`model_name` of an already existing model.

```python
class FreshWaterModel(BaseModel):
    """Docstring describing model.

    Args:
        Describe arguments here
    """

    model_name = "freshwater"
    """The model name for use in registering the model and logging."""
```

With the basic class now defined an `__init__` function should be added to the class.
This should do a few things. Firstly, it should check that the provided initialisation
values are sane (e.g. number of ponds is not negative). Secondly, any model specific
attributes (e.g. number of ponds) should be stored, and general attributes should be
passed to the `__init__` of the base class. Finally, names of model specific attributes
should be appended to `__repr` so that they can be found (and printed) by `BaseModel`'s
`__repr__` function.

```python
def __init__(
    self,
    update_interval: timedelta64,
    start_time: datetime64,
    no_of_ponds: int,
    **kwargs: Any,
):
        
    # Sanity checking of input variables goes here
    if no_of_ponds < 0:
        to_raise = InitialisationError(
                "There has to be at least one pond in the freshwater model!"
            )
        LOGGER.error(to_raise)
        raise to_raise
        
    # Provide general attributes to the __init__ of the base class
    super().__init__(update_interval, start_time, **kwargs)
    # Store model specific details as attributes.
    self.no_of_ponds = int(no_of_ponds)
    # Save attribute names to be used by the __repr__
    self._repr.append("no_of_ponds")
```

Generally, `__init__` functions should only handle the most basic sanity checking and
should take in fairly simple variables. However, our configuration is stored in a
complex configuration object (a dictionary at the moment), which needs to be unpacked.
Furthermore, some of the information contained in the configuration has to be converted
to a more usable form (particularly time/date information). To accomplish this a
`from_config` factory method has to be defined. This function unpacks the configuration,
performs more complex sanity checks, and if necessary converts the information from the
configuration to a more usable form. This is a class method, and so creates a
initialised instance of the `Model` (and if it can't is raises an error).

```python
@classmethod
def from_config(cls, config: dict[str, Any]) -> FreshWaterModel:
    """Factory function to initialise the freshwater model from configuration.

    This function unpacks the relevant information from the configuration file, and
    then uses it to initialise the model. If any information from the config is
    invalid rather than returning an initialised model instance an error is raised.

    Args:
        config: The complete (and validated) Virtual Rainforest configuration.

    Raises:
        InitialisationError: If configuration data can't be properly converted
    """

    # Assume input is valid until we learn otherwise
    valid_input = True
    # Convert configuration values to the required format for the __init__
    try:
        raw_interval = pint.Quantity(config["freshwater"]["model_time_step"]).to(
            "minutes"
        )
        # Round raw time interval to nearest minute
        update_interval = timedelta64(int(round(raw_interval.magnitude)), "m")
        start_time = datetime64(config["core"]["timing"]["start_time"])
        no_of_pools = config["freshwater"]["no_of_pools"]
    # Catch cases where Values or dimensions are wrong
    except (
        ValueError,
        pint.errors.DimensionalityError,
        pint.errors.UndefinedUnitError,
    ) as e:
        valid_input = False
        LOGGER.error(
            "Configuration types appear not to have been properly validated. This "
            "problem prevents initialisation of the freshwater model. The first "
            "instance of this problem is as follows: %s" % str(e)
        )
    
    # If everything is fine initialise a class instance (using cls)
    if valid_input:
        LOGGER.info(
            "Information required to initialise the freshwater model successfully "
            "extracted."
        )
        return cls(update_interval, start_time, no_of_pools)
    else:
        # Otherwise raise an InitialisationError
        raise InitialisationError()
```

Every model class needs to include a function to update its Model state. The exact
details of what should be in this `update` function are yet to be decided, apart from
how to update the internal model timing loop.

```python
def update(self) -> None:
    """Function to update the freshwater model (only updates time currently)."""

    # Update internal model timing loop
    self.next_update += self.update_interval
```

In addition to the above, there are three other functions that must be included as part
of the model class. The names and roles of these functions might well change as the
Virtual Rainforest model develops, but that kind of API change is something that would
require significant discussion. These functions are not actually used at present, so
while they have to be included, there's no need to include any particular content within
them (i.e. they can just be function definitions with docstrings).

```python
def setup(self) -> None:
    """Placeholder function to spin up the freshwater model."""

def spinup(self) -> None:
    """Placeholder function to spin up the freshwater model."""

def cleanup(self) -> None:
    """Placeholder function for freshwater model cleanup."""
```

## Writing a schema for the module configuration

The root module directory **must** also contain a [JSONSchema](https://json-schema.org/)
document that defines the configuration options for the model.  A detailed description
of the configuration system works can be found
[here](../virtual_rainforest/core/config.md) but the schema definition is used to
validate configuration files for a Virtual Rainforest simulation that uses your model.

So the example model used here would need to provide the file:
`virtual_rainforest/models/freshwater/freshwater_schema.json`

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

## Setting up the model `__init__.py` file

All model directories need to include an `__init__.py` file. The simple presence of the
`__init__.py` file tells Python that the directory content should be treated as module,
but then the file needs to contain code to do two things:

1. The `__init__.py` file needs to register the JSONSchema file for the module. The
    {meth}`~virtual_rainforest.core.config.register_schema` function takes a module name
    and the path to the schema file and then, after checking the file can be loaded and is
    valid, adds the schema to the schema registry
    {data}`~virtual_rainforest.core.config.SCHEMA_REGISTRY`.

1. It also needs to import the main BaseModel subclass. So for example, it should import
    `FreshwaterModel` from the `virtual_rainforest.models.freshwater.freshwater_model`
    module. This gives a shorter reference for a commonly used object
    (`virtual_rainforest.models.freshwater.FreshwaterModel`) but it also means
    that the BaseModel class is always imported when the model module
    (`virtual_rainforest.models.freshwater`) is imported. This is used when the package
    is loaded to automatically discover all the BaseModel classes and register them.

    The class is not going to actually be used within the file, so needs `#noqa: 401`
    to suppress a `flake8` error.

The resulting `__init__.py` file should then look something like this:

```python
"""This is the freshwater model module. The module level docstring should contain a 
short description of the overall model design and purpose.
"""  # noqa: D204, D415

from importlib import resources

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.freshwater.freshwater_model import (
    FreshWaterModel  
) # noqa: 401

with resources.path(
    "virtual_rainforest.models.freshwater", "freshwater_schema.json"
) as schema_file_path:
    register_schema(module_name="freshwater", schema_file_path=schema_file_path)
```

When the `virtual_rainforest` package is loaded, it will automatically import
`virtual_rainforest.models.freshwater`. That will cause both the model and the schema to
be loaded and registered.
