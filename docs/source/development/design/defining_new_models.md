---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0.dev0
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

```{important}
When a model is used in the Virtual Ecosystem, the code relies on naming conventions to
access the different model components used in the model and register these components so
that they can be easily found from within the code - see the
{mod}`~virtual_ecosystem.core.registry` submodule for details.

You need to choose a unique model name that will be used to name the root model
directory, submodules within the model and then two critical model components. The name
will be used following two standard Python naming conventions:

* Model directory and file names use **snake case** (lower case with underscores): e.g.
  `abiotic` or `abiotic_simple`.
* Class names use **camel case** (capitalised words with no spaces): e.g. `Abiotic` and
  `AbioticSimple`.

The critical names are the model subclass and configuration subclasses and the example
below shows the required pattern.

* `abiotic_simple.abiotic_simple_model.AbioticSimpleModel`
* `abiotic_simple.model_config.AbioticSimpleConfiguration`
```

The rest of this page assumes that you are creating a new `freshwater` model.

## Create a new submodule folder

Start by creating  a new directory for your model within the `models` directory:
`virtual_ecosystem/models/freshwater`

You will then need to create the three files shown below within this folder:

* The init file `virtual_ecosystem/models/freshwater/__init__.py`. This is
  required to indicate to Python that the folder is a submodule within the
  `virtual_ecosystem` package, but we also use it to provide overview documentation of
  the model structure.
* The `virtual_ecosystem/models/freshwater/model_config.py` submodule, providing the
  `FreshwaterConfiguration` class that defines  the settings needed to configure how
  the model runs.
* The `virtual_ecosystem/models/freshwater/freshwater_model.py` submodule, providing the
  main `FreshwaterModel` class that implements the model itself.

It is very likely that you will also want to create additional code submodules within
this directory to split out different parts of the module functionality and  to keep
code files organised and a manageable size.

## The model `__init__.py` file

This file is used to tell Python that the directory contains a package submodule. It
_can_ be used to run code automatically when any component of the submodule is imported,
but in the Virtual Ecosystem, we only use the `__init__.py` to provide a brief overview
of the module as a docstring. It can be used to provide a short description of any
submodules and how they are used within the model. The submodule files should then have
their own docstring progviding more detail. These docstrings are automatically included
in the HTML documentation of the package.

A docstring should be formatted using block quotes, as below:

```{code-block} python
"""This is the freshwater model module. The module level docstring should contain a
short description of the overall model design and purpose, and link to key components
and how they interact.
"""  # noqa: D204, D415

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

All of your configuration models and fields must have clear docstrings that describe
what the model and fields are. As an example, the new `freshwater.model_config` module
might look like this:

```{code} python

class FreshwaterConstants(Configuration):
    """Constants settings for the freshwater model."""

    number_of_pools: int = 5
    """Number of pools to simulate."""
    ashrae_model_a: float = 95
    """The A constant of the ASHRAE evaporation model."""
    ashrae_model_b: float = Field(gt=0, default=37.4)
    """The B constant of the ASHRAE evaporation model."""
    molar_mass_water: ClassVar[float] = 18.01528
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
kind that should be held constant throughout a simulation. Many of the parameters
required in a Virtual Ecosystem simulation have been estimated from field data, The
values may have uncertainty or may vary significantly between sites. For this reason,
all parameters for your model should be included in your model configuration, to allow
other users to experiment with the results of changing variables and to explore the
sensitivity of model predictions to the configuration settings.

However, some variables are genuine constants, such as the molar mass of water in the
example above. The `pydantic` package has a few ways of fixing constants:

* For integer values and strings, the `Literal` type can be used to specify the exact
  value to be used and then no other value will be accepted. For example,
  {code}`number_of_pools: Literal[5] = 5`, would enforce a fixed number of pools.
* The `Literal` type cannot be used with floating point numbers, which is unfortunate
  since most parameters will be floats! You _can_ write a custom field validator that
  will enforce the specified default value.
