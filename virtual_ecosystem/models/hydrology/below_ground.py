"""The ``models.hydrology.below_ground`` module simulates the below-ground hydrological
processes for the Virtual Ecosystem. This includes vertical flow, soil moisture and
matric potential, groundwater storage, and subsurface horizontal flow.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray


def calculate_vertical_flow(
    soil_moisture: NDArray[np.float32],
    soil_layer_thickness: NDArray[np.float32],
    soil_moisture_capacity: float | NDArray[np.float32],
    soil_moisture_residual: float | NDArray[np.float32],
    hydraulic_conductivity: float | NDArray[np.float32],
    hydraulic_gradient: float | NDArray[np.float32],
    nonlinearily_parameter: float | NDArray[np.float32],
    groundwater_capacity: float | NDArray[np.float32],
    seconds_to_day: float,
) -> NDArray[np.float32]:
    r"""Calculate vertical water flow through soil column, [mm d-1].

    To calculate the flow of water through unsaturated soil, this function uses the
    Richards equation. First, the function calculates the effective saturation :math:`S`
    and effective hydraulic conductivity :math:`K(S)` based on the moisture content
    :math:`\Theta` using the Mualem-van Genuchten model
    :cite:p:`van_genuchten_closed-form_1980`:

    :math:`S = \frac{\Theta - \Theta_{r}}{\Theta_{s} - \Theta_{r}}`

    and

    :math:`K(S) = K_{s}* \sqrt{S} *(1-(1-S^{1/m})^{m})^{2}`

    where :math:`\Theta_{r}` is the residual moisture content, :math:`\Theta_{s}` is the
    saturated moisture content, :math:`K_{s}` is the saturated hydraulic conductivity,
    and :math:`m=1-1/n` is a shape parameter derived from the non-linearity parameter
    :math:`n`. Then, the function applies Darcy's law to calculate the water flow rate
    :math:`q` in :math:`\frac{m^3}{s^1}` considering the effective hydraulic
    conductivity:

    :math:`q = - K(S)*(\frac{dh}{dl}-1)`

    where :math:`\frac{dh}{dl}` is the hydraulic gradient with :math:`l` the
    length of the flow path in meters (here equal to the soil depth).

    Note that there are severe limitations to this approach on the temporal and
    spatial scale of this model and this can only be treated as a very rough
    approximation!

    Args:
        soil_moisture: Volumetric relative water content in top soil, [unitless]
        soil_layer_thickness: Thickness of all soil_layers, [mm]
        soil_moisture_capacity: Soil moisture capacity, [unitless]
        soil_moisture_residual: Residual soil moisture, [unitless]
        hydraulic_conductivity: Hydraulic conductivity of soil, [m/s]
        hydraulic_gradient: Hydraulic gradient (change in hydraulic head) along the flow
            path, positive values indicate downward flow, [m/m]
        nonlinearily_parameter: Dimensionless parameter in van Genuchten model that
            describes the degree of nonlinearity of the relationship between the
            volumetric water content and the soil matric potential.
        groundwater_capacity: Storage capacity of groundwater, [mm]
        seconds_to_day: Factor to convert between second and day

    Returns:
        volumetric flow rate of water, [mm d-1]
    """
    shape_parameter = 1 - 1 / nonlinearily_parameter

    # Calculate soil effective saturation in rel. vol. water content for each layer:
    effective_saturation = (soil_moisture - soil_moisture_residual) / (
        soil_moisture_capacity - soil_moisture_residual
    )

    # Calculate the effective hydraulic conductivity in m/s
    effective_conductivity = np.array(
        hydraulic_conductivity
        * np.sqrt(effective_saturation)
        * (1 - (1 - (effective_saturation) ** (1 / shape_parameter)) ** shape_parameter)
        ** 2,
    )

    # Calculate flow from top soil to lower soil in mm per month
    flow = -effective_conductivity * (hydraulic_gradient - 1) * seconds_to_day

    # Make sure that flow does not exceed storage capacity in mm
    available_storage = (soil_moisture - soil_moisture_residual) * soil_layer_thickness

    flow_min = []
    for i in np.arange(len(soil_moisture) - 1):
        flow_layer = np.where(
            effective_conductivity[i] < available_storage[i + 1],
            flow[i],
            available_storage[i + 1],
        )
        flow_min.append(flow_layer)

    outflow = np.where(
        effective_conductivity[-1] < groundwater_capacity,
        flow[-1],
        groundwater_capacity,
    )
    flow_min.append(outflow)

    return np.array(flow_min)


def update_soil_moisture(
    soil_moisture: NDArray[np.float32],
    vertical_flow: NDArray[np.float32],
    evapotranspiration: NDArray[np.float32],
    soil_moisture_capacity: NDArray[np.float32],
    soil_moisture_residual: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Update soil moisture profile.

    This function calculates soil moisture for each layer by removing the vertical flow
    of the current layer and adding it to the layer below. The implementation is based
    on :cite:t:`van_der_knijff_lisflood_2010`. Additionally, the evapotranspiration is
    removed from the second soil layer.

    Args:
        soil_moisture: Soil moisture after infiltration and surface evaporation, [mm]
        vertical_flow: Vertical flow between all layers, [mm]
        evapotranspiration: Canopy evaporation, [mm]
        soil_moisture_capacity: Soil moisture capacity for each layer, [mm]
        soil_moisture_residual: Residual soil moisture for each layer, [mm]

    Returns:
        updated soil moisture profile, relative volumetric water content, dimensionless
    """
    # TODO this is currently not conserving water
    # Remove vertical flow from topsoil moisture and ensure it is within capacity
    top_soil_moisture = np.clip(
        soil_moisture[0] - vertical_flow[0],
        soil_moisture_residual[0],
        soil_moisture_capacity[0],
    )

    # Add topsoil vertical flow to layer below and remove that layers flow as well as
    # evapotranspiration = root water uptake, and ensure it is within capacity
    root_soil_moisture = np.clip(
        soil_moisture[1] + vertical_flow[0] - vertical_flow[1] - evapotranspiration,
        soil_moisture_residual[1],
        soil_moisture_capacity[1],
    )

    # For all further soil layers, add the vertical flow from the layer above, remove
    # that layers flow, and ensure it is within capacity
    if len(vertical_flow) == 2:
        soil_moisture_updated = np.stack((top_soil_moisture, root_soil_moisture))

    elif len(vertical_flow) > 2:
        lower_soil_moisture = [
            np.clip(
                (soil_moisture[i + 1] + vertical_flow[i] - vertical_flow[i + 1]),
                soil_moisture_residual[i + 1],
                soil_moisture_capacity[i + 1],
            )
            for sm, vf in zip(
                soil_moisture[2:],
                vertical_flow[2:],
            )
            for i in range(len(soil_moisture) - 2)
        ]
        soil_moisture_updated = np.concatenate(
            ([top_soil_moisture], [root_soil_moisture], lower_soil_moisture)
        )

    return soil_moisture_updated


