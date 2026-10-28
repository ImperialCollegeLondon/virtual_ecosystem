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

    The function then applies Darcy's law to calculate the downward water flux
    :math:`q` in :math:`\text{m s}^{-1}`. Using the standard soil physics convention
    where :math:`z` is positive upward (so depth is negative, becoming more negative
    with depth), the total hydraulic head combines the matric potential and
    gravitational components. The Darcy flux is:

    .. math::
        q = -K(\Theta) \left(\frac{d\Psi_m}{dz} + 1\right)

    where :math:`\frac{d\Psi_{m}}{dz}` is the matric potential gradient with
    respect to :math:`z` (positive upward), and the :math:`+1` gravity term reflects
    the fact that gravitational head increases by 1 m per metre upward, driving flow
    downward. The leading negative sign follows the standard Darcy convention: flow
    is in the direction of decreasing total head. Under uniform moisture conditions
    (:math:`\frac{d\Psi_m}{dz} = 0`), this reduces to :math:`q = -K`, which is
    negative in the upward-positive frame and therefore represents downward flow.

    Since :math:`z` is negative downward, the gradient denominator
    :math:`z_{i+1} - z_i` is negative (deeper layers have more negative :math:`z`),
    so the sign of the gradient is handled consistently by the finite difference.
    Downward flux is negative in this convention; it is negated before storage so
    that vertical_flow is always a positive quantity representing
    downward transfer in mm d-1. Upward flux q
    is set to zero, suppressing capillary rise as a deliberate simplification.

    The flow is converted from :math:`\text{m s}^{-1}` to :math:`\text{mm d}^{-1}`
    and limited by available water in the source layer and pore space in the
    receiving layer.

    Note that there are severe limitations to this approach on the temporal and
    spatial scale of this model and this can only be treated as a very rough
    approximation!

    Args:
        soil_moisture: Volumetric relative water content in top soil, [unitless]
        soil_layer_thickness: Thickness of all soil layers, [m]
        soil_layer_depth: Soil layer depth, negative downward (z positive upward), [m]
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
    m_parameter = 1.0 - 1.0 / van_genuchten_nonlinearity_parameter

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
    # The harmonic mean ensures a low-conductivity layer restricts flow more
    # strongly than an arithmetic mean would.
    conductivity_above = effective_conductivity[:-1]
    conductivity_below = effective_conductivity[1:]
    conductivity_sum = conductivity_above + conductivity_below
    conductivity_boundary = np.divide(
        2.0 * conductivity_above * conductivity_below,
        conductivity_sum,
        out=np.zeros_like(conductivity_sum),
        where=conductivity_sum > 0,
    )

    # Matric potential gradient with respect to depth, [m m-1], positive upward.
    matric_gradient = np.gradient(
        matric_potential,
        soil_layer_depth,
        axis=0,
    )[:-1]

    # Darcy flux [m s-1]: q = -K * (d_psi_m/dz + 1)
    # z is positive upward, so downward flow is negative q.
    # Under uniform moisture (d_psi_m/dz = 0): q = -K < 0 (downward) as expected.
    flux_m_per_second = -conductivity_boundary * (matric_gradient + 1.0)

    # Retain only downward flux (negative q in upward-positive convention).
    # Upward flux (positive q) is set to zero, suppressing capillary rise.
    # Negate so that vertical_flow is stored as a positive downward quantity [mm d-1].
    flux_mm_per_day = (
        np.minimum(
            np.nan_to_num(
                flux_m_per_second,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            ),
            0.0,
        )
        * -1.0
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

    # Free-drainage lower boundary: unit hydraulic gradient (gravity only), q = -K.
    # Setting d_psi_m/dz = 0 in the Darcy equation gives q = -K(0 + 1) = -K,
    # i.e. downward flux of magnitude K. Stored as positive mm/day.
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
) -> dict[str, NDArray[np.floating]]:
    """Update soil moisture profile with mass-conserving flux limitation.

    This function calculates soil moisture for each layer by removing the vertical flow
    of the current layer and adding it to the layer below. Additionally, canopy
    transpiration and subsurface stormflow are removed from the second soil layer.
    If the requested outgoing fluxes exceed the water available above residual soil
    moisture, only the removable fluxes are reduced so that mass is conserved and soil
    moisture does not fall below the residual value because of flux removal.
    Transpiration is treated as an external demand and is not modified here.

    Args:
        soil_moisture: Soil moisture after infiltration and surface evaporation, [mm]
        vertical_flow: Potential vertical flow between all layers, [mm]
        transpiration: Canopy transpiration, [mm]
        subsurface_stormflow: Potential subsurface storm flow, [mm]
        soil_moisture_saturation: Soil moisture saturation for each layer, [mm]
        soil_moisture_residual: Residual soil moisture for each layer, [mm]

    Returns:
        Dictionary containing updated soil moisture profile and the actual removable
        fluxes used.
    """
    n_layers = len(soil_moisture)

    soil_moisture_updated = np.zeros_like(soil_moisture, dtype=float)
    vertical_flow_actual = np.zeros_like(vertical_flow, dtype=float)
    subsurface_stormflow_actual = np.array(subsurface_stormflow, copy=True, dtype=float)
    transpiration_actual = np.zeros_like(transpiration, dtype=float)

    available_outflow = np.maximum(
        soil_moisture[0] - soil_moisture_residual[0],
        0.0,
    )
    vertical_flow_actual[0] = np.minimum(vertical_flow[0], available_outflow)
    soil_moisture_updated[0] = soil_moisture[0] - vertical_flow_actual[0]

    if n_layers > 1:
        root_inflow = vertical_flow_actual[0]
        root_storage_before_outflow = soil_moisture[1] + root_inflow

        root_available_outflow = np.maximum(
            root_storage_before_outflow - soil_moisture_residual[1],
            0.0,
        )

        transpiration_actual = np.minimum(
            np.maximum(transpiration, 0.0),
            root_available_outflow,
        )

        root_available_for_removable_fluxes = np.maximum(
            root_available_outflow - transpiration_actual,
            0.0,
        )

        root_total_removable_demand = vertical_flow[1] + subsurface_stormflow_actual

        root_scale = np.where(
            root_total_removable_demand > root_available_for_removable_fluxes,
            np.divide(
                root_available_for_removable_fluxes,
                root_total_removable_demand,
                out=np.ones_like(root_total_removable_demand, dtype=float),
                where=root_total_removable_demand > 0.0,
            ),
            1.0,
        )

        vertical_flow_actual[1] = vertical_flow[1] * root_scale
        subsurface_stormflow_actual = subsurface_stormflow_actual * root_scale

        soil_moisture_updated[1] = (
            root_storage_before_outflow
            - vertical_flow_actual[1]
            - transpiration_actual
            - subsurface_stormflow_actual
        )

    for i in range(2, n_layers):
        inflow = vertical_flow_actual[i - 1]
        storage_before_outflow = soil_moisture[i] + inflow

        available_outflow = np.maximum(
            storage_before_outflow - soil_moisture_residual[i],
            0.0,
        )

        vertical_flow_actual[i] = np.minimum(vertical_flow[i], available_outflow)
        soil_moisture_updated[i] = storage_before_outflow - vertical_flow_actual[i]

    soil_moisture_updated = np.clip(
        soil_moisture_updated,
        soil_moisture_residual,
        soil_moisture_saturation,
    )

    return {
        "soil_moisture": soil_moisture_updated,
        "vertical_flow": vertical_flow_actual,
        "subsurface_stormflow": subsurface_stormflow_actual,
        "transpiration": transpiration_actual,
    }


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
        denominator_tolerance: Small value to avoid division by zero

    Returns:
        An estimate of the water potential of the soil, [m]
    """
    shape_parameter = 1 - 1 / van_genuchten_nonlinearity_parameter
    effective_saturation_safe = np.maximum(effective_saturation, denominator_tolerance)

    return (
        -1
        / air_entry_potential_inverse
        * (effective_saturation_safe ** (-1 / shape_parameter) - 1)
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

    :math:`Q_{uz} = \frac{1}{T_{uz}} * UZ`

    where :math:`T_{uz}` is the reservoir constant for the upper groundwater layer
    [days], and :math:`UZ` is the amount of water that is stored in the upper zone [mm].
    The amount of water stored in the upper zone is computed as follows:

    :math:`UZ = GW_{uz} + D_{ls,gw} + D_{pref,gw} - D_{uz,lz}`

    where :math:`GW_{uz}` is the amount of water stored in the upper groundwater zone
    at the start of the timestep, :math:`D_{ls,gw}` is the flow from the lower soil
    layer to groundwater, :math:`D_{pref,gw}` is the amount of preferential flow or
    bypass flow per time step, and :math:`D_{uz,lz}` is the amount of water that
    percolates from the upper to the lower zone, all in [mm].

    The water that percolates from the upper to the lower zone is the inflow to the
    lower groundwater zone. This amount of water is provided by the upper groundwater
    zone. :math:`D_{uz,lz}` is a fixed amount per computational time step and it is
    defined as follows:

    :math:`D_{uz,lz} = \min(GW_{perc}, UZ)`

    where :math:`GW_{perc}`, [mm], is the maximum percolation rate from the upper to
    the lower groundwater zone for the timestep. The outflow from the lower zone to the
    channel is then computed by:

    :math:`Q_{lz} = \frac{1}{T_{lz}} * LZ`

    :math:`T_{lz}` is the reservoir constant for the lower groundwater layer, [days],
    and :math:`LZ` is the amount of water that is stored in the lower zone, [mm].
    :math:`LZ` is computed as follows:

    :math:`LZ = GW_{lz} + D_{uz,lz} - GW_{loss,act}`

    where :math:`GW_{lz}` is the amount of water stored in the lower groundwater zone
    at the start of the timestep, :math:`D_{uz,lz}` is the percolation from the upper
    groundwater zone, [mm], and :math:`GW_{loss,act}` is the actual groundwater loss,
    [mm], defined as:

    :math:`GW_{loss,act} = \min(GW_{loss}, GW_{lz} + D_{uz,lz})`

    The amount of water defined by :math:`GW_{loss}` never rejoins the river channel and
    is lost beyond the catchment boundaries or to deep groundwater systems. The larger
    the value of :math:`GW_{loss}`, the larger the amount of water that leaves the
    system. The actual groundwater loss is capped by the water available in the lower
    zone so that groundwater storage cannot become negative.

    Args:
        groundwater_storage: Amount of water that is stored in the groundwater reservoir
            , [mm]
        vertical_flow_to_groundwater: Flow from the lower soil layer to groundwater for
            this timestep, [mm]
        bypass_flow: Flow that bypasses the soil matrix and drains directly to the
            groundwater, [mm]
        max_percolation_rate_uzlz: Maximum percolation rate between upper and lower
            groundwater zone for this timestep, [mm]
        groundwater_loss: Potential amount of water that never rejoins the river channel
            and is lost beyond the catchment boundaries or to deep groundwater systems
            for this timestep, [mm]
        reservoir_const_upper_groundwater: Reservoir constant for the upper groundwater
            layer, [days]
        reservoir_const_lower_groundwater: Reservoir constant for the lower groundwater
            layer, [days]

    Returns:
        updated amount of water stored in upper and lower zone, outflow from the upper
        zone to the channel, outflow from the lower zone to the channel, and actual
        groundwater loss
    """

    output = {}

    # Update water stored in upper zone, [mm]
    upper_zone = np.array(
        groundwater_storage[0] + vertical_flow_to_groundwater + bypass_flow
    )

    # The water that percolates from the upper to the lower groundwater zone is defined
    # as the minimum of `max_percolation_rate_uzlz` and the amount water stored in upper
    # zone
    percolation_to_lower_zone = np.minimum(
        max_percolation_rate_uzlz,
        upper_zone,
    )

    # Update water stored in upper zone after percolation, [mm]
    upper_zone = upper_zone - percolation_to_lower_zone

    # Calculate outflow from the upper zone to the channel, [mm]
    output["subsurface_flow"] = np.minimum(
        np.maximum(0.0, upper_zone / reservoir_const_upper_groundwater),
        upper_zone,
    )

    # Update water stored in lower zone, [mm], must be >= 0
    lower_zone = np.array(groundwater_storage[1] + percolation_to_lower_zone)

    # Groundwater loss cannot exceed available water in lower zone, [mm]
    groundwater_loss = np.minimum(groundwater_loss, lower_zone)
    output["groundwater_loss"] = groundwater_loss

    # Apply groundwater loss
    lower_zone = lower_zone - groundwater_loss

    # Calculate outflow from the lower zone to the channel, [mm], must be >= 0
    output["baseflow"] = np.minimum(
        np.maximum(0.0, lower_zone / reservoir_const_lower_groundwater),
        lower_zone,
    )

    # Update ground water storage
    output["groundwater_storage"] = np.vstack(
        (upper_zone - output["subsurface_flow"], lower_zone - output["baseflow"])
    )

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

    :math:`Q_2 = k_{Q_2} \, S_e^{\beta_{Q_2}} \, \max(q_{\mathrm{root}} - T, 0)`

    where :math:`Q_2` is the lateral subsurface stormflow (mm timestep-1),
    :math:`k_{Q_2}`
    is the empirical lateral flow coefficient, :math:`S_e` is the effective saturation
    of the middle soil layer (-), :math:`beta_{Q_2}` is a non-linearity exponent,
    :math:`S2` is the middle soil water storage (mm), :math:`q_{root}` is the root-zone
    soil moisture (mm), and :math:`T` is the transpiration
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
