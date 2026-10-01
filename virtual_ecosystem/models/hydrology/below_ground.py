"""The ``models.hydrology.below_ground`` module simulates the below-ground hydrological
processes for the Virtual Ecosystem. This includes vertical flow, soil moisture and
matric potential, groundwater storage, and subsurface horizontal flow.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.models.hydrology.hydrology_tools import (
    calculate_effective_saturation,
)


def calculate_vertical_flow(
    soil_moisture: NDArray[np.floating],
    soil_layer_thickness: NDArray[np.floating],
    soil_layer_depth: NDArray[np.floating],
    soil_moisture_saturation: float | NDArray[np.floating],
    soil_moisture_residual: float | NDArray[np.floating],
    saturated_hydraulic_conductivity: float | NDArray[np.floating],
    air_entry_potential_inverse: float,
    van_genuchten_nonlinearity_parameter: float,
    pore_connectivity_parameter: float,
    seconds_to_day: float,
    denominator_tolerance: float,
) -> dict[str, NDArray[np.floating]]:
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
        \Psi_{m} = -\frac{1}{\alpha} (S_{e}^{-\frac{1}{m}}-1)^\frac{1}{n}

    where :math:`\alpha` is the inverse of air entry value. :math:`\Psi_{m}` is
    negative for unsaturated soil (tension).

    Then, the function applies Darcy's law to calculate the downward water flux
    :math:`q` in :math:`\text{m s}^{-1}`. Using depth :math:`d` as the vertical
    coordinate (positive downward), the gravitational head decreases by 1 m per
    meter of depth, so the total hydraulic gradient is:

    .. math::
        q = K_{\mathrm{face}}
        \left(1 - \frac{d\Psi_m}{dd}\right)

    where :math:`\frac{d\Psi_{m}}{dd}` is the matric potential gradient with
    respect to depth :math:`d` (positive downward). The :math:`-1` gravity term
    arises because elevation decreases as depth increases: a unit increase in depth
    reduces the gravitational head by 1 m, driving flow downward.
    :math:`K_{\mathrm{face}}` is the harmonic mean of the adjacent layers'
    effective conductivities. Upward flux (negative :math:`q`) is set
    to zero, suppressing capillary rise as a deliberate simplification.
    The flow is converted from :math:`\text{m s}^{-1}` to :math:`\text{mm d}^{-1}`
    and limited by available water in the source layer and pore space in the
    receiving layer.

    Note that there are severe limitations to this approach on the temporal and
    spatial scale of this model and this can only be treated as a very rough
    approximation!

    Args:
        soil_moisture: Volumetric relative water content in top soil, [unitless]
        soil_layer_thickness: Thickness of all soil layers, [m]
        soil_layer_depth: Soil layer depth (positive downward), [m]
        soil_moisture_saturation: Soil moisture saturation, [unitless]
        soil_moisture_residual: Residual soil moisture, [unitless]
        saturated_hydraulic_conductivity: Hydraulic conductivity of soil, [m/s]
        air_entry_potential_inverse: Inverse of air entry water potential (parameter
            alpha in van Genuchten model), [m-1]
        van_genuchten_nonlinearity_parameter: Dimensionless parameter in van Genuchten
            model that describes the degree of nonlinearity of the relationship between
            the volumetric water content and the soil matric potential.
        pore_connectivity_parameter: Pore connectivity parameter, dimensionless
        seconds_to_day: Factor to convert between second and day
        denominator_tolerance: Small value to avoid division by zero

    Returns:
        matric potential, [m]; volumetric flow rate of water, [mm d-1]; effective
        saturation, [rel. vol.]
    """

    # Calculate soil effective saturation in rel. vol. water content for each layer:
    effective_saturation = calculate_effective_saturation(
        soil_moisture=soil_moisture,
        soil_moisture_saturation=soil_moisture_saturation,
        soil_moisture_residual=soil_moisture_residual,
    )
    effective_saturation = np.clip(
        np.nan_to_num(effective_saturation, nan=0.0, posinf=1.0, neginf=0.0),
        0.0,
        1.0,
    )

    # Calculate matric potential for each grid point and depth.
    # psi_m is negative for unsaturated soil (tension).
    n_parameter = van_genuchten_nonlinearity_parameter
    m_parameter = 1.0 - 1.0 / n_parameter

    se_for_potential = np.clip(effective_saturation, denominator_tolerance, 1.0)
    matric_potential = calculate_matric_potential(
        effective_saturation=se_for_potential,
        air_entry_potential_inverse=air_entry_potential_inverse,
        van_genuchten_nonlinearity_parameter=van_genuchten_nonlinearity_parameter,
        denominator_tolerance=denominator_tolerance,
    )

    # Calculate the unsaturated (effective) hydraulic conductivity, [m s-1].
    # The saturated hydraulic conductivity is reduced according to the current effective
    # saturation. Dry soil therefore conducts less water.
    effective_conductivity = (
        saturated_hydraulic_conductivity
        * effective_saturation**pore_connectivity_parameter
        * (1.0 - (1.0 - effective_saturation ** (1.0 / m_parameter)) ** m_parameter)
        ** 2
    )

    # Available water and pore space are water depths [mm]:
    # volumetric moisture [-] * layer thickness [m] * 1000 [mm/m].
    available_water_mm = (
        np.maximum(soil_moisture - soil_moisture_residual, 0.0)
        * soil_layer_thickness
        * 1000.0
    )
    receiving_space_mm = (
        np.maximum(soil_moisture_saturation - soil_moisture, 0.0)
        * soil_layer_thickness
        * 1000.0
    )

    # Estimate conductivity at each layer boundary using the harmonic mean.
    # The harmonic mean makes a low-conductivity layer restrict flow more strongly
    # than an arithmetic average would.
    conductivity_above = effective_conductivity[:-1]
    conductivity_below = effective_conductivity[1:]
    conductivity_sum = conductivity_above + conductivity_below
    conductivity_boundary = np.divide(
        2.0 * conductivity_above * conductivity_below,
        conductivity_sum,
        out=np.zeros_like(conductivity_sum),
        where=conductivity_sum > 0,
    )

    # Matric potential is negative pressure head [m]. Depth increases downward,
    # so this Darcy form gives positive flux for downward flow.
    # k_boundary [m/s] * hydraulic gradient [-] = flux [m/s].
    matric_gradient = np.gradient(
        matric_potential,
        soil_layer_depth,
        axis=0,
    )[:-1]
    flux_m_per_second = conductivity_boundary * (1.0 - matric_gradient)

    # Convert flux rate [m s-1] to [mm day-1].
    flux_mm_per_day = (
        np.maximum(
            np.nan_to_num(
                flux_m_per_second,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            ),
            0.0,
        )
        * seconds_to_day
        * 1000.0
    )

    # Limit transfer: the upper layer must have water to lose, and the lower
    # layer must have pore space to receive it.
    vertical_flow = np.zeros_like(soil_moisture)
    vertical_flow[:-1] = np.minimum(
        flux_mm_per_day,
        np.minimum(
            available_water_mm[:-1],
            receiving_space_mm[1:],
        ),
    )

    # Free-drainage lower boundary: unit hydraulic gradient (gravity only), q = K.
    # This assumes the matric potential gradient is zero at the base of the column,
    # so only gravity drives flow out of the bottom layer.
    # Limited by water available in the bottom layer.
    bottom_flux_mm_per_day = (
        np.maximum(
            np.nan_to_num(
                effective_conductivity[-1],
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            ),
            0.0,
        )
        * seconds_to_day
        * 1000.0
    )
    vertical_flow[-1] = np.minimum(
        bottom_flux_mm_per_day,
        available_water_mm[-1],
    )

    return {
        "matric_potential": np.nan_to_num(
            matric_potential,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        ),
        "vertical_flow": vertical_flow,
        "effective_saturation": effective_saturation,
    }


