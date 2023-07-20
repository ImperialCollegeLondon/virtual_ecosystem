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

## Using non-default values for constants

If you want to use a non-default value for a constant this can be accomplished using the
[configuration system](core/config.md). The configuration for each specific model
contains a `constants` section. Within this section constants are grouped based on the
name of the data class they belong to. An example of this can be seen below:

```toml
[example_model.constants.ExampleConsts]
example_constant_1 = 23.0
example_constant_2 = -7.7
```

Any values supplied in this way will be used to override the default values for the data
class in question. Only constants for which non-default values are supplied will be
replaced. Anything that is not included within the configuration will just take the
default value, which is set in the data class (see
[here](../development/defining_new_models.md) for further details).
