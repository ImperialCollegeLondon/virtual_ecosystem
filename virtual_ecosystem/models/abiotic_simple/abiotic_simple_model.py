"""The :mod:`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model` module
creates a
:class:`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.

Todo:
* update temperatures to Kelvin
* pressure and CO2 profiles should only be filled for filled/true above ground layers
"""  # noqa: D205

from __future__ import annotations

from typing import Any

from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import (
    CoreComponents,
    CoreConsts,
    LayerStructure,
)
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic.wind import calculate_wind_profile
from virtual_ecosystem.models.abiotic_simple import microclimate
from virtual_ecosystem.models.abiotic_simple.constants import (
    AbioticSimpleBounds,
    AbioticSimpleConsts,
)


class AbioticSimpleModel(
    BaseModel,
    model_name="abiotic_simple",
    model_update_bounds=("1 day", "1 month"),
    vars_required_for_init=(
        "air_temperature_ref",
        "relative_humidity_ref",
        "atmospheric_pressure_ref",
        "atmospheric_co2_ref",
        "leaf_area_index",
        "layer_heights",
        "wind_speed_ref",
        "mean_annual_temperature",
    ),
    vars_updated=(
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
        "wind_speed",
        "molar_density_air",
        "specific_heat_air",
    ),
    vars_required_for_update=(
        "air_temperature_ref",
        "relative_humidity_ref",
        "vapour_pressure_deficit_ref",
        "atmospheric_pressure_ref",
        "atmospheric_co2_ref",
        "leaf_area_index",
        "layer_heights",
        "sensible_heat_flux",
        "wind_speed_ref",
        "mean_annual_temperature",
    ),
    vars_populated_by_init=(  # TODO move functionality from setup() to __init__
        "soil_temperature",
        "vapour_pressure_ref",
        "vapour_pressure_deficit_ref",
        "air_temperature",
        "relative_humidity",
        "atmospheric_pressure",
        "atmospheric_co2",
        "vapour_pressure_deficit",
        "sensible_heat_flux",
        "wind_speed",
        "molar_density_air",
        "specific_heat_air",
    ),
    vars_populated_by_first_update=(),
):
    """A class describing the abiotic simple model.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        model_constants: Set of constants for the abiotic_simple model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        model_constants: AbioticSimpleConsts = AbioticSimpleConsts(),
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        self.model_constants = model_constants
        """Set of constants for the abiotic simple model"""
        self.bounds = AbioticSimpleBounds()
        """Upper and lower bounds for abiotic variables."""
        self.abiotic_constants = AbioticConsts()
        """Set of constants shared with the process-based abiotic model."""

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> AbioticSimpleModel:
        """Factory function to initialise the abiotic simple model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(
            config, "abiotic_simple", "AbioticSimpleConsts"
        )

        LOGGER.info(
            "Information required to initialise the abiotic simple model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            model_constants=model_constants,
        )

    def setup(self) -> None:
        """Function to set up the abiotic simple model.

        This function initializes soil temperature for all soil layers and calculates
        the reference vapour pressure deficit for all time steps. Both variables are
        added directly to the self.data object.

        The function also creates initial profiles of microclimatic variables and
        sets fluxes to zero (this is required for the hydrology model and held constant
        over the simulation).
        """

        # create soil temperature array
        self.data["soil_temperature"] = self.layer_structure.from_template()

        # calculate vapour pressure deficit at reference height for all time steps
        vapour_pressure_and_deficit = microclimate.calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            saturation_vapour_pressure_factors=(
                self.model_constants.saturation_vapour_pressure_factors
            ),
        )
        self.data["vapour_pressure_deficit_ref"] = vapour_pressure_and_deficit[
            "vapour_pressure_deficit"
        ]
        self.data["vapour_pressure_ref"] = vapour_pressure_and_deficit[
            "vapour_pressure"
        ]

        # Generate initial profiles of air temperature [C], relative humidity [-],
        # vapour pressure deficit [kPa], soil temperature [C], atmospheric pressure
        # [kPa], and atmospheric :math:`\ce{CO2}` [ppm]
        initial_microclimate = microclimate.run_microclimate(
            data=self.data,
            layer_structure=self.layer_structure,
            time_index=0,
            constants=self.model_constants,
            bounds=AbioticSimpleBounds(),
        )

        # Sensible heat flux is a required variable for the wind update
        self.data["sensible_heat_flux"] = self.layer_structure.from_template()
        self.data["sensible_heat_flux"][self.layer_structure.index_flux_layers] = 0

        initial_wind = update_wind(
            data=self.data,
            microclimate_data=initial_microclimate,
            layer_structure=self.layer_structure,
            time_index=0,
            abiotic_constants=self.abiotic_constants,
            core_constants=self.core_constants,
        )

        # Update data object
        for output_dict in (
            initial_microclimate,
            initial_wind,
        ):
            self.data.add_from_dict(output_dict=output_dict)

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic simple model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic simple model.

        Args:
            time_index: The index of the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # This section performs a series of calculations to update the variables in the
        # abiotic model. The updated variables are then added to the data object.
        microclimate_out = microclimate.run_microclimate(
            data=self.data,
            layer_structure=self.layer_structure,
            time_index=time_index,
            constants=self.model_constants,
            bounds=self.bounds,
        )

        wind_out = update_wind(
            data=self.data,
            microclimate_data=microclimate_out,
            layer_structure=self.layer_structure,
            time_index=time_index,
            abiotic_constants=self.abiotic_constants,
            core_constants=self.core_constants,
        )

        for output_dict in [microclimate_out, wind_out]:
            self.data.add_from_dict(output_dict=output_dict)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""


