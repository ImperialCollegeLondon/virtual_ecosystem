"""The :mod:`~virtual_ecosystem.models.abiotic.abiotic_model` module creates a
:class:`~virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
This implements the full complexity abiotic model.
"""  # noqa: D205

from __future__ import annotations

from typing import Any

from pyrealm.constants import CoreConst as PyrealmConst

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic.energy_balance import (
    initialise_canopy_and_soil_fluxes,
)
from virtual_ecosystem.models.abiotic.microclimate import run_microclimate
from virtual_ecosystem.models.abiotic_simple.constants import (
    AbioticSimpleBounds,
    AbioticSimpleConsts,
)
from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
    calculate_vapour_pressure_deficit,
    run_simple_microclimate,
)


class AbioticModel(
    BaseModel,
    model_name="abiotic",
    model_update_bounds=("1 hour", "1 month"),
    vars_required_for_init=(
        "air_temperature_ref",
        "relative_humidity_ref",
        "downward_shortwave_radiation",
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
    ),
    vars_populated_by_init=(
        "soil_temperature",
        "vapour_pressure_ref",
        "vapour_pressure_deficit_ref",
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "wind_speed",
        "atmospheric_pressure",
        "atmospheric_co2",
        "shortwave_absorption",
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
    ),
    vars_populated_by_first_update=(
        "longwave_emission",
        "specific_heat_air",
    ),
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
        handeled in :fun:`~virtual_ecosystem.abiotic.abiotic_model._setup`.
        """

        super().__init__(data, core_components, static, **kwargs)

        self.model_constants: AbioticConsts
        """Set of constants for the abiotic model."""
        self.simple_constants: AbioticSimpleConsts
        """Set of constants for simple abiotic model."""

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> AbioticModel:
        """Factory function to initialise the abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(config, "abiotic", "AbioticConsts")
        static = config["abiotic"]["static"]

        LOGGER.info(
            "Information required to initialise the abiotic model successfully "
            "extracted."
        )
        return cls(
            data,
            core_components=core_components,
            static=static,
            model_constants=model_constants,
        )

    def _setup(
        self, model_constants: AbioticConsts = AbioticConsts(), **kwargs
    ) -> None:
        """Function to set up the abiotic model.

        This function initializes soil temperature and canopy temperature for all
        corresponding layers and calculates the reference vapour pressure deficit for
        all time steps of the simulation. All variables are added directly to the
        self.data object.

        Args:
            model_constants: Set of constants for the abiotic model.
            **kwargs: Further arguments to the setup method.
        """

        self.model_constants = model_constants
        self.simple_constants = AbioticSimpleConsts()

        # create soil temperature array
        self.data["soil_temperature"] = self.layer_structure.from_template()

        # Calculate vapour pressure deficit at reference height for all time steps
        vapour_pressure_and_deficit = calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            pyrealm_const=PyrealmConst(),
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
            constants=self.simple_constants,
            bounds=AbioticSimpleBounds(),
        )

        # Generate initial profiles of canopy temperature and heat fluxes from soil and
        # canopy
        initial_canopy_and_soil = initialise_canopy_and_soil_fluxes(
            air_temperature=initial_microclimate["air_temperature"],
            topofcanopy_radiation=self.data["downward_shortwave_radiation"].isel(
                time_index=0
            ),
            leaf_area_index=self.data["leaf_area_index"],
            layer_heights=self.data["layer_heights"],
            layer_structure=self.layer_structure,
            light_extinction_coefficient=(
                self.model_constants.light_extinction_coefficient
            ),
            canopy_temperature_ini_factor=(
                self.model_constants.canopy_temperature_ini_factor
            ),
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

        TODO the units of fluxes are in W m-2 and we need to make sure that the input
        energy over a time interval is coherent with the calculations of fluxes in that
        time interval.

        Args:
            time_index: The index of the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """
        # Run microclimate model (TODO time interval = 1 h only for fluxes)
        update_dict = run_microclimate(
            data=self.data,
            time_index=time_index,
            time_interval=3600,
            cell_area=self.grid.cell_area,
            layer_structure=self.layer_structure,
            abiotic_constants=self.model_constants,
            core_constants=self.core_constants,
            pyrealm_const=PyrealmConst,
        )

        self.data.add_from_dict(output_dict=update_dict)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
