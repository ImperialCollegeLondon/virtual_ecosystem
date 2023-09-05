"""The :mod:`~virtual_rainforest.models.litter.litter_model` module creates a
:class:`~virtual_rainforest.models.litter.litter_model.LitterModel` class as a child of
the :class:`~virtual_rainforest.core.base_model.BaseModel` class. At present a lot of
the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.setup` and
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.litter.litter_model.LitterModel.from_config` exists in
a more complete state, and unpacks a small number of parameters from our currently
pretty minimal configuration dictionary. These parameters are then used to generate a
class instance. If errors crop here when converting the information from the config
dictionary to the required types (e.g. :class:`~numpy.timedelta64`) they are caught and
then logged, and at the end of the unpacking an error is thrown. This error should be
caught and handled by downstream functions so that all model configuration failures can
be reported as one.
"""  # noqa: D205, D415

# FUTURE - Potentially convert this model to use differential equations at some point.
# In reality, litter chemistry should change continuously with time not just at the
# final time step as in the current implementation. This is turn means that the decay
# rates should change continuously. I think the current implementation is fine, because
# this will be a small inaccuracy in a weakly coupled part of the model. However, if we
# ever become interested in precisely quantifying litter stocks then this should be
# refactored into a set of differential equations.

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.constants import load_constants
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import set_layer_roles
from virtual_rainforest.models.litter.constants import LitterConsts
from virtual_rainforest.models.litter.litter_pools import calculate_litter_pool_updates


