"""The :mod:`~virtual_rainforest.models.hydrology.hydrology_model` module
creates a
:class:`~virtual_rainforest.models.hydrology.hydrology_model.HydrologyModel`
class as a child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.hydrology.hydrology_model.HydrologyModel.from_config`
exists in a more complete state, and unpacks a small number of parameters from our
currently pretty minimal configuration dictionary. These parameters are then used to
generate a class instance. If errors crop here when converting the information from the
config dictionary to the required types they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled by
downstream functions so that all model configuration failures can be reported as one.
"""  # noqa: D205, D415

from __future__ import annotations

from math import sqrt
from typing import Any, Union

import numpy as np
import xarray as xr
from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import check_valid_constant_names, set_layer_roles
from virtual_rainforest.models.hydrology.constants import HydroConsts


class HydrologyModel(BaseModel):
    """A class describing the hydrology model.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
        initial_soil_moisture: The initial volumetric relative water content [unitless]
            for all layers.
        constants: Set of constants for the hydrology model.

    Raises:
        InitialisationError: when initial soil moisture is out of bounds.
    """

    model_name = "hydrology"
    """The model name for use in registering the model and logging."""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that hydrology model can sensibly capture."""
    upper_bound_on_time_scale = "1 month"
    """Longest time scale that hydrology model can sensibly capture."""
    required_init_vars = (
        ("precipitation", ("spatial",)),
        ("leaf_area_index", ("spatial",)),
        ("air_temperature_ref", ("spatial",)),
        ("relative_humidity_ref", ("spatial",)),
        ("atmospheric_pressure_ref", ("spatial",)),
        ("evapotranspiration", ("spatial",)),
        ("elevation", ("spatial",)),
        ("surface_runoff", ("spatial",)),
        # TODO this requires the plant model to run before the hydrology; this works as
        # long as the p-model does not require soil moisture as an input. If it does, we
        # have to discuss where we move the calculation of stream flow.
    )
    # TODO add time dimension
    """The required variables and axes for the hydrology model"""
    vars_updated = [
        "soil_moisture",
        "surface_runoff",  # equivalent to SPLASH runoff
        "vertical_flow",
        "soil_evaporation",
        "stream_flow",  # P-ET; TODO later surface_runoff_acc + below_ground_acc
        "surface_runoff_accumulated",
    ]
    """Variables updated by the hydrology model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: int,
        canopy_layers: int,
        initial_soil_moisture: float,
        constants: HydroConsts,
        **kwargs: Any,
    ):
        # Sanity checks for initial soil moisture
        if type(initial_soil_moisture) is not float:
            to_raise = InitialisationError("The initial soil moisture must be a float!")
            LOGGER.error(to_raise)
            raise to_raise

        if initial_soil_moisture < 0 or initial_soil_moisture > 1:
            to_raise = InitialisationError(
                "The initial soil moisture has to be between 0 and 1!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        super().__init__(data, update_interval, **kwargs)

        # Create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.layer_roles = layer_roles
        """A list of vertical layer roles."""
        self.update_interval
        """The time interval between model updates."""
        self.initial_soil_moisture = initial_soil_moisture
        """Initial volumetric relative water content [unitless] for all layers and grid
        cells identical."""
        self.constants = constants
        """Set of constants for the hydrology model"""
        self.data.grid.set_neighbours(distance=sqrt(self.data.grid.cell_area))
        """Set neighbours."""

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> HydrologyModel:
        """Factory function to initialise the hydrology model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.
            update_interval: Frequency with which all models are updated.
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]
        initial_soil_moisture = config["hydrology"]["initial_soil_moisture"]

        # Check if any constants have been supplied
        if "hydrology" in config and "constants" in config["hydrology"]:
            # Checks that constants is config are as expected
            check_valid_constant_names(config, "hydrology", "HydroConsts")
            # If an error isn't raised then generate the dataclass
            constants = HydroConsts(**config["hydrology"]["constants"]["HydroConsts"])
        else:
            # If no constants are supplied then the defaults should be used
            constants = HydroConsts()

        LOGGER.info(
            "Information required to initialise the hydrology model successfully "
            "extracted."
        )
        return cls(
            data,
            update_interval,
            soil_layers,
            canopy_layers,
            initial_soil_moisture,
            constants,
        )

    def setup(self) -> None:
        """Function to set up the hydrology model.

        At the moment, this function initializes variables that are required to run the
        first update(). For the within grid cell hydrology, soil moisture is initialised
        homogenously for all soil layers, which are treated as one single bucket in this
        simple approach. This design might change with the implementation of the SPLASH
        model in the plant module which will take care of the above-ground hydrology.
        Air temperature and relative humidity below the canopy are set to the 2m
        reference values.

        For the hydrology across the grid (above-/below-ground and total runoff), this
        function identifies the upstream neighbours of each grid cell based on a digital
        elevation model.

        TODO implement below-ground horizontal flow and update stream flow
        """

        # Create 1-dimensional numpy array filled with initial soil moisture values for
        # all soil layers and np.nan for atmosphere layers
        soil_moisture_values = np.repeat(
            a=[np.nan, self.initial_soil_moisture],
            repeats=[
                len(self.layer_roles) - self.layer_roles.count("soil"),
                self.layer_roles.count("soil"),
            ],
        )
        # Broadcast 1-dimensional array to grid and assign dimensions and coordinates
        self.data["soil_moisture"] = DataArray(
            np.broadcast_to(
                soil_moisture_values,
                (len(self.data.grid.cell_id), len(self.layer_roles)),
            ).T,
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(len(self.layer_roles)),
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": self.data.grid.cell_id,
            },
            name="soil_moisture",
        )

        # Create initial air temperature with reference temperature below the canopy
        # for first soil evaporation update.
        self.data["air_temperature"] = (
            DataArray(self.data["air_temperature_ref"].isel(time_index=0))
            .expand_dims("layers")
            .rename("air_temperature")
            .assign_coords(
                coords={
                    "layers": [self.layer_roles.index("subcanopy")],
                    "layer_roles": ("layers", ["subcanopy"]),
                    "cell_id": self.data.grid.cell_id,
                },
            )
        )

        # Create initial relative humidity with reference humidity below the canopy
        # for first soil evaporation update.
        self.data["relative_humidity"] = (
            DataArray(self.data["relative_humidity_ref"].isel(time_index=0))
            .expand_dims("layers")
            .rename("relative_humidity")
            .assign_coords(
                coords={
                    "layers": [self.layer_roles.index("subcanopy")],
                    "layer_roles": ("layers", ["subcanopy"]),
                    "cell_id": self.data.grid.cell_id,
                },
            )
        )

        # Identify cell ID of the lowest neighbour for each grid cell
        lowest_neighbour = find_lowest_neighbour(
            neighbours=self.data.grid.neighbours,
            elevation=np.array(self.data["elevation"]),
        )

        # Identify all upstream cell IDs
        self.upstream_ids = find_upstream_cells(lowest_neighbour)
        """Upstream IDs for the calculation of accumulated runoff."""

        # Get the runoff created by SPLASH or initial data set as the initial state:
        initial_runoff = np.array(self.data["surface_runoff"])

        # Set initial accumulated runoff to zero
        accumulated_runoff = np.zeros_like(self.data["elevation"])

        # Calculate accumulated (surface) runoff for each cell
        new_accumulated_runoff = accumulate_surface_runoff(
            upstream_ids=self.upstream_ids,
            surface_runoff=initial_runoff,
            accumulated_runoff=accumulated_runoff,
        )

        self.data["surface_runoff_accumulated"] = DataArray(
            new_accumulated_runoff,
            dims="cell_id",
            name="surface_runoff_accumulated",
            coords={"cell_id": self.data.grid.cell_id},
        )

    def spinup(self) -> None:
        """Placeholder function to spin up the hydrology model."""
        # TODO soil moisture and accumulated runoff need a spin up

    def update(self, time_index: int) -> None:
        r"""Function to update the hydrology model.

        At the moment, this step calculates soil moisture, vertical flow, soil
        evaporation, and surface runoff (per grid cell and accumulated), and estimates
        mean stream flow. Soil moisture and surface runoff are calculated
        with a simple bucket model based on :cite:t:`davis_simple_2017`: if
        precipitation exceeds soil moisture capacity, the excess water is added to
        runoff and soil moisture is set to soil moisture capacity value; if the soil is
        not saturated, precipitation is added to the current soil moisture level and
        runoff is set to zero. All soil layers are combined into one bucket. Note that
        this function will likely change with the implementation of the SPLASH model
        :cite:p:`davis_simple_2017` in the plant module which will take care of the
        grid cell based above-ground hydrology. The accumulated surface runoff is
        calculated as the sum off current runoff and the runoff from upstream cells at
        the previous time step.

        Soil evaporation is calculated with classical bulk aerodynamic formulation,
        following the so-called ':math:`\alpha` method', see
        :func:`~virtual_rainforest.models.hydrology.hydrology_model.calculate_soil_evaporation`
        .

        Vertical flow is calculated using the Richards equation, see
        :func:`~virtual_rainforest.models.hydrology.hydrology_model.calculate_vertical_flow`
        . Note that there are severe limitations to this approach on the temporal and
        spatial scale of this model and this can only be treated as a very rough
        approximation! Further, we do not remove the water from the soil but assume a
        steady state.

        Mean stream flow :math:`Q` is estimated as

        :math:`Q = P - ET - \Delta S`

        where :math:`P` is mean precipitation, :math:`ET` is evapotranspiration, and
        :math:`\Delta S` is the change in soil moisture. Note that this has to be called
        after evapotranspiration is calculated by the plant model which works as long as
        the P-model does not require moisture as an input. In the future, this
        might move to a different model or the order of models might change.

        The function requires the following input variables from the data object:

        * air temperature, [C]
        * relative humidity, []
        * atmospheric pressure, [kPa]
        * precipitation, [mm]
        * wind speed (currently not implemented, default = 0.1 m s-1)
        * leaf area index, [m m-2]
        * layer heights, [m]
        * Volumetric relative water content (previous time step), [unitless]
        * evapotranspiration (current time step), [mm]
        * accumulated surface runoff (previous time step), [mm]

        and the following soil parameters (defaults in
        :class:`~virtual_rainforest.models.hydrology.constants.HydroConsts`):

        * soil moisture capacity, [unitless]
        * soil moisture residual, [unitless]
        * soil hydraulic conductivity, [m s-1]
        * soil hydraulic gradient, [m m-1]
        * van Genuchten non-linearity parameter, dimensionless

        and a number of additional parameters that as described in detail in
        :class:`~virtual_rainforest.models.hydrology.constants.HydroConsts`.

        """
        # select time conversion factor # TODO implement flexible time steps
        if self.update_interval != Quantity("1 month"):
            to_raise = NotImplementedError("This time step is currently not supported.")
            LOGGER.error(to_raise)
            raise to_raise

        time_conversion_factor = self.constants.seconds_to_month

        # Select variables at relevant heights for current time step
        current_precipitation = self.data["precipitation"].isel(time_index=time_index)
        leaf_area_index_sum = self.data["leaf_area_index"].sum(dim="layers")
        subcanopy_temperature = (
            self.data["air_temperature"]
            .isel(layers=self.layer_roles.index("subcanopy"))
            .drop_vars(["layer_roles", "layers"])
        )
        subcanopy_humidity = (
            self.data["relative_humidity"]
            .isel(layers=self.layer_roles.index("subcanopy"))
            .drop_vars(["layer_roles", "layers"])
        )
        subcanopy_pressure = (self.data["atmospheric_pressure_ref"]).isel(
            time_index=time_index
        )

        # Calculate soil depth in mm
        soil_depth = self.data["layer_heights"].isel(layers=-1).drop_vars(
            ["layers"]
        ) * (-self.constants.meters_to_millimeters)

        # Interception: precipitation at the surface is reduced as a function of leaf
        # area index
        # TODO the interception reservoir should be treated as a bucket that fills up
        # before water falls through, and from which water evaporates back into the
        # atmosphere. However, this is strongly affected by the intensity of rainfall
        # and therefore currently not implemented. Instead we assume that a fraction of
        # rainfall is intercepted and evaporated over the course of one time step
        precipitation_surface = current_precipitation * (
            1 - self.constants.water_interception_factor * leaf_area_index_sum
        )

        # Calculate total soil moisture (before rainfall) in mm
        # To find out how much rain can be taken up by the soil before rain goes to
        # runoff, the volumetric relative water content (between 0 and 1) is converted
        # to mm with this equation:
        # water content in mm = relative water content / 100 * depth in mm
        # Example: for 20% water at 40 cm this would be: 20/100 * 400mm = 80 mm
        # TODO We treat the soil as one bucket, in the future, there should be a
        # flow between layers and a gradient of soil moisture and soil water potential
        total_soil_moisture_mm = (
            self.data["soil_moisture"].isel(layers=-1)
            * (-self.constants.meters_to_millimeters)
            * self.data["layer_heights"].isel(layers=-1)
        ).drop_vars(["layers", "layer_roles"])

        # Calculate how much water can be added to soil before capacity is reached.
        available_capacity_mm = (
            self.constants.soil_moisture_capacity * soil_depth - total_soil_moisture_mm
        )

        # Find grid cells where precipitation exceeds available capacity
        surface_runoff_cells = precipitation_surface.where(
            precipitation_surface > available_capacity_mm
        )

        # create output dict as intermediate step to not overwrite data directly
        soil_hydrology = {}

        # Calculate runoff of each grid cell in mm; might get replaced by SPLASH model
        soil_hydrology["surface_runoff"] = (
            DataArray(surface_runoff_cells.data - available_capacity_mm.data)
            .fillna(0)
            .rename("surface_runoff")
            .rename({"dim_0": "cell_id"})
            .assign_coords({"cell_id": self.data["soil_moisture"].cell_id})
        )

        # Calculate total water in mm in each grid cell
        total_water_mm = total_soil_moisture_mm + precipitation_surface

        # Calculate volumetric relative soil moisture after infiltration and cap to
        # soil moisture capacity
        soil_moisture_infiltrated = DataArray(
            np.clip(
                total_water_mm / soil_depth, 0, self.constants.soil_moisture_capacity
            )
        )

        # Calculate soil (surface) evaporation
        soil_hydrology["soil_evaporation"] = calculate_soil_evaporation(
            temperature=subcanopy_temperature,
            relative_humidity=subcanopy_humidity,
            atmospheric_pressure=subcanopy_pressure,
            soil_moisture=soil_moisture_infiltrated,
            wind_speed=0.1,  # TODO wind_speed in data object, m/s
            celsius_to_kelvin=self.constants.celsius_to_kelvin,
            density_air=self.constants.density_air,
            latent_heat_vapourisation=self.constants.latent_heat_vapourisation,
            gas_constant_water_vapour=self.constants.gas_constant_water_vapour,
            heat_transfer_coefficient=self.constants.heat_transfer_coefficient,
            flux_to_mm_conversion=self.constants.flux_to_mm_conversion,
            timestep_conversion_factor=time_conversion_factor,
        )

        # Calculate soil moisture after evaporation
        soil_moisture_evap = (
            soil_moisture_infiltrated - soil_hydrology["soil_evaporation"] / soil_depth
        )

        # Calculate vertical flow in mm per time step for mean soil moisture
        # Note that there are severe limitations to this approach on the temporal and
        # spatial scale of this model and this can only be treated as a very rough
        # approximation to discuss nutrient leaching.
        # Further, we do not remove the water from the soil but assume a steady state
        soil_hydrology["vertical_flow"] = calculate_vertical_flow(
            soil_moisture=soil_moisture_evap,
            soil_depth=soil_depth,
            soil_moisture_capacity=self.constants.soil_moisture_capacity,
            soil_moisture_residual=self.constants.soil_moisture_residual,
            hydraulic_conductivity=self.constants.hydraulic_conductivity,
            hydraulic_gradient=self.constants.hydraulic_gradient,
            timestep_conversion_factor=self.constants.seconds_to_month,
            nonlinearily_parameter=self.constants.nonlinearily_parameter,
            meters_to_millimeters=self.constants.meters_to_millimeters,
        )

        # Expand soil moisture to all soil layers and add atmospheric layers (nan)
        soil_hydrology["soil_moisture"] = xr.concat(
            [
                DataArray(
                    np.full(
                        (
                            len(self.layer_roles) - self.layer_roles.count("soil"),
                            len(self.data["layer_heights"].cell_id),
                        ),
                        np.nan,
                    ),
                    dims=["layers", "cell_id"],
                ),
                soil_moisture_evap.expand_dims(
                    dim={"layers": self.layer_roles.count("soil")},
                ),
            ],
            dim="layers",
        ).assign_coords(
            coords={
                "layers": np.arange(len(self.layer_roles)),
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": self.data["layer_heights"].cell_id,
            }
        )

        # Calculate accumulated surface runoff
        # Get the runoff created by SPLASH or initial data set
        single_cell_runoff = np.array(soil_hydrology["surface_runoff"])

        # Get accumulated runoff from previous time step
        accumulated_runoff = np.array(self.data["surface_runoff_accumulated"])

        # Calculate accumulated runoff for each cell (me + sum of upstream neighbours)
        new_accumulated_runoff = accumulate_surface_runoff(
            upstream_ids=self.upstream_ids,
            surface_runoff=single_cell_runoff,
            accumulated_runoff=accumulated_runoff,
        )

        soil_hydrology["surface_runoff_accumulated"] = DataArray(
            new_accumulated_runoff, dims="cell_id"
        )

        # Calculate stream flow as Q= P-ET-dS ; vertical flow is not considered
        # The maximum stream flow capacity is set to an arbitray value, could be used to
        # flag flood events
        stream_flow = DataArray(
            np.clip(
                (
                    precipitation_surface
                    - self.data["evapotranspiration"].sum(dim="layers")
                    - (
                        self.data["soil_moisture"].mean(dim="layers")
                        - soil_moisture_evap
                    ),
                ),
                0,
                HydroConsts.stream_flow_capacity,
            ),
        )
        soil_hydrology["stream_flow"] = stream_flow.rename(
            {"dim_1": "cell_id"}
        ).squeeze("dim_0")

        # Update data object
        self.data.add_from_dict(output_dict=soil_hydrology)

    def cleanup(self) -> None:
        """Placeholder function for hydrology model cleanup."""


def calculate_vertical_flow(
    soil_moisture: DataArray,
    soil_depth: DataArray,
    soil_moisture_capacity: Union[float, DataArray],
    soil_moisture_residual: Union[float, DataArray],
    hydraulic_conductivity: Union[float, DataArray],
    hydraulic_gradient: Union[float, DataArray],
    timestep_conversion_factor: float,
    nonlinearily_parameter: Union[float, DataArray],
    meters_to_millimeters: float,
) -> DataArray:
    r"""Calculate vertical water flow through soil column.

    To calculate the flow of water through unsaturated soil, this function uses the
    Richards equation. First, the function calculates the effective saturation :math:`S`
    and effective hydraulic conductivity :math:`K(S)` based on the moisture content
    :math:`\Theta` using the van Genuchten/Mualem model:

    :math:`S = \frac{\Theta - \Theta_{r}}{\Theta_{s} - \Theta_{r}}`

    and

    :math:`K(S) = K_{s}*(S*(1-S^{1/m})^{m})^{2}`

    where :math:`\Theta_{r}` is the residual moisture content, :math:`\Theta_{s}` is the
    saturated moisture content, :math:`K_{s}` is the saturated hydraulic conductivity,
    and :math:`m=1-1/n` is a shape parameter derived from the non-linearity parameter
    :math:`n`. Then, the function applies Darcy's law to calculate the water flow rate
    :math:`q` in :math:`\frac{m^3}{s^1}` considering the effective hydraulic
    conductivity:

    :math:`q = K(S)*A*\frac{dh}{dl}`

    where :math:`A` is the column cross section area (which will be dropped in the
    conversion to mm) :math:`\frac{dh}{dl}` is the hydraulic gradient with :math:`l` the
    length of the flow path in meters (here equal to the soil depth). We assume the
    whole soil column as one layer and the soil moisture to be the mean soil moisture.

    Note that there are severe limitations to this approach on the temporal and
    spatial scale of this model and this can only be treated as a very rough
    approximation! Further, we do not remove the water from the soil but assume a
    steady state. To consider the latter, this function should be replaced with a more
    sophisticaed, multi-layer model or a simple residence time assumption.

    Args:
        soil_moisture: (mean) Volumetric relative water content in top soil, [unitless]
        soil_depths: soil depths = length of the flow path, [m]
        soil_moisture_capacity: soil moisture capacity, [unitless]
        soil_moisture_residual: residual soil moisture, [unitless]
        hydraulic_conductivity: hydraulic conductivity of soil, [m/s]
        hydraulic_gradient: hydraulic gradient (change in hydraulic head) along the flow
            path, positive values indicate downward flow, [m/m]
        timestep_conversion_factor: factor to convert flow from m^3 per second to mm per
            model time step
        nonlinearily_parameter: dimensionless parameter in van Genuchten model that
            describes the degree of nonlinearity of the relationship between the
            volumetric water content and the soil matric potential.

    Returns:
        volumetric flow rate of water, [mm/timestep]
    """
    m = 1 - 1 / nonlinearily_parameter

    # Calculate soil effective saturation after van Genuchten (1980)
    effective_saturation = (soil_moisture - soil_moisture_residual) / (
        soil_moisture_capacity - soil_moisture_residual
    )

    # Calculate the effective hydraulic conductivity after Mualem (1976)
    effective_conductivity = (
        hydraulic_conductivity
        * effective_saturation
        * (1 - (1 - (effective_saturation) ** (1 / m)) ** m) ** 2
    )

    # Calculate the water flow rate after Darcy (1856) in m^3 per seconds and convert to
    # mm per timestep
    return (
        effective_conductivity
        * hydraulic_gradient
        / soil_depth
        * meters_to_millimeters
        * timestep_conversion_factor
    )


def calculate_soil_evaporation(
    temperature: DataArray,
    relative_humidity: DataArray,
    atmospheric_pressure: DataArray,
    soil_moisture: DataArray,
    wind_speed: Union[float, DataArray],
    celsius_to_kelvin: float,
    density_air: Union[float, DataArray],
    latent_heat_vapourisation: Union[float, DataArray],
    gas_constant_water_vapour: float,
    heat_transfer_coefficient: float,
    flux_to_mm_conversion: float,
    timestep_conversion_factor: float,
) -> DataArray:
    """Calculate soil evaporation based classical bulk aerodynamic formulation.

    TODO write description and add references
    TODO move constants to HydroConsts or CoreConstants and check values

    Args:
        temperature: air temperature at reference height, [C]
        relative_humidity: relative humidity at reference height, []
        atmospheric_pressure: atmospheric pressure at reference height, [kPa]
        soil_moisture: Volumetric relative water content [unitless]
        wind_speed: wind speed at reference height, [m s-1]
        celsius_to_kelvin: factor to convert teperature from Celsius to Kelvin
        density_air: density if air, [kg m-3]
        latent_heat_vapourisation: latent heat of vapourisation, [J kg-1]
        gas_constant_water_vapour: gas constant for water vapour, [J kg-1 K-1]
        heat_transfer_coefficient: heat transfer coefficient of air
        flux_to_mm_conversion: flux to mm conversion factor

    Returns:
        soil evaporation, [mm]
    """

    # Convert temperature to Kelvin
    temperature_k = temperature + celsius_to_kelvin

    # Estimate alpha using the Barton (1979) equation
    barton_ratio = (1.8 * soil_moisture) / (soil_moisture + 0.3)
    alpha = np.where(barton_ratio > 1, 1, barton_ratio)

    saturation_vapour_pressure = DataArray(
        0.6112 * np.exp((17.67 * (temperature_k)) / (temperature_k + 243.5))
    )

    saturated_specific_humidity = DataArray(
        (gas_constant_water_vapour / latent_heat_vapourisation)
        * (
            saturation_vapour_pressure
            / (atmospheric_pressure - saturation_vapour_pressure)
        ),
        dims=temperature.dims,
    )

    specific_humidity_air = DataArray(
        (relative_humidity * saturated_specific_humidity) / 100,
        dims=relative_humidity.dims,
        name="specific_humidity",
    )

    aerodynamic_resistance = heat_transfer_coefficient / np.sqrt(wind_speed)

    evaporative_flux = (density_air / aerodynamic_resistance) * (
        alpha * saturation_vapour_pressure - specific_humidity_air
    )

    return DataArray(  # TODO check this
        (evaporative_flux / flux_to_mm_conversion) / timestep_conversion_factor
    )


def find_lowest_neighbour(neighbours: list, elevation: np.ndarray) -> list:
    """Find lowest neighbour for each grid cell from elevation data.

    This function finds the cell IDs of the lowest neighbour for each grid cell. This
    can be used to determine in which direction surface runoff flows.

    Args:
        neighbours: list of neighbours
        elevation: elevation, [m]

    Returns:
        list of lowest neighbour IDs
    """
    lowest_neighbour = []
    for cell_id, neighbors_id in enumerate(neighbours):
        downstream_id_loc = np.argmax(elevation[cell_id] - elevation[neighbors_id])
        lowest_neighbour.append(neighbors_id[downstream_id_loc])

    return lowest_neighbour


def find_upstream_cells(lowest_neighbour: list) -> list:
    """Find all upstream cell IDs for all grid cells.

    This function identified all cell IDs that are upstream of each grid cell. This can
    be used to calculate the water flow that goes though a grid cell.

    Args:
        lowest_neighbour: list of lowest neighbour cell_ids

    Returns:
        list of all upstream IDs for each grid cell
    """
    upstream_ids: list = [[] for i in range(len(lowest_neighbour))]

    for down_s, up_s in enumerate(lowest_neighbour):
        upstream_ids[up_s].append(down_s)

    return upstream_ids


def accumulate_surface_runoff(
    upstream_ids: list,
    surface_runoff: np.ndarray,
    accumulated_runoff: np.ndarray,
) -> np.ndarray:
    """Calculate accumulated surface runoff for each grid cell.

    This function takes the accumulated surface runoff from the previous timestep and
    adds all surface runoff of the current time step from upstream cell IDs.

    The function currently raises a `ValueError` if accumulated runoff is negative.

    Args:
        upstream_ids: list of all upstream IDs for each grid cell
        surface_runoff: surface runoff of the current time step, [mm]
        accumulated_runoff: accumulated surface runoff from previous time step, [mm]

    Returns:
        accumulated surface runoff, [mm]
    """

    for cell_id, upstream_id in enumerate(upstream_ids):
        accumulated_runoff[cell_id] += np.sum(surface_runoff[upstream_id])

    for num in accumulated_runoff:
        if num < 0:
            to_raise = ValueError(
                "The accumulated surface runoff should not be negative!"
            )
            LOGGER.error(to_raise)
            raise to_raise

    return accumulated_runoff
