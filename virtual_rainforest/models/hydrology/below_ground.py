"""The ``models.hydrology.below_ground`` module simulates the below-ground hydrological
processes for the Virtual Rainforest. At the moment, this includes vertical flow, and
soil moisture. In the future, this will also include subsurface horizontal flow.
"""  # noqa: D205, D415

from typing import Union

import numpy as np
from numpy.typing import NDArray


def calculate_vertical_flow(
    soil_moisture: NDArray[np.float32],
    soil_layer_thickness: NDArray[np.float32],
    soil_moisture_capacity: Union[float, NDArray[np.float32]],
    soil_moisture_residual: Union[float, NDArray[np.float32]],
    hydraulic_conductivity: Union[float, NDArray[np.float32]],
    hydraulic_gradient: Union[float, NDArray[np.float32]],
    nonlinearily_parameter: Union[float, NDArray[np.float32]],
    groundwater_capacity: Union[float, NDArray[np.float32]],
    seconds_to_day: float,
) -> NDArray[np.float32]:
    r"""Calculate vertical water flow through soil column.

    To calculate the flow of water through unsaturated soil, this function uses the
    Richards equation. First, the function calculates the effective saturation :math:`S`
    and effective hydraulic conductivity :math:`K(S)` based on the moisture content
    :math:`\Theta` using the van Genuchten/Mualem model:

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
        soil_moisture_capacity: soil moisture capacity, [unitless]
        soil_moisture_residual: residual soil moisture, [unitless]
        hydraulic_conductivity: hydraulic conductivity of soil, [m/s]
        hydraulic_gradient: hydraulic gradient (change in hydraulic head) along the flow
            path, positive values indicate downward flow, [m/m]
        nonlinearily_parameter: dimensionless parameter in van Genuchten model that
            describes the degree of nonlinearity of the relationship between the
            volumetric water content and the soil matric potential.
        groundwater_capacity: storage capacity of groundwater
        seconds_to_day: factor to convert between second and day

    Returns:
        volumetric flow rate of water, [mm/timestep]
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

    groundwater_storage = groundwater_capacity * np.sum(soil_layer_thickness, axis=0)

    outflow = np.where(
        effective_conductivity[-1] < groundwater_storage,
        flow[-1],
        groundwater_storage,
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
    of the current layer and adding it to the layer below. Additionally, the
    evapotranspiration is removed from the second soil layer.

    Args:
        soil_moisture: soil moisture after infiltration and surface evaporation, [mm]
        vertical_flow: vertical flow between all layers, [mm]
        evapotranspiration: canopy evaporation, [mm]
        soil_moisture_capacity: soil moisture capacity for each layer, [mm]
        soil_moisture_residual: residual soil moisture for each layer, [mm]

    Returns:
        updated soil moisture profile, relative volumetric water content, dimensionless
    """
    # TODO this is currently not conserving water
    top_soil_moisture = np.clip(
        soil_moisture[0] - vertical_flow[0],
        soil_moisture_residual[0],
        soil_moisture_capacity[0],
    )

    root_soil_moisture = np.clip(
        soil_moisture[1] + vertical_flow[0] - vertical_flow[1] - evapotranspiration,
        soil_moisture_residual[1],
        soil_moisture_capacity[1],
    )

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


