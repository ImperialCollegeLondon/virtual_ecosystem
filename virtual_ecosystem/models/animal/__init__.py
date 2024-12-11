"""The :mod:`~virtual_ecosystem.models.animal` module is one of the component models
of the Virtual Ecosystem. It is comprised of a number of submodules.

Each of the animal sub-modules has its own API reference page:

* The :mod:`~virtual_ecosystem.models.animal.animal_model` submodule instantiates the
  AnimalModel class which consolidates the functionality of the animal module
  into a single class, which the high level functions of the Virtual Ecosystem
  can then make use of.
* The :mod:`~virtual_ecosystem.models.animal.animal_cohorts` provides a class for the
  individual animal cohorts, their attributes, and behaviors.
* The :mod:`~virtual_ecosystem.models.animal.functional_group` provides a class for
  the animal functional groups that define the type of animal in an animal cohort.
* The :mod:`~virtual_ecosystem.models.animal.animal_traits` provides classes for
  the traits that feed into the functional group class definitions.
* The :mod:`~virtual_ecosystem.models.animal.scaling_functions` provides a set of
  allometric scaling functions that define the biological rates used in the animal
  module.
* The :mod:`~virtual_ecosystem.models.animal.constants` provides a set of dataclasses
  containing the constants required by the broader animal model.
* The :mod:`~virtual_ecosystem.models.animal.decay` provides a model for carcasses
  created by animal mortality, animal excrement and the litter available for animals to
  consume.
* The :mod:`~virtual_ecosystem.models.animal.plant_resources` provides the
  :class:`~virtual_ecosystem.models.animal.plant_resources.PlantResources` class,
  which provides an API for exposing plant model data via the animal model protocols.
"""  # noqa: D205

from virtual_ecosystem.models.animal.animal_model import AnimalModel  # noqa: F401