* Alternatively, you can make the constant field a class attribute using `ClassVar`, as
  in the example above. Whenever the configuration model is used, it will always have
  this fixed value. Additionally, class attributes are not included when configuration
  models are dumped to file, so the constant field will not appear in the TOML version
  of the configuration. If users try to add it, it will be rejected. The class
  attributes _do_ occur in the configuration documentation though!

  This is probably the cleanest way to set fixed constants, but you should clearly
  document which parameters in your configuration cannot be changed.

The example model below shows the various options in practice:

```{code-block} ipython3
from pydantic import field_validator
from typing import ClassVar, Literal
from scipy import constants
from virtual_ecosystem.core.configuration import ModelConfigurationRoot, Configuration


class Example(Configuration):
    """An example configuration model."""

    f1: ClassVar[float] = 12.3
    """A constant float set as a class attribute. This field does not appear in the TOML
    representation of the model and cannot be changed."""
    f2: Literal[3] = 3
    """A constant  integer set using Literal. This field _does_ appear in the TOML
    representation of the model but users cannot change the value."""
    f3: float = constants.Boltzmann
    """The Bolzmann constant"""
    f4: float = constants.angstrom
    """One angstrom in metres."""

    @field_validator("f3", "f4", mode="after")
    @classmethod
    def enforce_constants(cls, value, context):
        """Custom validation to enforce constants in field f3 and f4."""

        fname = context.field_name
        constant_default = cls.model_fields[fname].default
        if not value == constant_default:
            raise ValueError(
                f"The {fname} field can only take the constant value {constant_default}"
            )
```

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
`ashrae_model_a: float = 95` - or be provided using `Field(default=...)`.

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
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.exceptions import InitialisationError
from virtual_ecosystem.core.logger import LOGGER

# You will likely also have a set of imports of model specific code such as constants
# classes and other classes and functions. For example:
from virtual_ecosystem.models.freshwater.model_config import FreshwaterConstants
from virtual_ecosystem.models.freshwater.streamflow import calculate_streamflow
```

### Defining the new class and class attributes

Now create a new class that derives from the
{mod}`~virtual_ecosystem.core.base_model.BaseModel`.

To begin with, choose a class name
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

```{admonition} Model dependencies
:class: tip

Your model may depend on a particular execution order for other models. This order is
found automatically by Virtual Ecosystem based on the variables that the models require
to be initialised and updated. Eg. if a model requires variable `A` to be initialised
and that variable is provided by another model, this second model will run first.

If a suitable order cannot be found, the simulation will stop and an error message will
be provided informing on the specific issue.
```

### Defining the model `__init__` method

The next step is to define the `__init__` method for the class. This needs to do a few
things, **in this order**:

1. It _must_ call the {meth}`~virtual_ecosystem.core.base_model.BaseModel.__init__`
   method of the {meth}`~virtual_ecosystem.core.base_model.BaseModel` parent class,
   also known as the superclass

   ```{code-block} ipython3
   super().__init__(data, update_interval, **kwargs)
   ```

   Calling this method runs all of the shared core functionality across models, such as
   setting the update intervals and validating that the input data provides the required
   variables to run the model.

1. It should define any specific attributes of the new model class. For
  example, the configuration above defines a path to a CSV file of pond data, which
  needs to be provided to the models and the set of model constants. These should be
  added to the signature of the `__init__` method, alongside the required parameters of
  the base class, and then stored as attributes of the instance.

1. The method should then _conditionally_ call the model `_setup` method. This method is
   used to run any code that is used to populate the initial state of the model.

   The call must be conditional because it is possible to configure a model so that all
   of the model state, including the data generated by the `_setup` method, is fixed by
   the initial inputs. In this case, the model should not run the setup step: this is
   indicated if the model `_run_setup` attribute is `False`.

1. The `__init__` method can also contain code that should be executed _regardless_ of
   the static configuration. For example, some models have can configure additional data
   export and so `__init__` would then need to set up the exporter process even when the
   model is running in static mode.

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
    pond_data_path: Path,
    constants: FreshwaterConstants,
):

    # Call the __init__() method of the base class
    super().__init__(data, update_interval)

    # Type and document attributes
    self.pond_data_path: Path
    """Path to the pond data file."""
    self.constants: FreshwaterConstants
    """Constants for the model."""

    # Conditionally run setup steps.
    if self._run_setup:
        self._setup(pond_data_path=pond_data_path, constants=constants)

    # Save attribute names to be used by the __repr__
    self._repr.append("pond_data_path")
```