def convert_soil_moisture_to_water_potential(
    soil_moisture: NDArray[np.float32],
    air_entry_water_potential: float,
    water_retention_curvature: float,
    soil_moisture_capacity: float,
) -> NDArray[np.float32]:
    r"""Convert soil moisture into an estimate of water potential.

    This function provides a coarse estimate of soil water potential :math:`\Psi_{m}`.
    It is taken from :cite:t:`campbell_simple_1974`:

    :math:`\Psi_{m} = \Psi_{e} * (\frac{\Theta}{\Theta_{s}})^{b}`

    where :math:`\Psi_{e}` is the air-entry, :math:`\Theta` is the volumetric water
    content, :math:`\Theta_{s}` is the saturated water content, and :math:`b` is the
    water retention curvature parameter.

    Args:
        soil_moisture: Volumetric relative water content, [unitless]
        air_entry_water_potential: Water potential at which soil pores begin to aerate,
            [kPa]
        water_retention_curvature: Curvature of water retention curve, [unitless]
        soil_moisture_capacity: The relative water content at which the soil is fully
            saturated, [unitless].

    Returns:
        An estimate of the water potential of the soil, [kPa]
    """

    return air_entry_water_potential * (
        (soil_moisture / soil_moisture_capacity) ** water_retention_curvature
    )


