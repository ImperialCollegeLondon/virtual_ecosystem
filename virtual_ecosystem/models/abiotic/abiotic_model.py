"""The :mod:`~virtual_ecosystem.models.abiotic.abiotic_model` module creates a
:class:`~virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
This implements the full complexity abiotic model.

TODO There are currently a number of unresolved/not implemented processes which require
further advancement in other models of the Virtual Ecosystem or potentially some changes
to the vertical layer structure:

* add process based calculation of soil temperature
* change temperatures to Kelvin
* adjust for soil moisture default in mm (once updated in hydrology model)
* coordinate latent heat flux/evapotranspiration processes between plants and abiotic
* add soil fluxes to lower atmosphere (might need to drop 'subcanopy' layer)
* introducte 'metaconstants' to support sharing of constants between models
* add self.model_timing.update_interval in seconds as input to soil balance
* expand tests to cover different atmospheric conditions
* expand use of LayerStructure and shape for more compact concatenating

"""  # noqa: D205

from __future__ import annotations

from typing import Any

from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic import (
    conductivities,
    energy_balance,
    soil_energy_balance,
    wind,
)
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic_simple import microclimate
from virtual_ecosystem.models.abiotic_simple.constants import (
    AbioticSimpleBounds,
    AbioticSimpleConsts,
)


