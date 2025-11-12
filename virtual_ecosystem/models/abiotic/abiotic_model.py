"""The :mod:`~virtual_ecosystem.models.abiotic.abiotic_model` module creates a
:class:`~virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
This implements the full complexity abiotic model.
"""  # noqa: D205

from __future__ import annotations

from typing import Any

from pyrealm.constants import CoreConst as PyrealmCoreConst

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConfiguration
from virtual_ecosystem.models.abiotic.energy_balance import (
    initialise_canopy_and_soil_fluxes,
)
from virtual_ecosystem.models.abiotic.microclimate import run_microclimate
from virtual_ecosystem.models.abiotic.model_config import (
    AbioticConfiguration,
    AbioticConstants,
)
from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
    calculate_vapour_pressure_deficit,
    run_simple_microclimate,
)
from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds


class AbioticModel(
    BaseModel,
    model_name="abiotic",
    model_update_bounds=("1 hour", "1 month"),
    vars_required_for_init=(
        "air_temperature_ref",
        "relative_humidity_ref",
        "leaf_area_index",
        "layer_heights",
        "wind_speed_ref",
    ),
    vars_updated=(
        "air_temperature",
        "canopy_temperature",
        "soil_temperature",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "wind_speed",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "density_air",
        "specific_heat_air",
        "latent_heat_vapourisation",
        "aerodynamic_resistance_canopy",
        "net_radiation",
    ),
    vars_required_for_update=(
        "air_temperature_ref",
        "relative_humidity_ref",
        "vapour_pressure_deficit_ref",
        "atmospheric_pressure_ref",
        "atmospheric_co2_ref",
        "wind_speed_ref",
        "leaf_area_index",
        "layer_heights",
        "downward_shortwave_radiation",
        "stomatal_conductance",
        "shortwave_absorption",
        "aerodynamic_resistance_surface",
        "soil_evaporation",
    ),
    vars_populated_by_init=(
        "soil_temperature",
        "vapour_pressure_ref",
        "vapour_pressure_deficit_ref",
        "air_temperature",
        "relative_humidity",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "wind_speed",
        "atmospheric_pressure",
        "atmospheric_co2",
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "net_radiation",
    ),
    vars_populated_by_first_update=("longwave_emission",),
):
    """A class describing the abiotic model.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        model_constants: Set of constants for the abiotic model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        static: bool = False,
        **kwargs: Any,
    ):
        """Abiotic init function.

        The init function is used only to define class attributes. Any logic should be
        handled in :fun:`~virtual_ecosystem.abiotic.abiotic_model._setup`.
        """

        super().__init__(data, core_components, static, **kwargs)

        self.model_constants: AbioticConstants
        """Set of constants for the abiotic model."""
        self.bounds: AbioticSimpleBounds
        """A set of bounds on microclimates variables, used with both the simple model
        of the initial state and the full energy balance calculations."""
        self.pyrealm_core_constants: PyrealmCoreConst
        """Pyrealm core constants."""

    @classmethod
    def from_config(
        cls,
        data: Data,
        configuration: CompiledConfiguration,
        core_components: CoreComponents,
    ) -> AbioticModel:
        """Factory function to initialise the abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            configuration: A validated Virtual Ecosystem model configuration object.
            core_components: The core components used across models.
        """

        # Extract the validated model configuration from the complete compiled
        # configuration. This syntax is odd but required to support static typing
        model_configuration: AbioticConfiguration = configuration.get_subconfiguration(
            "abiotic", AbioticConfiguration
        )

        core_configuration: CoreConfiguration = configuration.get_subconfiguration(
            "core", CoreConfiguration
        )

        LOGGER.info(
            "Information required to initialise the abiotic model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            static=model_configuration.static,
            model_constants=model_configuration.constants,
            pyrealm_core_constants=core_configuration.pyrealm.core,
            bounds=model_configuration.bounds,
        )

    def _setup(
        self,
        model_constants: AbioticConstants = AbioticConstants(),
        pyrealm_core_constants: PyrealmCoreConst = PyrealmCoreConst(),
        bounds: AbioticSimpleBounds = AbioticSimpleBounds(),
        **kwargs,
    ) -> None:
        """Function to set up the abiotic model.

        This function initializes soil temperature and canopy temperature for all
        corresponding layers and calculates the reference vapour pressure deficit for
        all time steps of the simulation. All variables are added directly to the
        self.data object.

        Args:
            model_constants: Set of constants for the abiotic model.
            pyrealm_core_constants: Additional configuration options to the pyrealm
                package.
            bounds: A set of bounds to be applied to abiotic variables.
            **kwargs: Further arguments to the setup method.
        """

        self.model_constants = model_constants
        self.pyrealm_core_constants = pyrealm_core_constants
        self.bounds = bounds

        # create soil temperature array
        self.data["soil_temperature"] = self.layer_structure.from_template()

        # Calculate vapour pressure deficit at reference height for all time steps
        vapour_pressure_and_deficit = calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            pyrealm_core_constants=self.pyrealm_core_constants,
        )
        self.data["vapour_pressure_deficit_ref"] = (
            vapour_pressure_and_deficit["vapour_pressure_deficit"]
        ).rename("vapour_pressure_deficit_ref")

        self.data["vapour_pressure_ref"] = (
            vapour_pressure_and_deficit["vapour_pressure"]
        ).rename("vapour_pressure_ref")

        # Generate initial profiles of air temperature [C], relative humidity [-],
        # vapour pressure deficit [kPa], soil temperature [C], atmospheric pressure
        # [kPa], and atmospheric :math:`\ce{CO2}` [ppm]
        initial_microclimate = run_simple_microclimate(
            data=self.data,
            layer_structure=self.layer_structure,
            time_index=0,
            constants=self.model_constants,
            core_constants=self.core_constants,
            bounds=self.bounds,
        )

        # Generate initial profiles of canopy temperature and heat fluxes from soil and
        # canopy
        initial_canopy_and_soil = initialise_canopy_and_soil_fluxes(
            air_temperature=initial_microclimate["air_temperature"],
            layer_structure=self.layer_structure,
            initial_flux_value=self.model_constants.initial_flux_value,
        )

        # Update data object
        for output_dict in (
            initial_microclimate,
            initial_canopy_and_soil,
        ):
            self.data.add_from_dict(output_dict=output_dict)

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic model."""

    def _update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic model.

        Args:
            time_index: The index of the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """
        # Run microclimate model
        update_dict = run_microclimate(
            data=self.data,
            time_index=time_index,
            time_interval=self.model_timing.update_interval_seconds,
            cell_area=self.grid.cell_area,
            layer_structure=self.layer_structure,
            abiotic_constants=self.model_constants,
            core_constants=self.core_constants,
            pyrealm_core_constants=self.pyrealm_core_constants,
            abiotic_bounds=self.bounds,
        )

        self.data.add_from_dict(output_dict=update_dict)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
