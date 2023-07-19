# Virtual Rainforest parameterisation

The Virtual Rainforest contains a very large number of constants. These constants are
assigned default values based on either site specific data or best estimates from the
literature. However, in many cases this still leads to significant uncertainty about
true values of constants. Because of this, the Virtual Rainforest is set up to allow all
constants to be changed. This allows end users to change constant values if they have
access to better estimates, and also allows for sensitivity analysis to be performed.

As a quick note on terminology, we have chosen to call all our parameters "constants",
despite many of them not being truly universal constants. This is to make it clear that
none of them should be changed within a given Virtual Rainforest simulation. Though it
is fine to use different values for them across different simulations.

## Defining constants and their default values

Each model should define a `constants.py` submodule. Constants and their default values
should be defined in this submodule using {func}`dataclasses.dataclass`. These constants
can be stored in a single data class or spread over multiple data classes. However,
having a large number of data classes is likely to make the downstream code messier, so
constants should only be split across multiple classes when there's a strong reason to
do so. It's also important that every constant is given an explicit type hint, otherwise
the default value cannot be overwritten. An example `constants.py` file is shown below:

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

## Using non-default values for constants

If you want to use a non-default value for a constant this can be accomplished using the
configuration system. The configuration for each specific model contains a `constants`
section. Within this section each constants are grouped based on the name of the data
class they belong to. An example of this can be seen below:

```toml
[example_model.constants.ExampleConsts]
example_constant_1 = 23.0
example_constant_2 = -7.7
```

Any values supplied in this way will be used to override the default values for the data
class in question. Only constants for which non-default values are supplied will be
replaced, anything that is not included within the configuration will just use the
default value.
