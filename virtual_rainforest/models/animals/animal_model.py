"""The :mod:`~virtual_rainforest.models.animals.animal_model` module creates a
:class:`~virtual_rainforest.models.animals.animal_model.AnimalModel` class as a
child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.setup` and
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the
Virtual Rainforest model develops. The factory method
:func:`~virtual_rainforest.models.animals.animal_model.AnimalModel.from_config`
exists in a more complete state, and unpacks a small number of parameters
from our currently pretty minimal configuration dictionary. These parameters are
then used to generate a class instance. If errors crop up here when converting the
information from the config dictionary to the required types
(e.g. :class:`~numpy.timedelta64`) they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled
by downstream functions so that all model configuration failures can be reported as one.
"""  # noqa: D205, D415


from __future__ import annotations

from math import sqrt
from typing import Any

from pint import Quantity

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.animal_communities import AnimalCommunity
from virtual_rainforest.models.animals.functional_group import FunctionalGroup


class AnimalModel(BaseModel):
    """A class describing the animal model.

    Describes the specific functions and attributes that the animal module should
    possess. Currently it is incomplete and mostly just a copy of the template set out
    in AnimalModel.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        start_time: Time at which the model is initialized.
    """

    model_name = "animals"
    """The model name for use in registering the model and logging."""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that soil model can sensibly capture."""
    upper_bound_on_time_scale = "1 month"
    """Longest time scale that soil model can sensibly capture."""
    required_init_vars = ()
    """Required initialisation variables for the animal model."""
    vars_updated = []
    """The animal model doesn't currently use the data object so nothing to update."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        functional_groups: list[FunctionalGroup],
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

        self.data.grid.set_neighbours(distance=sqrt(self.data.grid.cell_area))
        """Run a new set_neighbours (temporary solution)."""

        self.communities: dict[int, AnimalCommunity] = {
            k: AnimalCommunity(functional_groups) for k in self.data.grid.cell_id
        }
        """ Generate a dictionary of AnimalCommunity objects, one per grid cell."""

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> AnimalModel:
        """Factory function to initialise the animal model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) virtual rainforest configuration.
            update_interval: Frequency with which all models are updated
        """

        # Find timing details

        functional_groups_raw = config["animals"]["functional_groups"]

        functional_groups = []
        for k in functional_groups_raw:
            functional_groups.append(
                FunctionalGroup(k[0], k[1], k[2], k[3], k[4], k[5])
            )
        """create list of functional group objects to initialize  communities with."""

        LOGGER.info(
            "Information required to initialise the animal model successfully "
            "extracted."
        )
        return cls(data, update_interval, functional_groups)

    def setup(self) -> None:
        """Function to set up the animal model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the animal model."""

    def update(self, time_index: int) -> None:
        """Placeholder function to solve the animal model.

        Args:
            time_index: The index representing the current time step in the data object.
        """

    def cleanup(self) -> None:
        """Placeholder function for animal model cleanup."""

    def apply_community_method(
        self, community_method: str, *args: tuple, **kwargs: dict
    ) -> None:
        """This function applies community methods to all communities in the model.

        This function is a simplifying placeholder for what may need to be a number of
        different functions later one. Right now, it can be used to call the following
        functions for each AnimalCommunity within the AnimalModel.

        - populate_community()
        - forage_community()
        - migrate_community()
        - birth_community()
        - metabolize_community()
        - increase_age_community()
        - mortality_community()


        """
        for community in self.communities.values():
            method = getattr(community, community_method)
            method(*args, **kwargs)
