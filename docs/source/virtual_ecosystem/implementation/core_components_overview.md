
# Implementation of the core components

* The Config object, containing the validated configuration.
* The Grid object, containing the shared spatial structure of the simulation.
* The LayerStructure object, which is used to coordinate the vertical structure of the
  simulation from the top of the canopy down to the lowest soil layer.
* The CoreConstants object, which is used to provide fixed constant values that are
  shared across science models. Each model will have a separate model constants object
  that is used to set model-specific constants.
* The ModelTiming object, which is used to validate the runtime and update frequency of
  the simulation.
* The Data object, which is used to store all of the initial input data along with the
  variables representing the rest of the model state. This is also used to pass data
  between the different models.
