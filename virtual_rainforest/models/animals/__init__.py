"""The :mod:`~virtual_rainforest.models.animals` module is one of the component models
of the Virtual Rainforest. It is comprised of a number of submodules.

Each of the animal sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.models.animals.animal_model` submodule instantiates the
  AnimalModel class which consolidates the functionality of the animal module
  into a single class, which the high level functions of the Virtual Rainforest
  can then make use of.
* The :mod:`~virtual_rainforest.models.animals.animal_communities` provides a class for
  containing and managing all of the animal cohorts within a grid square.
* The :mod:`~virtual_rainforest.models.animals.animal_cohorts` provides a class for the
  individual animal cohorts, their attributes, and behaviors.
* The :mod:`~virtual_rainforest.models.animals.functional_group` provides a class for
  the animal functional groups that define the type of animal in an animal cohort.
* The :mod:`~virtual_rainforest.models.animals.animal_traits` provides classes for
  the traits that feed into the functional group class definitions.
* The :mod:`~virtual_rainforest.models.animals.scaling_functions` provides a set of
  allometric scaling functions that define the biological rates used in the animal
  module.
* The :mod:`~virtual_rainforest.models.animals.constants` provides a set of dataclasses
  containing the constants required by the broader animal model.
* The :mod:`~virtual_rainforest.models.animals.decay` provides a model for
  both surface carcasses created by mortality and animal excrement.
* The :mod:`~virtual_rainforest.models.animals.plant_resources` provides the
  :class:`~virtual_rainforest.models.animals.plant_resources.PlantResources` class,
  which provides an API for exposing plant model data via the animal model protocols.
"""  # noqa: D205, D415

from virtual_rainforest.models.animals.animal_model import AnimalModel  # noqa: F401