def update_soil_moisture(
    soil_moisture: NDArray[np.floating],
    vertical_flow: NDArray[np.floating],
    transpiration: NDArray[np.floating],
    subsurface_stormflow: NDArray[np.floating],
    soil_moisture_saturation: NDArray[np.floating],
    soil_moisture_residual: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Update soil moisture profile.

    This function calculates soil moisture for each layer by removing the vertical flow
    of the current layer and adding it to the layer below. The implementation is based
    on :cite:t:`van_der_knijff_lisflood_2010`. Additionally, the canopy transpiration
    and the subsurface stormflow are removed from the second soil layer.

    Args:
        soil_moisture: Soil moisture after infiltration and surface evaporation, [mm]
        vertical_flow: Vertical flow between all layers, [mm]
        transpiration: Canopy transpiration, [mm]
        subsurface_stormflow: Subsurface storm flow, [mm]
        soil_moisture_saturation: Soil moisture saturation for each layer, [mm]
        soil_moisture_residual: Residual soil moisture for each layer, [mm]

    Returns:
        updated soil moisture profile, relative volumetric water content, dimensionless
    """
    # TODO this is currently not conserving water
    # Remove vertical flow from topsoil moisture and ensure it is within capacity
    top_soil_moisture = np.clip(
        soil_moisture[0] - vertical_flow[0],
        soil_moisture_residual[0],
        soil_moisture_saturation[0],
    )

    # Add topsoil vertical flow to layer below and remove that layers flow as well as
    # canopy transpiration = root water uptake, and ensure it is within capacity
    root_soil_moisture = np.clip(
        soil_moisture[1]
        + vertical_flow[0]
        - vertical_flow[1]
        - transpiration
        - subsurface_stormflow,
        soil_moisture_residual[1],
        soil_moisture_saturation[1],
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
                soil_moisture_saturation[i + 1],
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
    effective_saturation: NDArray[np.floating],
    air_entry_potential_inverse: float,
    van_genuchten_nonlinearity_parameter: float,
    denominator_tolerance: float,
) -> NDArray[np.floating]:
    r"""Convert soil moisture into an estimate of water potential.

    This function estimates soil water potential :math:`\Psi_{m}` as using the van
    Genuchten - Mualem model
    (:cite:t:`van_genuchten_closed-form_1980`, :cite:t:`mualem_new_1976`):

    .. math ::
        \Psi_{m} = -\frac{1}{\alpha} (S_{e}^{-\frac{1}{m}} - 1)^{(\frac{1}{n})}

    where :math:`\alpha` is the inverse of the air-entry , :math:`S_{e}` is the
    effective saturation, n and m are van Genuchten parameters.

    Args:
        effective_saturation: Effective saturation
        air_entry_potential_inverse: Inverse of air entry potential (parameter alpha in
            van Genuchten), [m-1]
        van_genuchten_nonlinearity_parameter: Dimensionless parameter in van Genuchten
            model that describes the degree of nonlinearity of the relationship between
            the volumetric water content and the soil matric potential.
        denominator_tolerance: Small value to prevent division by zero

    Returns:
        An estimate of the water potential of the soil, [m]
    """
    shape_parameter = 1 - 1 / van_genuchten_nonlinearity_parameter
    return (
        -1
        / air_entry_potential_inverse
        * (effective_saturation ** (-1 / shape_parameter) - 1)
        ** (1 / van_genuchten_nonlinearity_parameter)
    )


def update_groundwater_storage(
    groundwater_storage: NDArray[np.floating],
    vertical_flow_to_groundwater: NDArray[np.floating],
    bypass_flow: NDArray[np.floating],
    max_percolation_rate_uzlz: float | NDArray[np.floating],
    groundwater_loss: float | NDArray[np.floating],
    reservoir_const_upper_groundwater: float | NDArray[np.floating],
    reservoir_const_lower_groundwater: float | NDArray[np.floating],
) -> dict[str, NDArray[np.floating]]:
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
    # as the minimum of `max_percolation_rate_uzlz` and the amount water stored in upper
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
    output["subsurface_flow"] = np.maximum(
        0.0, upper_zone / reservoir_const_upper_groundwater
    )

    # Update water stored in lower zone, [mm], must be >=0
    lower_zone = np.array(
        groundwater_storage[1] + percolation_to_lower_zone - groundwater_loss
    )

    # Calculate outflow from the lower zone to the channel, [mm], must be >=0
    output["baseflow"] = np.maximum(0.0, lower_zone / reservoir_const_lower_groundwater)

    # Update ground water storage
    output["groundwater_storage"] = np.vstack((upper_zone, lower_zone))

    return output


def calculate_subsurface_stormflow(
    effective_saturation: NDArray[np.floating],
    root_soil_moisture: NDArray[np.floating],
    transpiration: NDArray[np.floating],
    stormflow_coefficient: float,
    saturation_exponent: float,
) -> NDArray[np.floating]:
    r"""Calculate lateral subsurface stormflow (Q2).

    The lateral subsurface flow implementation is based on after
    :cite:t:`ye_regionalization_2014`:

    .. math::
        Q2 = k_{Q2} * S_{e}^beta_{Q2} * max(root_soil_moisture - transpiration, 0)

    where :math:`Q2` is the lateral subsurface stormflow (mm timestep-1), :math:`k_{Q2}`
    is the empirical lateral flow coefficient, :math:`S_{e}` is the effective saturation
    of the middle soil layer (-), :math:`beta_{Q2}` is a non-linearity exponent,
    :math:`S2` is the middle soil water storage (mm), :math:`T` is the transpiration
    extracted from the middle soil layer during the current timestep (mm).

    Args:
        effective_saturation: Effective saturation of root soil layer, [-]
        root_soil_moisture: Root-zone soil moisture, [mm]
        transpiration: Transpiration, equivalent to root water uptake, [mm]
        stormflow_coefficient: Stormflow coefficient, [-]
        saturation_exponent: Saturation exponent, [-]

    Returns:
        Subsurface stormflow, [mm]
    """

    available_water = np.maximum(root_soil_moisture - transpiration, 0.0)

    subsurface_stormflow = (
        stormflow_coefficient
        * effective_saturation**saturation_exponent
        * available_water
    )

    return np.maximum(subsurface_stormflow, 0.0)
