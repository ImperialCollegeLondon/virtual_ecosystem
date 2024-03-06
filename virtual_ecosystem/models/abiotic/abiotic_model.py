"""The :mod:`~virtual_ecosystem.models.abiotic.abiotic_model` module creates a
:class:`~virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class. At
present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_ecosystem.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Ecosystem
model develops. The factory method
:func:`~virtual_ecosystem.models.abiotic.abiotic_model.AbioticModel.from_config`
exists in a more complete state, and unpacks a small number of parameters from our
currently pretty minimal configuration dictionary. These parameters are then used to
generate a class instance. If errors crop here when converting the information from the
config dictionary to the required types they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled by
downstream functions so that all model configuration failures can be reported as one.

TODO There are currently a number of unresolved/not implemented processes which require
further advancement in other models of the Virtual Ecosystem or potentially some changes
to the vertical layer structure:

* add process based calculation of soil temperature
* change temperatures to Kelvin
* adjust for soil moisture default in mm (once updated in hydrology model)
* coordinate latent heat flux/evapotranspiration processes between plants and abiotic
* add soil fluxes to lower atmosphere (might need to drop 'subcanopy' layer)
* return updated fluxes to data object
* introducte 'metaconstants' to support sharing of constants between models
* add self.model_timing.update_interval in seconds as input to soil balance
* expand tests to cover different atmospheric conditions

"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

import numpy as np
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
from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts


class AbioticModel(
    BaseModel,
    model_name="abiotic",
    model_update_bounds=("1 hour", "1 month"),
    required_init_vars=(
        ("air_temperature_ref", ("spatial",)),
        ("relative_humidity_ref", ("spatial",)),
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
        self.core_constants = core_components.core_constants
        """Set of universal constants that are used across all models."""

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

    def setup(self) -> None:
        """Function to set up the abiotic model.

        This function initializes soil temperature and canopy temperature for all
        corresponding layers and calculates the reference vapour pressure deficit for
        all time steps of the simulation. All variables are added directly to the
        self.data object.
        """

        # Calculate vapour pressure deficit at reference height for all time steps
        vapour_pressure_and_deficit = microclimate.calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            constants=AbioticSimpleConsts(),  # TODO sort out when constants revised
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
            layer_roles=self.layer_structure.layer_roles,
            time_index=0,
            constants=AbioticSimpleConsts(),  # TODO sort out when constants revised
            Bounds=microclimate.Bounds,
        )

        initial_canopy_and_soil = energy_balance.initialise_canopy_and_soil_fluxes(
            air_temperature=initial_microclimate["air_temperature"],
            topofcanopy_radiation=self.data["topofcanopy_radiation"].isel(time_index=0),
            leaf_area_index=self.data["leaf_area_index"],
            layer_heights=self.data["layer_heights"],
            light_extinction_coefficient=(
                self.model_constants.light_extinction_coefficient
            ),
            canopy_temperature_ini_factor=(
                self.model_constants.canopy_temperature_ini_factor
            ),
        )

        initial_conductivities = conductivities.initialise_conductivities(
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
        self.data.add_from_dict(output_dict=initial_microclimate)
        self.data.add_from_dict(output_dict=initial_canopy_and_soil)
        self.data.add_from_dict(output_dict=initial_conductivities)

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic model.

        The function updates the microclimate in the following order:

        * wind profiles
        * soil energy balance
        * conductivities
        * canopy energy balance for each layer
        * TODO add all soil fluxes to atmosphere
        * TODO update soil temperatures

        Args:
            time_index: The index of the current time step in the data object.
        """

        # Wind profiles
        wind_update_inputs: dict[str, DataArray] = {}

        for var in ["layer_heights", "leaf_area_index", "air_temperature"]:
            selection = (
                self.data[var]
                .where(self.data[var].layer_roles != "soil")
                .dropna(dim="layers")
            )
            wind_update_inputs[var] = selection

        wind_update = wind.calculate_wind_profile(
            canopy_height=self.data["canopy_height"].to_numpy(),
            wind_height_above=(self.data["canopy_height"] + 15).to_numpy(),
            wind_layer_heights=wind_update_inputs["layer_heights"].to_numpy(),
            leaf_area_index=wind_update_inputs["leaf_area_index"].to_numpy(),
            air_temperature=wind_update_inputs["air_temperature"].to_numpy(),
            atmospheric_pressure=self.data["atmospheric_pressure"].to_numpy()[0],
            sensible_heat_flux_topofcanopy=(
                self.data["sensible_heat_flux_topofcanopy"].to_numpy()
            ),
            wind_speed_ref=(
                self.data["wind_speed_ref"].isel(time_index=time_index).to_numpy()
            ),
            wind_reference_height=(self.data["canopy_height"] + 10).to_numpy(),
            abiotic_constants=self.model_constants,
            core_constants=self.core_constants,
        )  # TODO wind height above in constants, cross-check with reference heights

        wind_output = {}
        wind_speed_above_canopy = DataArray(
            wind_update["wind_speed_above_canopy"],
            dims="cell_id",
            coords={"cell_id": self.data.grid.cell_id},
        )
        wind_output["wind_speed_above_canopy"] = wind_speed_above_canopy

        for var in ["wind_speed_canopy", "friction_velocity"]:
            var_out = DataArray(
                np.concatenate(
                    (
                        wind_update[var],
                        np.full(
                            (
                                len(self.layer_structure.layer_roles)
                                - len(wind_update[var]),
                                self.data.grid.n_cells,
                            ),
                            np.nan,
                        ),
                    ),
                ),
                dims=self.data["layer_heights"].dims,
                coords=self.data["layer_heights"].coords,
            )
            wind_output[var] = var_out

        self.data.add_from_dict(output_dict=wind_output)

        # Soil energy balance
        topsoil_layer_index = self.layer_structure.layer_roles.index("soil")

        soil_heat_balance = soil_energy_balance.calculate_soil_heat_balance(
            data=self.data,
            topsoil_layer_index=topsoil_layer_index,
            update_interval=43200,  # TODO self.model_timing.update_interval
            abiotic_consts=self.model_constants,
            core_consts=self.core_constants,
        )

        soil_output = {}  # TODO add these variables to combined flux variables
        var_list = [
            "soil_absorption",
            "longwave_emission_soil",
            "sensible_heat_flux_soil",
            "latent_heat_flux_soil",
            "ground_heat_flux",
        ]
        for var in var_list:
            soil_output[var] = DataArray(
                soil_heat_balance[var],
                dims="cell_id",
                coords={"cell_id": self.data.grid.cell_id},
            )
        self.data["soil_temperature"][topsoil_layer_index] = soil_heat_balance[
            "new_surface_temperature"
        ]
        self.data.add_from_dict(output_dict=soil_output)

        # TODO Update soil temperatures

        # Update air temperature, leaf temperature and vapour pressure deficit
        # TODO return sensible and latent heat flux
        new_microclimate = energy_balance.calculate_leaf_and_air_temperature(
            data=self.data,
            time_index=time_index,
            topsoil_layer_index=self.layer_structure.layer_roles.index("soil"),
            abiotic_constants=self.model_constants,
            abiotic_simple_constants=AbioticSimpleConsts(),
            core_constants=self.core_constants,
        )
        self.data.add_from_dict(output_dict=new_microclimate)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
