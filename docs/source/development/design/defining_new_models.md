---
jupytext:
  formats: md:myst
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
---

# Creating new Virtual Ecosystem models

The Virtual Ecosystem initially contains a set of models defining core components of
an ecosystem, examples include the `abiotic`, `animal`, `plants` and `soil` models.
However, the simulation is designed to be modular:

* Different combinations of models can be configured for a particular simulation.
* New models can be defined in order to extend the simulation or alter the implementation:
  examples of new functionality might be `freshwater` or `disturbance` models.

This page sets out the steps needed to add a new model to the Virtual Ecosystem and
ensure that it can be accessed by the `core` processes in the simulation.

## Create a new submodule folder

Start by creating  a new folder for your model, within the `virtual_ecosystem/models/`
directory.

```bash
mkdir virtual_ecosystem/models/freshwater
```

You will need to create at least three files within this folder, although you may choose
to add other python modules containing different parts of the module functionality.

* An `__init__.py` file, which tells Python that the folder is a submodule within the
  `virtual_ecosystem` package.
* A python module  `{model_name}_model.py` that will contain the main model
  object.
* A python module `model_config.py` that defines the settings needed to configure how
  the model runs.

For example:

```bash
touch virtual_ecosystem/models/freshwater/__init__.py
touch virtual_ecosystem/models/freshwater/freshwater_model.py
touch virtual_ecosystem/models/freshwater/model_config.py
```

## Model configuration