def update_wind(
    data: Data,
    microclimate_data: dict[str, DataArray],
    layer_structure: LayerStructure,
    time_index: int,
    abiotic_constants: AbioticConsts,
    core_constants: CoreConsts,
) -> dict[str, DataArray]:
    """Update wind speed, molar density of air, and specific heat of air.

    This function wraps the steps to update the wind profile and returns the subset of
    variables that are relevant for the abiotic simple model.

    Args:
        data: Data instance
        microclimate_data: Dictionary with microclimate varaibles for current time step
        layer_structure: LayerStructure instance
        time_index: Time index
        abiotic_constants: Set of constants for the abiotic model
        core_constants: Set of constants shared across all models

    Returns:
        dictionary with "wind_speed", "molar_density_air", "specific_heat_air"
    """
    # TODO: this type-ignore is because our Data interface doesn't currently accept
    #       list[str] indices, which it should.
    update_inputs = data[
        ["layer_heights", "leaf_area_index"]  # type: ignore [index]
    ].isel(layers=layer_structure.index_filled_atmosphere)
    air_temperature = microclimate_data["air_temperature"].isel(
        layers=layer_structure.index_filled_atmosphere
    )

    wind_update = calculate_wind_profile(
        canopy_height=data["layer_heights"][1].to_numpy(),
        wind_height_above=data["layer_heights"][0:2].to_numpy(),
        wind_layer_heights=update_inputs["layer_heights"].to_numpy(),
        leaf_area_index=update_inputs["leaf_area_index"].to_numpy(),
        air_temperature=air_temperature.to_numpy(),
        atmospheric_pressure=microclimate_data["atmospheric_pressure"][0].to_numpy(),
        sensible_heat_flux_topofcanopy=data["sensible_heat_flux"][1].to_numpy(),
        wind_speed_ref=data["wind_speed_ref"].isel(time_index=time_index).to_numpy(),
        wind_reference_height=(
            data["layer_heights"][1] + abiotic_constants.wind_reference_height
        ).to_numpy(),
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )  # TODO wind height above in constants, cross-check with LayerStructure setup

    # Store 2D wind outputs using the full vertical structure
    wind_out = {}
    for var in ["wind_speed", "molar_density_air", "specific_heat_air"]:
        wind_out[var] = layer_structure.from_template()
        wind_out[var][layer_structure.index_filled_atmosphere] = wind_update[var]

    return wind_out
