r"""The ``models.abiotic.hydrology`` module calculates the hydrology of the Virtual
Rainforest.

The first part of the module determines the water balance within each grid cell as
follows:

:math:`P = I + RO_{above} + RO_{below} + \lambda E + E_{surface} + \Delta Q_{soil}`

where :math:`I` is the intercept loss, :math:`P` is precipitation, :math:`RO_{above}`
and :math:`RO_{below}` are the above- and below-ground runoff, respectively,
:math:`\lambda E` is evapotranspiration from plants, :math:`E_{surface}` is surface
evaporation, and :math:`\Delta Q_{soil}` is the change in soil water content.

The second part of the module calculates the water balance across the full model grid.
This feature is currently not implemented.
"""  # noqa: D205, D415

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.data import Data
from virtual_rainforest.models.abiotic.abiotic_tools import AbioticConstants


@dataclass
class HydrologyConstants:  # TODO find default values and references
    """Hydrology constants dataclass."""

    interception_capacity_default: float = 2.5
    """The amount of water that can sit on a m^2 of leaf area before water drips through
        and water stored on branches and stems, [mm m-2]."""
    canopy_water_extinction_coefficient_default: float = 1
    """Canopy water extinction coefficient (m^2/kg)"""
    precipitation_intensity_factor_default: float = 0
    """Factor that describes average rainfall intensity in the tropics."""
    soil_moisture_capacity_default: float = 150
    """Soil moisture capacity default value, [mm]"""
    vertical_flow_factor_default: float = 0.1
    """Default value to calculate vertical flow as a functon of change in soil moisture.
        """


class Hydrology:
    """Hydrology class.

    This class uses a :class:`~virtual_rainforest.core.data.Data` object to populate
    and store hydrology-related attributes which serve as inputs to other modules.

    Creating an instance of this class expects a `data` object that contains the
    following variables:

    * elevation: elevation above sea level, [m]
    * slope: slope
    * aspect: aspect
    * rainfall: rainfall, [m]
    * leaf area index, [m m-1]
    * latent heat flux from surface, [J m-2]
    * latent heat of vaporisation, [J kg-1]
    * soil moisture from previous time step
    * soil moisture capacity

    The ``hydro_const`` argument takes an instance of class
    :class:`~virtual_rainforest.models.abiotic.hydrology.HydrologyConstants`, which
    provides a user modifiable set of required constants.

    Args:
        data: A Virtual Rainforest Data object.
        hydro_const: A HydrologyConstants instance.
    """

    def __init__(self, data: Data) -> None:
        """Initializes hydrology method."""
        self.data = data  # TODO is this how we access the data object?

        # initialise attributes
        self.interception_loss: DataArray
        """Interception loss, [mm]"""
        self.precipitation_surface: DataArray
        """Precipitation that reaches surface (top of canopy precipitation - intercept
            loss), [mm]"""
        self.soil_moisture_updated: DataArray
        """Soil moisture updated using water balance, """  # TODO what unit here?
        self.surface_runoff: DataArray
        """Surface runoff, [mm] """
        self.vertical_flow: DataArray
        """Vertical flow, [mm] """
        self.subsurface_runoff: DataArray
        """Sub-surface runoff, [mm]"""
        self.surface_water_availability: DataArray
        """Surface water availability, fraction"""
        # TODO add attributes related to lateral flow

        # Calculate digitial elevation model based flow map here?

    # PART 1: GRID_CELL WATER BALANCE (VERTICAL)
    def run_hydrology_cell(
        self,
        interception_capacity: float = HydrologyConstants.interception_capacity_default,
        canopy_water_extinction_coefficient: float = (
            HydrologyConstants.canopy_water_extinction_coefficient_default
        ),
        intercept_method: str = "sum",
        vertical_flow_method: str = "proportional",
    ) -> None:
        """Run cell-based hydrology balance."""

        # calculate interception loss, [mm]
        self.interception_loss = calculate_interception_loss(
            precipitation=self.data["precipitation"],
            leaf_area_index=self.data["leaf_area_index"],
            interception_capacity=interception_capacity,
            extinction_coefficient=canopy_water_extinction_coefficient,
            intercept_method=intercept_method,
        )

        # calculate water that reaches surface, [mm]
        self.precipitation_surface = self.data["precipitation"] - self.interception_loss

        # calculate surface evaporation, [mm]
        # TODO lambda in data object?
        surface_evaporation = (
            self.data["latent_heat_flux_surface"]
            / self.data["latent_heat_vaporisation"]
        )

        # calculate current state of soil moisture
        current_soil_moisture = (
            self.data["soil_moisture"].isel(
                soil_layers=0
            )  # top soil layer, TODO check order is correct
            + self.precipitation_surface
            - self.data["evapotranspiration"].sum(dims="canopy_layers")
            - surface_evaporation
        )

        # check if soil moisture capacity in data, else create and fill with default
        if "soil_moisture_capacity" not in self.data:
            soil_moisture_capacity = DataArray(
                np.repeat(
                    HydrologyConstants.soil_moisture_capacity_default,
                    len(current_soil_moisture),
                ),
                dims="cell_id",
            )

        # calculate runoff and update soil moisture, simple bucket approach
        self.soil_moisture_updated, self.surface_runoff = calculate_surface_runoff(
            precipitation_surface=self.precipitation_surface,
            current_soil_moisture=current_soil_moisture,
            soil_moisture_capacity=soil_moisture_capacity,
        )

        # calculate vertical flow
        self.vertical_flow = calculate_vertical_flow(
            soil_moisture=self.soil_moisture_updated,
            soil_depth=self.data["soil_depth"],
            vertical_flow_method=vertical_flow_method,
        )

        # TODO calculate sub-surface runoff NOT IMPLEMENTED
        self.subsurface_runoff = DataArray(np.zeros(len(current_soil_moisture)))

        # TODO calculate surface water availability NOT IMPLEMENTED
        self.surface_water_availability = DataArray(
            np.zeros(len(current_soil_moisture))
        )

    # TODO PART 2: GRID BASED WATER BALANCE (LATERAL)
    def run_hydrology_grid(self) -> None:
        """Run hydrology balance across grid."""
        raise NotImplementedError("Implementation of this feature is still missing")

        # Balance overland flow
        # Balance sub-surface flow
        # Calculate stream flow