### The `_setup` method

The `_setup` method typically contains the bulk of the code that needs to run to setup
the initial state of the model and populate the data variables listed in the
`_vars_populated_by_init` attribute. The signature of the function typically takes the
model specific arguments defined on the `__init__` method and uses those values to
populate model attributes and calculate data values. It is typical for `_setup` to call
additional methods that you define on the class or functions from additional submodules.

Following the example above:

```{code-block} ipython3
def _setup(self, pond_data_path: Path, constants: FreshwaterConstants) -> None:
    """Set up the freshwater model."""

    self.pond_data_path = pond_data_path
    self.constants = constants

    # Load the data using an extra method on the class
    self.load_pond_data(self.pond_data_path)

    # Populate a variable using a user defined method
    self.data["pond_temperature"] = calculate_pond_temperature(
      data=self.data, constants=self.constants, time_index=0
    )
```

### The `_update` method

The `_update` method must then be define to calculate the changes in the model state
that occur at each time step. The function _must_ have a `time_index` argument, which is
used by some models to iterate over data that follows a time series through a
simulation, such as climatic variables.

```{code-block} ipython3
def update(self, time_index: int) -> None:
    """Function to update the freshwater model.

    Args:
        time_index: The index representing the current time step in the data object.
    """

    # Recalculate the pond temperature based on the current conditions
    self.data["pond_temperature"] = calculate_pond_temperature(
      data=self.data, constants=self.constants, time_index=time_index
    )

```

### The `from_config` factory method

The job of the `from_config` method for a model is to take a validated configuration and
then do any processing and validating to convert the configuration into the arguments
required by the `__init__` method. The configuration object will contain sections for
all of the models being used in a simulation, so you should extract the configuration
for your model and then do any processing - this might simply be passing sections of the
configuration to the `__init__` method or might need to do some pre-processing.

The method then uses those parsed arguments to actually call the `__init__` method and
return an initialised instance of the model using the settings. The `from_config`
method should raise an `InitialisationError` if the configuration fails.

As an example:

```{code-block} ipython3
@classmethod
def from_config(
    cls, data: Data, configuration: Configuration, update_interval: Quantity
) -> FreshWaterModel:
    """Factory function to initialise the freshwater model from configuration.

    This function unpacks the relevant information from the configuration file, and
    then uses it to initialise the model. If any information from the config is
    invalid rather than returning an initialised model instance an error is raised.

    Args:
        data: A :class:`~virtual_ecosystem.core.data.Data` instance.
        configuration: A validated Virtual Ecosystem model configuration object.
        update_interval: Frequency with which all models are updated
    """

    # Extract the model configuration from the complete configuration.
    model_config: FreshwaterConfiguration = configuration.get_subconfiguration(
        "freshwater", FreshwaterConfiguration
    )

    pond_data_path = model_config.pond_data_path
    constants = model_config.constants


    LOGGER.info(
        "Information required to initialise the soil model successfully extracted."
    )
    return cls(
        data=data,
        update_interval=update_interval,
        pond_data_path=pond_data_path,
        constants=constants
    )
```

### Other model steps

There are currently two other method that must be included as part of the model class.
Neither of these are currently used, so can simply be included as function stubs with
docstrings as shown below:

```{code-block} ipython3
def spinup(self) -> None:
    """Placeholder function to spin up the freshwater model."""

def cleanup(self) -> None:
    """Placeholder function for freshwater model cleanup."""
```