class LitterModel(BaseModel):
    """A class defining the litter model.

    This model can be configured based on the data object and a config dictionary. At
    present the underlying model this class wraps is quite simple (i.e. two litter
    pools), but this will get more complex as the Virtual Rainforest develops.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The number of canopy layers to be modelled.
        constants: Set of constants for the litter model.
    """

    model_name = "litter"
    """An internal name used to register the model and schema"""
    lower_bound_on_time_scale = "30 minutes"
    """Shortest time scale that the litter model can sensibly capture."""
    upper_bound_on_time_scale = "3 months"
    """Longest time scale that the litter model can sensibly capture."""
    required_init_vars = (
        ("litter_pool_above_metabolic", ("spatial",)),
        ("litter_pool_above_structural", ("spatial",)),
        ("litter_pool_woody", ("spatial",)),
        ("litter_pool_below_metabolic", ("spatial",)),
        ("litter_pool_below_structural", ("spatial",)),
        ("lignin_above_structural", ("spatial",)),
        ("lignin_woody", ("spatial",)),
        ("lignin_below_structural", ("spatial",)),
    )
    """Required initialisation variables for the litter model.

    This is a set of variables that must be present in the data object used to create a
    LitterModel , along with any core axes that those variables must map on to."""
    vars_updated = (
        "litter_pool_above_metabolic",
        "litter_pool_above_structural",
        "litter_pool_woody",
        "litter_pool_below_metabolic",
        "litter_pool_below_structural",
        "lignin_above_structural",
        "lignin_woody",
        "lignin_below_structural",
    )
    """Variables updated by the litter model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: int,
        canopy_layers: int,
        constants: LitterConsts,
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

        # Check that litter pool data is appropriately bounded
        if (
            np.any(data["litter_pool_above_metabolic"] < 0.0)
            or np.any(data["litter_pool_above_structural"] < 0.0)
            or np.any(data["litter_pool_woody"] < 0.0)
            or np.any(data["litter_pool_below_metabolic"] < 0.0)
            or np.any(data["litter_pool_below_structural"] < 0.0)
        ):
            to_raise = InitialisationError(
                "Initial litter pools contain at least one negative value!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Check that lignin proportions are between 0 and 1
        if (
            np.any(data["lignin_above_structural"] < 0.0)
            or np.any(data["lignin_woody"] < 0.0)
            or np.any(data["lignin_below_structural"] < 0.0)
            or np.any(data["lignin_above_structural"] > 1.0)
            or np.any(data["lignin_woody"] > 1.0)
            or np.any(data["lignin_below_structural"] > 1.0)
        ):
            to_raise = InitialisationError(
                "Lignin proportions must be between 0 and 1!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.constants = constants
        """Set of constants for the litter model"""

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)
        # Find first soil layer from the list of layer roles
        self.top_soil_layer_index = next(
            i for i, v in enumerate(layer_roles) if v == "soil"
        )
        """The layer in the data object representing the first soil layer."""
        # Find first soil layer from the list of layer roles
        self.surface_layer_index = next(
            i for i, v in enumerate(layer_roles) if v == "surface"
        )
        """The layer in the data object representing the surface layer."""

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> LitterModel:
        """Factory function to initialise the litter model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.
            update_interval: Frequency with which all models are updated
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]

        # Load in the relevant constants
        constants = load_constants(config, "litter", "LitterConsts")

        LOGGER.info(
            "Information required to initialise the litter model successfully "
            "extracted."
        )
        return cls(data, update_interval, soil_layers, canopy_layers, constants)

    def setup(self) -> None:
        """Placeholder function to setup up the litter model."""

        # TODO - At some point this could be used to calculate an initial litter input
        # rate so that the soil model can be run before the litter model. Think we need
        # to decide how we are handling model order first though.

        # TODO - These variables should be created by the animal model, but it is not
        # yet linked into the full vr_run flow yet. Once it is this step should be
        # deleted.
        self.data["decomposed_excrement"] = DataArray(
            np.zeros_like(self.data.grid.cell_id),
            dims=["cell_id"],
            coords={
                "cell_id": self.data.grid.cell_id,
            },
            name="decomposed_excrement",
        )
        self.data["decomposed_carcasses"] = DataArray(
            np.zeros_like(self.data.grid.cell_id),
            dims=["cell_id"],
            coords={
                "cell_id": self.data.grid.cell_id,
            },
            name="decomposed_carcasses",
        )

    def spinup(self) -> None:
        """Placeholder function to spin up the litter model."""

    def update(self, time_index: int) -> None:
        """Calculate changes in the litter pools and use them to update the pools.

        Args:
            time_index: The index representing the current time step in the data object.
        """

        # Estimate water potentials based on soil moistures
        water_potential = convert_soil_moisture_to_water_potential(
            soil_moisture=self.data["soil_moisture"][
                self.top_soil_layer_index
            ].to_numpy(),
            air_entry_water_potential=self.constants.air_entry_water_potential,
            water_retention_curvature=self.constants.water_retention_curvature,
            saturated_water_content=self.constants.saturated_water_content,
        )

        # Find litter pool updates using the litter pool update function
        updated_litter_pools = calculate_litter_pool_updates(
            surface_temp=self.data["air_temperature"][
                self.surface_layer_index
            ].to_numpy(),
            topsoil_temp=self.data["soil_temperature"][
                self.top_soil_layer_index
            ].to_numpy(),
            water_potential=water_potential,
            constants=self.constants,
            update_interval=self.update_interval.to("day").magnitude,
            above_metabolic=self.data["litter_pool_above_metabolic"].to_numpy(),
            above_structural=self.data["litter_pool_above_structural"].to_numpy(),
            woody=self.data["litter_pool_woody"].to_numpy(),
            below_metabolic=self.data["litter_pool_below_metabolic"].to_numpy(),
            below_structural=self.data["litter_pool_below_structural"].to_numpy(),
            lignin_above_structural=self.data["lignin_above_structural"].to_numpy(),
            lignin_woody=self.data["lignin_woody"].to_numpy(),
            lignin_below_structural=self.data["lignin_below_structural"].to_numpy(),
            decomposed_excrement=self.data["decomposed_excrement"].to_numpy(),
            decomposed_carcasses=self.data["decomposed_carcasses"].to_numpy(),
        )

        # Update the litter pools
        self.data.add_from_dict(updated_litter_pools)

    def cleanup(self) -> None:
        """Placeholder function for litter model cleanup."""


def convert_soil_moisture_to_water_potential(
    soil_moisture: NDArray[np.float32],
    air_entry_water_potential: float,
    water_retention_curvature: float,
    saturated_water_content: float,
) -> NDArray[np.float32]:
    """Convert soil moisture into an estimate of water potential.

    This function provides a coarse estimate of soil water potential. It is taken from
    :cite:t:`campbell_simple_1974`.

    TODO - This is a stopgap solution until we decide on a systematic way of handling
    water potentials across the relevant models (`soil`, `litter`, `plants` and
    `hydrology`).

    Args:
        soil_moisture: Volumetric relative water content [unitless]
        air_entry_water_potential: Water potential at which soil pores begin to aerate
            [kPa]
        water_retention_curvature: Curvature of water retention curve [unitless]
        saturated_water_content: The relative water content at which the soil is fully
            saturated [unitless].

    Returns:
        An estimate of the water potential of the soil [kPa]
    """

    return air_entry_water_potential * (
        (soil_moisture / saturated_water_content) ** water_retention_curvature
    )
