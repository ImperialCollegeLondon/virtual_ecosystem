"""The ``models.hydrology.below_ground`` module simulates the below-ground hydrological
processes for the Virtual Ecosystem. This includes vertical flow, soil moisture and
matric potential, groundwater storage, and subsurface horizontal flow.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray


def calculate_vertical_flow(
    soil_moisture: NDArray[np.float32],
    soil_layer_thickness: NDArray[np.float32],
    soil_layer_depth: NDArray[np.float32],
    soil_moisture_saturation: float | NDArray[np.float32],
    soil_moisture_residual: float | NDArray[np.float32],
    saturated_hydraulic_conductivity: float | NDArray[np.float32],
    air_entry_potential_inverse: float,
    van_genuchten_nonlinearily_parameter: float,
    pore_connectivity_parameter: float,
    groundwater_capacity: float | NDArray[np.float32],
    seconds_to_day: float,
) -> dict[str, NDArray[np.float32]]:
    r"""Calculate vertical water flow through soil column, [mm d-1].

    To calculate the flow of water through unsaturated soil, this function combines
    Richards' equation and Darcy's law for unsaturated flow. It calculates the effective
    saturation :math:`S_{e}` and effective unsaturated hydraulic conductivity
    :math:`K(\Theta)` based on the moisture content :math:`\Theta` using the van
    Genuchten - Mualem model
    (:cite:t:`van_genuchten_closed-form_1980`, :cite:t:`mualem_new_1976`).

    First, the effective saturation is calculated as:

    .. math ::
        S_{e} = \frac{\Theta - \Theta_{r}}{\Theta_{s} - \Theta_{r}}

    where :math:`\Theta_{r}` is the soil moisture residual and :math:`\Theta_{s}` is
    the soil moisture saturation.

    Then, the effective unsaturated hydraulic conductivity is computed as:

    .. math ::
        K(\Theta) = K_{s} S_{e}^{L} (1-(1-S_{e}^{\frac{1}{m}})^{m})^{2}

    where :math:`K_{s}` is the saturated hydraulic conductivity,
    :math:`L` is the pore connectivity parameter, and :math:`m=1-1/n` is a shape
    parameter derived from the non-linearity parameter :math:`n`.

    The soil matric potential :math:`\Psi_{m}` is calculated as follows:

    .. math ::
        \Psi_{m} = \frac{1}{\alpha} (S_{e}^{-\frac{1}{m}}-1)^\frac{1}{n}

    where :math:`\alpha` is the inverse of air entry value.

    Then, the function applies Darcy's law to calculate the water flow rate
    :math:`q` in :math:`\frac{m}{s-1}` considering the effective unsaturated hydraulic
    conductivity:

    .. math ::
        q = - K(\Theta) (\frac{d \Psi_{m}}{dz} + 1)

    where :math:`\frac{d \Psi_{m}}{dz}` is the matric potential gradient with :math:`z`
    the elevation (gravitational potential) or gravitational head. The result is
    converted to mm per day.

    Note that there are severe limitations to this approach on the temporal and
    spatial scale of this model and this can only be treated as a very rough
    approximation!

    Args:
        soil_moisture: Volumetric relative water content in top soil, [unitless]
        soil_layer_thickness: Thickness of all soil layers, [m]
        soil_layer_depth: Soil layer depth, [m]
        soil_moisture_saturation: Soil moisture saturation, [unitless]
        soil_moisture_residual: Residual soil moisture, [unitless]
        saturated_hydraulic_conductivity: Hydraulic conductivity of soil, [m/s]
        air_entry_potential_inverse: Inverse of air entry water potential (parameter
            alpha in van Genuchten model), [m-1]
        van_genuchten_nonlinearily_parameter: Dimensionless parameter in van Genuchten
            model that describes the degree of nonlinearity of the relationship between
            the volumetric water content and the soil matric potential.
        pore_connectivity_parameter: Pore connectivity parameter, dimensionless
        groundwater_capacity: Storage capacity of groundwater, [m]
        seconds_to_day: Factor to convert between second and day

    Returns:
        matric potential,[m] volumetric flow rate of water, [mm d-1]
    """

    output = {}
    shape_parameter = 1 - 1 / van_genuchten_nonlinearily_parameter

    # Calculate soil effective saturation in rel. vol. water content for each layer:
    # TODO make this function a tool
    effective_saturation = (soil_moisture - soil_moisture_residual) / (
        soil_moisture_saturation - soil_moisture_residual
    )

    # Calculate matric potential for each grid point and depth
    matric_potential = calculate_matric_potential(
        effective_saturation=effective_saturation,
        air_entry_potential_inverse=air_entry_potential_inverse,
        van_genuchten_nonlinearily_parameter=van_genuchten_nonlinearily_parameter,
    )

    # Calculate the unsaturated (effective) hydraulic conductivity in m/s
    effective_conductivity = np.array(
        saturated_hydraulic_conductivity
        * effective_saturation**pore_connectivity_parameter
        * (1 - (1 - (effective_saturation) ** (1 / shape_parameter)) ** shape_parameter)
        ** 2,
    )

    # Compute matric potential gradient
    matric_potential_gradient = np.gradient(matric_potential, soil_layer_depth, axis=0)

    # Calculate vertical flow from top soil to lower soil in m s-1
    flow = -effective_conductivity * (matric_potential_gradient + 1)

    # Make sure that flow does not exceed storage capacity in m
    available_storage = (soil_moisture - soil_moisture_residual) * soil_layer_thickness

    # Flow in m per day to match unit of available storage
    flow_timestep = flow * seconds_to_day

    # Redistribute water in soil layers
    flow_min = []
    for i in np.arange(len(soil_moisture) - 1):
        flow_layer = np.where(
            flow_timestep[i] < available_storage[i + 1],
            flow_timestep[i],
            available_storage[i + 1],
        )
        flow_min.append(flow_layer)

    outflow = np.where(
        flow_timestep[-1] < groundwater_capacity,
        flow_timestep[-1],
        groundwater_capacity,
    )
    flow_min.append(outflow)

    output["matric_potential"] = matric_potential
    output["vertical_flow"] = np.abs(np.array(flow_min) / 1000.0)  # mm per day
    return output


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


def calculate_matric_potential(
    effective_saturation: NDArray[np.float32],
    air_entry_potential_inverse: float,
    van_genuchten_nonlinearily_parameter: float,
) -> NDArray[np.float32]:
    r"""Convert soil moisture into an estimate of water potential.

    This function estimates soil water potential :math:`\Psi_{m}` as using the van
    Genuchten - Mualem model
    (:cite:t:`van_genuchten_closed-form_1980`, :cite:t:`mualem_new_1976`):

    .. math ::
        \Psi_{m} = -\frac{1}{\alpha} (S_{e}^{-\frac{1}{m}} - 1)^{(\frac{1}{n})}

    where :math:`\alpha` is the inverse of the air-entry , :math:`S_{e}` is the
    effective saturation, n and m are van Genuchten parmeters.

    Args:
        effective_saturation: Effective saturation
        air_entry_potential_inverse: Inverse of air entry potential (parameter alpha in
            van Genuchten), [m-1]
        van_genuchten_nonlinearily_parameter: Dimensionless parameter in van Genuchten
            model that describes the degree of nonlinearity of the relationship between
            the volumetric water content and the soil matric potential.

    Returns:
        An estimate of the water potential of the soil, [m]
    """
    shape_parameter = 1 - 1 / van_genuchten_nonlinearily_parameter

    return (
        -1
        / air_entry_potential_inverse
        * (effective_saturation ** (-1 / shape_parameter) - 1)
        ** (1 / van_genuchten_nonlinearily_parameter)
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
    :cite:p:`van_der_knijff_lisflood_2010`.

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