def soil_moisture_to_matric_potential(
    soil_moisture: NDArray[np.float32],
    soil_moisture_capacity: Union[float, NDArray[np.float32]],
    soil_moisture_residual: Union[float, NDArray[np.float32]],
    nonlinearily_parameter: Union[float, NDArray[np.float32]],
    alpha: Union[float, NDArray[np.float32]],
) -> NDArray[np.float32]:
    r"""Convert soil moisture to matric potential using van Genuchten/Mualem model.

    The soil water content is converted to matric potential as follows:

    :math:`S = \frac{\Theta-\Theta_{r}}{\Theta_{s}-\Theta_{r}} = (1+(\alpha*\Phi)^n)^-m`

    where :math:`S` is the effective saturation (dimensionless), :math:`\Theta_{r}` and
    :math:`\Theta_{s}` are the residual and saturated moisture content or soil moisture
    capacity, respectively. `math`:\Phi` is the soil water matric potential and
    :math:`m`, :math:`n`, and :math:`\alpha` are shape parameters of the water retention
    curve.

    Args:
        soil_moisture: Volumetric relative water content in top soil, [unitless]
        soil_moisture_capacity: soil moisture capacity, [unitless]
        soil_moisture_residual: residual soil moisture, [unitless]
        nonlinearily_parameter: dimensionless parameter n in van Genuchten model that
            describes the degree of nonlinearity of the relationship between the
            volumetric water content and the soil matric potential.
        alpha: dimensionless parameter alpha in van Genuchten model that corresponds
            approximately to the inverse of the air-entry value, [kPa-1]

    Returns:
        soil water matric potential, [kPa]
    """

    shape_parameter = 1 - 1 / nonlinearily_parameter

    # Calculate soil effective saturation in rel. vol. water content for each layer:
    effective_saturation = (soil_moisture - soil_moisture_residual) / (
        soil_moisture_capacity - soil_moisture_residual
    )

    # Solve for phi
    effective_saturation_m = effective_saturation ** (-1 / shape_parameter)
    effective_saturation_1 = effective_saturation_m - 1
    effective_saturation_n = effective_saturation_1 ** (1 / nonlinearily_parameter)
    soil_matric_potential = effective_saturation_n / alpha

    return soil_matric_potential


def update_groundwater_storge(
    groundwater_storage: NDArray[np.float32],
    vertical_flow_to_groundwater: NDArray[np.float32],
    bypass_flow: NDArray[np.float32],
    max_percolation_rate_uzlz: Union[float, NDArray[np.float32]],
    groundwater_loss: Union[float, NDArray[np.float32]],
    reservoir_const_upper_groundwater: Union[float, NDArray[np.float32]],
    reservoir_const_lower_groundwater: Union[float, NDArray[np.float32]],
) -> list[NDArray[np.float32]]:
    """Update groundwater storage and calculate below ground horizontal flow.

    Groundwater storage and transport are modelled using two parallel linear reservoirs,
    similar to the approach used in the HBV-96 model (Lindström et al., 1997) and the
    LISFLOOD model. The upper zone represents a quick runoff component, which includes
    fast groundwater and subsurface flow through macro-pores in the soil. The lower zone
    represents the slow groundwater component that generates the base flow.

    Args:
        groundwater_storage: amount of water that is stored in the groundwater reservoir
            , [mm]
        vertical_flow_to_groundwater: flux from the lower soil layer to groundwater for
            this timestep, [mm]
        bypass_flow: flow that bypasses the soil matrix and drains directly to the
            groundwater, [mm]
        max_percolation_rate_uzlz: maximum perclation rate between pper and lower
            groundwater zone, [mm d-1]
        groundwater_loss: constant amount of water that never rejoins the river channel
            and is lost beyond the catchment boundaries or to deep groundwater systems,
            [mm]
        reservoir_const_upper_groundwater: reservoir constant for the upper groundwater
            layer, [days]
        reservoir_const_lower_groundwater: reservoir constant for the lower groundwater
            layer, [days]

    Returns:
        updated amount of water stored in upper and lower zone, outflow from the upper
            zone to the channel, and outflow from the lower zone to the channel
    """

    # percolation to lower zone
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
    outflow_upper_zone = 1 / reservoir_const_upper_groundwater * upper_zone

    # Update water stored in lower zone, [mm]
    lower_zone = np.array(
        groundwater_storage[1] + percolation_to_lower_zone - groundwater_loss
    )

    # Calculate outflow from the lower zone to the channel, [mm]
    outflow_lower_zone = 1 / reservoir_const_lower_groundwater * lower_zone

    updated_groundwater_storage = np.vstack((upper_zone, lower_zone))

    return [updated_groundwater_storage, outflow_upper_zone, outflow_lower_zone]