# helper functions for cell-based water balance
def calculate_interception_loss(
    precipitation: DataArray,
    leaf_area_index: DataArray,
    interception_capacity: float = (HydrologyConstants.interception_capacity_default),
    extinction_coefficient: float = (
        HydrologyConstants.canopy_water_extinction_coefficient_default
    ),
    intercept_method: str = "sum",
) -> DataArray:
    r"""Calculates canopy interception using the Rutter interception model.

    The Rutter model assumes that rainfall is intercepted by leaves and branches and
    that intercepted water is subsequently redistributed to other canopy surfaces and
    to the ground. The Rutter model can be expressed as:

    :math:`I = (W_{f} + W_{d}) * (1 - exp(-K * LAI))`

    where :math:`I` is the interception loss, :math:`W_{f}` is the maximum storage
    capacity of the foliage, :math:`W_{d}` is the maximum storage capacity of the
    branches and stems, :math:`K` is the extinction coefficient, which determines the
    amount of intercepted water that is redistributed to other canopy surfaces, and
    :math:`LAI` is the leaf area index, which is a measure of the amount of leaf area
    per unit ground area.

    Args:
        precipitation: precipitation,[mm]
        leaf_area_index: leaf area index, [m m-1]
        interception_capacity: the amount of water that can sit on a
            m\ :sub:`2`\ of leaf area before water drips through and water stored on
            branches and stems, [mm m-2]
        extinction_coefficient: water extinction coefficient, [m2 kg-1]
        intercept_method: calculation method, sum over all layers of stepwise

    Returns:
        interception loss [mm]
    """

    if intercept_method == "stepwise":
        raise (
            NotImplementedError(
                "Stepwise calculation of interception loss is not implemented."
            )
        )
    if intercept_method == "sum":
        # Calculate fraction of rainfall intercepted, sum all canopy layers
        frac_intercepted = 1 - np.exp(
            -extinction_coefficient * leaf_area_index.sum(dims="canopy_layers")
        )

        # Calculate interception loss
        interception_loss = DataArray(
            interception_capacity * frac_intercepted * (precipitation > 0),
            dims="cell_id",
        )

    return interception_loss


def calculate_surface_runoff(
    precipitation_surface: DataArray,
    current_soil_moisture: DataArray,
    soil_moisture_capacity: DataArray,
) -> Tuple[DataArray, DataArray]:
    """Calculate surface runoff and update soil mositure content.

    Args:
        precipitation_surface: precipitation that reaches surface, [mm],
        current_soil_moisture: current soil moisture at upper layer, [mm],
        soil_moisture_capacity: soil moisture capacity

    Returns:
        current soil moisture, [mm], surface runoff, [mm]
    """
    # TODO apply to DataArray with where() or any() !
    if precipitation_surface > soil_moisture_capacity:
        surface_runoff = current_soil_moisture - soil_moisture_capacity
        soil_moisture_updated = soil_moisture_capacity

    elif current_soil_moisture < 0:
        soil_moisture_updated = DataArray(
            np.zeros(len(current_soil_moisture)), dims="cell_id"
        )
        surface_runoff = DataArray(np.zeros(len(current_soil_moisture)), dims="cell_id")
    else:
        surface_runoff = DataArray(np.zeros(len(current_soil_moisture)), dims="cell_id")

    return (soil_moisture_updated, surface_runoff)