The model configuration needs to define both model settings - such as paths to model
specific input files, method choices and the like - and model constants. These are
defined in the `model_config.py` as [Pydantic
models](https://docs.pydantic.dev/latest/concepts/models/), which are very close to
standard Python dataclasses but have built in support for validation and serialisation.
When the Virtual Ecosystem model runs using `ve_run`, the first thing that happens is
that specified configuration files are loaded and then validated using this
configuration models. This allows the model to detect bad configuration and provided
detailed error reports before any further processing.

Each Virtual Ecosystem model needs to provide a single root configuration model. This
root class must have a couple of specific features to allow it to be identified when the
simulation starts.

* The root configuration class name must derive from the model name using the following
  pattern: the `abiotic_simple` model would have the `AbioticSimpleConfiguration` root
  configuration class. Basically, underscores are dropped and words are capitalised.
* The class must inherit from a shared root model class:
  {class}`~virtual_ecosystem.core.configuration.ModelConfigurationRoot`. This is used to
  enforce some model settings:

  * Instances of model configuration are frozen so they cannot be changed during a run.
  * Configuration models are strict about extra data: is unknown settings are provided
    when a configuration model instance is created, it fails.

The `model_config.py` file can then also contain additional configuration classes that
can be nested within the root configuration to define a tree of configuration settings.
For example, all existing models define a separate class to hold constants. Any
additional class must inherit from the
{class}`~virtual_ecosystem.core.configuration.Configuration` class, which again freezes
configuration model instances and makes them intolerant of extra data.

As an example, the new `freshwater.model_config` module might look like this:

```{code} python

class FreshwaterConstants(Configuration):
    """Constants settings for the freshwater model."""

    ashrae_model_a: float = 95
    """The A constant of the ASHRAE evaporation model."""
    ashrae_model_b: float = Field(gt=0, default=37.4)
    """The B constant of the ASHRAE evaporation model."""
    molar_mass_water: Literal[18.01528] = 18.01528
    """The molar mass of water."""

class FreshwaterConfiguration(ModelConfigurationRoot):

    pond_data_path: FILEPATH_PLACEHOLDER
    """Path to a CSV file containing pond data for simulation cells."""
    constants: FreshwaterConstants = FreshwaterConstants()
    """The constants settings for the freshwater model."""
```

With these validation classes, an instance of the root model above can be easily created
by reading data from an appropriate file format ('de-serialised'). We use TOML for
configuration files and so an instance of model above could be created from TOML like
this:

```{code} toml
[freshwater]
pond_data_path = '/path/to/freswater_pond_data.csv'
[freshwater.constants]
ashrae_model_a = 96
ashrae_model_b = 38
```

Similarly, a model instance can be exported to a file format ('serialised') to provide a
record of the settings used in a particular model.

### Defining constants

The definition of 'constant' in the Virtual Ecosystem is basically a parameter of any
kind that should be held constant throughout a simulation. Some constants are likely
never to be altered, but many are estimated with error and users may want to explore the
sensitivity of simulations to changes in those values. For this reason, all constants
with your model should be included in your model configuration.

The example above for the molar mass of water shows how you can include a constant in
your configuration and stop users from altering it. If a different value was set in a
configuration file, then it would generate a configuration error.

### Validation

The `pydantic` package provides a wide range of validation tools to enforce conditions on
the fields within the configuration models.

* All pydantic fields must have a declared type - validation will fail if the input data
  does not match that type. So any attempt to set `ashrae_model_a` must provide a float.
* The `Field` class provides additional built-in constraints on provided values. Each
  type supports [different
  constraints](https://docs.pydantic.dev/latest/api/standard_library_types), but in the
  example above `Field(gt=0, default=37.4)` checks that the input value is greater than
  zero.
* In addition, you can add [custom
  validators](https://docs.pydantic.dev/latest/concepts/validators/) for fields or
  validators for the whole class.

You should be as precise as you can about the validation of your model settings: they
provide very strong guidance to users about how to configure a simulation. When values
fail validation, we are able to use the great error reporting built in to pydantic to
provide detailed information about conguration failures.

### Defaults

The example above provides defaults for all values and you should do the same. This is
partly to give users some kind of a sense check of what expected values look like, but
also because it is easy to export example configurations as templates when all fields
have defaults. Defaults can either be provided by assignment - as with
`ashrae_model_a: float = 95` or be provided using `Field(default=...)`.

When a model instance is created from configuration files (de-serialised), the defaults
will be used to fill in any missing settings. This is extremely useful if a user wants
to be able to just switch one value in setting without having a complete configuration
file.

### Paths in configuration classes

You may want your configuration file to point to resources stored in an external file,
as in the example above. This should not be used to load array data that uses the core
data axes, but can be used to load model specific initialisation data.

As an example, the plants model uses definitions of different plant functional types and
the initial plant cohort distributions. The most convenient way to provide these for the
model initialisation is in CSV files containing a data frame. Since this data is not
needed by the other models, they are passed to the model using the
`pft_definitions_path` and `cohort_data_path` configuration options.

There are some specific requirements for including paths in configuration models:

* The Virtual Ecosystem allows users to provide multiple configuration files - this
  allows users to build up a library of settings for different models and then can
  specify combination of different configurations.

  These files are compiled into a single set of configuration data before validation.
  However, if those configuration files provide relative paths to data files, then the
  relative paths may well break when the data is compiled. For this reason, the
  compilation process resolves all paths in a given configuration file to absolute paths
  before compiling the data. Although settings may be typed as paths in a
  configuration class, the compilation step comes before validation and there is no type
  information available. For this reason, you **must** use the `_path` suffix on
  configuration options that provide file paths. This naming convention allows the
  Virtual Ecosystem configuration to manage file paths to ensure that file paths are
  preserved when configuration files are compiled.

* File paths should obviously point to existing files, but that makes it hard to set
  meaningful default values for use in generating example or template configurations.
  The custom {class}`~virtual_ecosystem.core.configuration.FILEPATH_PLACEHOLDER` type
  used in the example above helps solve this issue. Under the hood, this type uses the
  pydantic `FilePath`, which will fail validation if the input path does not exist. It
  also sets the default values `<PLACEHOLDER>`, but has extended validation to
  specifically check that this placeholder default has not been left in configuration
  file in use.

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
# - an custom exception to cover model initialisation failure
# - the global LOGGER, used to report information to users.
from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER

# You will likely also have a set of imports of model specific code such as constants
# classes and other classes and functions. For example:
from virtual_ecosystem.models.freshwater.model_config import FreshwaterConstants
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
    constants: FreshwaterConstants,
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

#### Model dependencies

Your model may depend on a particular execution order for other models. This order is
found automatically by Virtual Ecosystem based on the variables that the models require
to be initialised and updated. Eg. if a model requires variable `A` to be initialised
and that variable is provided by another model, this second model will run first.

If a suitable order cannot be found, the simulation will stop and an error message will
be provided informing on the specific issue.

### The `from_config` factory method

The job of the `from_config` method for a model is to take that a validated
configuration model, along with the shared `data` and `start_time` inputs, and then do
any processing and validating to convert the configuration into the arguments required
by the `__init__` method.

The method then uses those parsed arguments to actually call the `__init__` method and
return an initialised instance of the model using the settings. The `from_config`
method should raise an `InitialisationError` if the configuration fails.

The `from_config` method should also extract the required constants classes from the
config. At least one constants class should be created, but it's fine to split constants
across more classes if that makes for clearer code.
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
def _setup(self) -> None:
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