class AbioticModel(
    BaseModel,
    model_name="abiotic",
    model_update_bounds=("1 hour", "1 month"),
    vars_required_for_init=(
        "air_temperature_ref",
        "relative_humidity_ref",
        "topofcanopy_radiation",
        "leaf_area_index",
        "layer_heights",
    ),
    vars_updated=(
        "air_temperature",
        "canopy_temperature",
        "soil_temperature",
        "vapour_pressure",
        "vapour_pressure_deficit",
        "air_heat_conductivity",
        "conductivity_from_ref_height",
        "leaf_air_heat_conductivity",
        "leaf_vapour_conductivity",
        "wind_speed",
        "friction_velocity",
        "zero_displacement_height",
        "attenuation_coefficient",
        "mean_mixing_length",
        "relative_turbulence_intensity",
        "diabatic_correction_heat_above",
        "diabatic_correction_momentum_above",
        "diabatic_correction_heat_canopy",
        "diabatic_correction_momentum_canopy",
        "sensible_heat_flux",
        "sensible_heat_flux_soil",
        "latent_heat_flux",
        "latent_heat_flux_soil",
        "ground_heat_flux",
        "soil_absorption",
        "longwave_emission_soil",
        "molar_density_air",
        "specific_heat_air",
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
        "topofcanopy_radiation",
        "stomatal_conductance",
        "canopy_absorption",
    ),
    vars_populated_by_init=(
        "soil_temperature",
        "vapour_pressure_ref",
        "vapour_pressure_deficit_ref",
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "atmospheric_pressure",
        "atmospheric_co2",
        "canopy_absorption",  # DAVID This is assuming that abiotic runs before plants
        "canopy_temperature",
        "sensible_heat_flux",
        "latent_heat_flux",
        "ground_heat_flux",
        "air_heat_conductivity",
        "leaf_vapour_conductivity",
        "leaf_air_heat_conductivity",
    ),
    vars_populated_by_first_update=(
        "conductivity_from_ref_height",
        "vapour_pressure",
        "wind_speed",
        "friction_velocity",
        "zero_displacement_height",
        "attenuation_coefficient",
        "mean_mixing_length",
        "relative_turbulence_intensity",
        "diabatic_correction_heat_above",
        "diabatic_correction_momentum_above",
        "diabatic_correction_heat_canopy",
        "diabatic_correction_momentum_canopy",
        "sensible_heat_flux_soil",
        "latent_heat_flux_soil",
        "soil_absorption",
        "longwave_emission_soil",
        "molar_density_air",
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
        model_constants: AbioticConsts = AbioticConsts(),
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        self.model_constants = model_constants
        """Set of constants for the abiotic model."""
        self.simple_constants = AbioticSimpleConsts()
        """Set of constants for simple abiotic model."""  # TODO metaconstants

        self._setup()

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

        LOGGER.info(
            "Information required to initialise the abiotic model successfully "
            "extracted."
        )
        return cls(
            data,
            core_components=core_components,
            model_constants=model_constants,
        )

    def _setup(self) -> None:
        """Function to set up the abiotic model.

        This function initializes soil temperature and canopy temperature for all
        corresponding layers and calculates the reference vapour pressure deficit for
        all time steps of the simulation. All variables are added directly to the
        self.data object.
        """

        # create soil temperature array
        self.data["soil_temperature"] = self.layer_structure.from_template()

        # Calculate vapour pressure deficit at reference height for all time steps
        vapour_pressure_and_deficit = microclimate.calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            saturation_vapour_pressure_factors=(
                self.simple_constants.saturation_vapour_pressure_factors
            ),
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
        initial_microclimate = microclimate.run_microclimate(
            data=self.data,
            layer_structure=self.layer_structure,
            time_index=0,
            constants=self.simple_constants,
            bounds=AbioticSimpleBounds(),
        )

        initial_canopy_and_soil = energy_balance.initialise_canopy_and_soil_fluxes(
            air_temperature=initial_microclimate["air_temperature"],
            topofcanopy_radiation=self.data["topofcanopy_radiation"].isel(time_index=0),
            leaf_area_index=self.data["leaf_area_index"],
            layer_heights=self.data["layer_heights"],
            layer_structure=self.layer_structure,
            light_extinction_coefficient=(
                self.model_constants.light_extinction_coefficient
            ),
            canopy_temperature_ini_factor=(
                self.model_constants.canopy_temperature_ini_factor
            ),
        )

        initial_conductivities = conductivities.initialise_conductivities(
            layer_structure=self.layer_structure,
            layer_heights=self.data["layer_heights"],
            initial_air_conductivity=self.model_constants.initial_air_conductivity,
            top_leaf_vapour_conductivity=(
                self.model_constants.top_leaf_vapour_conductivity
            ),
            bottom_leaf_vapour_conductivity=(
                self.model_constants.bottom_leaf_vapour_conductivity
            ),
            top_leaf_air_conductivity=self.model_constants.top_leaf_air_conductivity,
            bottom_leaf_air_conductivity=(
                self.model_constants.bottom_leaf_air_conductivity
            ),
        )

        # Update data object
        for output_dict in (
            initial_microclimate,
            initial_canopy_and_soil,
            initial_conductivities,
        ):
            self.data.add_from_dict(output_dict=output_dict)

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic model.

        The function updates the microclimate in the following order:

        * wind profiles
        * soil energy balance
        * conductivities
        * canopy energy balance for each layer
        * TODO representation of turbulent fluxes is inconsistent
        * TODO add all soil fluxes to atmosphere
        * TODO update soil temperatures

        Args:
            time_index: The index of the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # Wind profiles

        # Reduce input variables to true above ground rows
        # TODO: this type-ignore is because our Data interface doesn't currently accept
        #       list[str] indices, which it should.
        wind_update_inputs = self.data[
            ["layer_heights", "leaf_area_index", "air_temperature"]  # type: ignore [index]
        ].isel(layers=self.layer_structure.index_filled_atmosphere)

        wind_update = wind.calculate_wind_profile(
            canopy_height=self.data["layer_heights"][1].to_numpy(),
            wind_height_above=self.data["layer_heights"][0:2].to_numpy(),
            wind_layer_heights=wind_update_inputs["layer_heights"].to_numpy(),
            leaf_area_index=wind_update_inputs["leaf_area_index"].to_numpy(),
            air_temperature=wind_update_inputs["air_temperature"].to_numpy(),
            atmospheric_pressure=self.data["atmospheric_pressure"][0].to_numpy(),
            sensible_heat_flux_topofcanopy=(
                self.data["sensible_heat_flux"][1].to_numpy()
            ),
            wind_speed_ref=(
                self.data["wind_speed_ref"].isel(time_index=time_index).to_numpy()
            ),
            wind_reference_height=(
                self.data["layer_heights"][1]
                + self.model_constants.wind_reference_height
            ).to_numpy(),
            abiotic_constants=self.model_constants,
            core_constants=self.core_constants,
        )  # TODO wind height above in constants, cross-check with LayerStructure setup

        # Store 2D wind outputs using the full vertical structure
        for var in ["wind_speed", "molar_density_air", "specific_heat_air"]:
            var_out = self.layer_structure.from_template()
            var_out[self.layer_structure.index_filled_atmosphere] = wind_update[var]
            self.data[var] = var_out

        # Store 1D outputs by cell id
        for var in [
            "friction_velocity",
            "diabatic_correction_heat_above",
            "diabatic_correction_momentum_above",
            "diabatic_correction_heat_canopy",
            "diabatic_correction_momentum_canopy",
        ]:
            self.data[var] = DataArray(
                wind_update[var], coords={"cell_id": self.data["cell_id"]}
            )

        # Soil energy balance
        soil_heat_balance = soil_energy_balance.calculate_soil_heat_balance(
            data=self.data,
            time_index=time_index,
            layer_structure=self.layer_structure,
            update_interval=43200,  # TODO self.model_timing.update_interval
            abiotic_consts=self.model_constants,
            core_consts=self.core_constants,
        )

        # Store 1D outputs by cell id
        for var in (
            "soil_absorption",
            "longwave_emission_soil",
            "sensible_heat_flux_soil",
            "latent_heat_flux_soil",
            "ground_heat_flux",
        ):
            self.data[var] = DataArray(
                soil_heat_balance[var], coords={"cell_id": self.data["cell_id"]}
            )

        # Update topsoil temperature
        self.data["soil_temperature"][self.layer_structure.index_topsoil] = (
            soil_heat_balance["new_surface_temperature"]
        )

        # TODO Update lower soil temperatures

        # Update air temperature, leaf temperature, vapour pressure, vapour pressure
        # deficit and turbulent fluxes
        new_microclimate = energy_balance.calculate_leaf_and_air_temperature(
            data=self.data,
            time_index=time_index,
            layer_structure=self.layer_structure,
            abiotic_constants=self.model_constants,
            abiotic_simple_constants=self.simple_constants,
            core_constants=self.core_constants,
        )
        self.data.add_from_dict(output_dict=new_microclimate)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