def calculate_vertical_flow(
    soil_moisture: DataArray,
    soil_depth: DataArray,
    vertical_flow_method: str = "proportional",
    vertical_flow_factor: float = HydrologyConstants.vertical_flow_factor_default,
) -> DataArray:
    r"""Calculate vertical flow of water though soil.

    The vertical flow can be calculated as a proportion of change in soil moisture or
    with the one-dimensional Richards equation.

    The one-dimensional Richards equation describes the movement of water through a
    porous medium, such as soil under the influence of gravity, capillary forces, and
    hydraulic conductivity:

    ..math:
    \frac {\delta Q_{soil}}{\delta t}
    = \frac {\delta} {\delta z (K(Q_{soil})} \frac {\delta h}{\delta z}

    where :math:`Q_{soil}` is the volumetric water content of the soil, :math:`t` is
    time, :math:`z` is depth, :math:`K(Q_{soil})` is the hydraulic conductivity as a
    function of the water content, and :math:`h` is the hydraulic head. The hydraulic
    head is a measure of the energy of the water in the soil, and is given by:

    :math:`h = z + \Psi (Q_{soil})`

    where :math:`\Psi (Q_{soil})` is the soil water potential as a function of the water
    content.

    Args:
        soil_moisture: soil moisture
        soil_depth: soil depth, [m]
        vertical_flow_method: method to calculate vertical flow, 'proportional' or
            'Richards'
        vertical_flow_factor: factor to calculate propotional flow

    Returns:
        vertical flow per unit time, [mm]
    """

    if vertical_flow_method == "Richards":
        raise (NotImplementedError("Richards equation is not implemented."))

    elif vertical_flow_method == "proportional":
        raise (NotImplementedError("Proportinal vertical flow is not implemented."))

    elif vertical_flow_method != ["Richards", "proportional"]:
        vertical_flow = DataArray(np.zeros(len(soil_moisture)))

    return vertical_flow


def calculate_soil_water_potential(
    density_water_vapor: DataArray,
    soil_node_depths: DataArray,
    density_water: float = AbioticConstants.density_water,
    gravity: float = AbioticConstants.gravity,
) -> DataArray:
    r"""Calculate soil water potential as a function of soil water content.

    Soil water potential :math:`\Psi` is calculated as follows:

    :math:`\Psi = - (\rho g h + 0.5 \rho v^{2})`

    where :math:`\rho` is the density of water, :math:`g` is the acceleration due to
    gravity, :math:`h` is the height of the water column above the point of measurement
    and :math:`\rho v` is the density of the water vapor.

    Args:
        density_water_vapor: density of the water vapor (kg m-3)
        soil_node_depths: soil node depths which represent heights of water colum above
            the point of calculation, [m]
        density_water: density of water (1000 kg m-3)
        gravity: acceleration due to gravity (9.81 m s-2)

    Returns:
        soil water potential
    """
    raise (NotImplementedError)


def calculate_hydraulic_conductivity(
    soil_moisture: DataArray,
    saturated_hydraulic_conductivity: DataArray,
    soil_porosity: DataArray,
    pore_size_distribution_index: DataArray,  # TODO reference
) -> DataArray:
    """Calculate hydraulic conductivity as a function of soil mositure.

    Args:
        soil_moisture: soil moisture
        saturated_hydraulic_conductivity: saturated hydraulic conductivity, [m/s]
        soil_porosity: soil porosity
        pore_size_distribution_index: pore size distribution index

    Returns:
        soil hydraulic conductivity
    """
    return (
        saturated_hydraulic_conductivity
        * (soil_moisture / soil_porosity) ** (1 / 2)
        * (
            1
            - (
                1
                - (soil_moisture / soil_porosity) ** (1 / pore_size_distribution_index)
            )
            ** pore_size_distribution_index
        )
        ** 2
    )


# THIS IS THE GRD BASED SECTION - NOT IMPLEMENTED
# grid based water balance
def map_hydrology(args: None, kwargs: None) -> None:
    """Creates flow direction/catchment map based on digital elevation model.

    Args:
        elevation: elevation, [m]
        slope: slope
        aspect: aspect

    Returns:
        topographic index
        flow direction map
        catchment map
    """
    raise NotImplementedError("Implementation of this feature is still missing.")


def run_water_balance_grid(args: None, kwargs: None) -> None:
    """Integrates water balance on grid level.

    Args:
        args: list of arguments, to be decided

    Returns:
        total overland flow [mm area-1]
        total subsurface flow [mm area-1]
        stream flow [mm area-1]
    """
    raise NotImplementedError("The grid-based water balance is not implemented.")