def update_groundwater_storage(
    groundwater_storage: NDArray[np.float32],
    vertical_flow_to_groundwater: NDArray[np.float32],
    bypass_flow: NDArray[np.float32],
    max_percolation_rate_uzlz: float | NDArray[np.float32],
    groundwater_loss: float | NDArray[np.float32],
    reservoir_const_upper_groundwater: float | NDArray[np.float32],
    reservoir_const_lower_groundwater: float | NDArray[np.float32],
) -> dict[str, NDArray[np.float32]]:
    r"""Update groundwater storage and calculate below ground horizontal flow.

    Groundwater storage and transport are modelled using two parallel linear reservoirs,
    similar to the approach used in the HBV-96 model
    :cite:p:`lindstrom_development_1997` and the LISFLOOD
    :cite:p:`van_der_knijff_lisflood_2010` (see for full documentation).

    The upper zone represents a quick runoff component, which includes fast groundwater
    and subsurface flow through macro-pores in the soil. The lower zone represents the
    slow groundwater component that generates the base flow.

    The outflow from the upper zone to the channel, :math:`Q_{uz}`, [mm], equals:

    :math:`Q_{uz} = \frac{1}{T_{uz}} * UZ * \Delta t`

    where :math:`T_{uz}` is the reservoir constant for the upper groundwater layer
    [days], and :math:`UZ` is the amount of water that is stored in the upper zone [mm].
    The amount of water stored in the upper zone is computed as follows:

    :math:`UZ = D_{ls,gw} + D_{pref,gw} - D{uz,lz}`

    where :math:`D_{ls,gw}` is the flow from the lower soil layer to groundwater,
    :math:`D_{pref,gw}` is the amount of preferential flow or bypass flow per time step,
    :math:`D_{uz,lz}` is the amount of water that percolates from the upper to the lower
    zone, all in [mm].

    The water percolates from the upper to the lower zone is the inflow to the lower
    groundwater zone. This amount of water is provided by the upper groundwater zone.
    :math:`D_{uz,lz}` is a fixed amount per computational time step and it is defined as
    follows:

    :math:`D_{uz,lz} = min(GW_{perc} * \Delta t, UZ)`

    where :math:`GW_{perc}`, [mm day], is the maximum percolation rate from the upper to
    the lower groundwater zone. The outflow from the lower zone to the channel is then
    computed by:

    :math:`Q_{lz} = \frac{1}{T_{lz}} * LZ * \Delta t`

    :math:`T_{lz}` is the reservoir constant for the lower groundwater layer, [days],
    and :math:`LZ` is the amount of water that is stored in the lower zone, [mm].
    :math:`LZ` is computed as follows:

    :math:`LZ = D_{uz,lz} - (GW_{loss} * \Delta t)`

    where :math:`D_{uz,lz}` is the percolation from the upper groundwater zone,[mm],
    and :math:`GW_{loss}` is the maximum percolation rate from the lower groundwater
    zone, [mm day].

    The amount of water defined by :math:`GW_{loss}` never rejoins the river channel and
    is lost beyond the catchment boundaries or to deep groundwater systems. The larger
    the value of ath:`GW_{loss}`, the larger the amount of water that leaves the system.

    Args:
        groundwater_storage: Amount of water that is stored in the groundwater reservoir
            , [mm]
        vertical_flow_to_groundwater: Flow from the lower soil layer to groundwater for
            this timestep, [mm]
        bypass_flow: Flow that bypasses the soil matrix and drains directly to the
            groundwater, [mm]
        max_percolation_rate_uzlz: Maximum percolation rate between upper and lower
            groundwater zone, [mm d-1]
        groundwater_loss: Constant amount of water that never rejoins the river channel
            and is lost beyond the catchment boundaries or to deep groundwater systems,
            [mm]
        reservoir_const_upper_groundwater: Reservoir constant for the upper groundwater
            layer, [days]
        reservoir_const_lower_groundwater: Reservoir constant for the lower groundwater
            layer, [days]

    Returns:
        updated amount of water stored in upper and lower zone, outflow from the upper
        zone to the channel, and outflow from the lower zone to the channel
    """

    output = {}
    # The water that percolates from the upper to the lower groundwater zone is defined
    # as the minumum of `max_percolation_rate_uzlz` and the amount water stored in upper
    # zone, here `groundwater_storage[0]`
    percolation_to_lower_zone = np.where(
        max_percolation_rate_uzlz < groundwater_storage[0],
        max_percolation_rate_uzlz,
        groundwater_storage[0],
    )

    # Update water stored in upper zone, [mm]
    upper_zone = np.array(
        groundwater_storage[0]
        + vertical_flow_to_groundwater
        + bypass_flow
        - percolation_to_lower_zone
    )

    # Calculate outflow from the upper zone to the channel, [mm]
    output["subsurface_flow"] = upper_zone / reservoir_const_upper_groundwater

    # Update water stored in lower zone, [mm]
    lower_zone = np.array(
        groundwater_storage[1] + percolation_to_lower_zone - groundwater_loss
    )

    # Calculate outflow from the lower zone to the channel, [mm]
    output["baseflow"] = lower_zone / reservoir_const_lower_groundwater

    # Update ground water storage
    output["groundwater_storage"] = np.vstack((upper_zone, lower_zone))

    return output
