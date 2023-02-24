"""The ``models.soil.carbon`` module  simulates the soil carbon cycle for the Virtual
Rainforest. At the moment only two pools are modelled, these are low molecular weight
carbon (LMWC) and mineral associated organic matter (MAOM). More pools and their
interactions will be added at a later date.
"""  # noqa: D205, D415

import numpy as np
from xarray import DataArray, Dataset

from virtual_rainforest.core.base_model import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.soil.constants import (
    BindingWithPH,
    MaxSorptionWithClay,
    MoistureScalar,
    TempScalar,
)

# TODO - I'm basically certain that the paper I've taken this model structure from has
# not used units consistently (in particular the BINDING_WITH_PH). Down the line I need
# to track down a reliable parameterisation for this section.


class SoilCarbonPools:
    """Class containing the full set of soil carbon pools.

    At the moment, only two pools are included. Functions exist for the transfer of
    carbon between these pools, but not with either the yet to be implemented soil
    carbon pools, other pools in the soil module, or other modules.
    """

    def __init__(self, maom: DataArray, lmwc: DataArray) -> None:
        """Initialise set of carbon pools."""

        # Check that arrays are of equal size and shape
        if maom.shape != lmwc.shape:
            to_raise = InitialisationError(
                "Dimension mismatch for initial carbon pools!",
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Check that negative initial values are not given
        if np.any(maom < 0) or np.any(lmwc < 0):
            to_raise = InitialisationError(
                "Initial carbon pools contain at least one negative value!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.maom = maom
        """Mineral associated organic matter pool (kg C m^-3)"""
        self.lmwc = lmwc
        """Low molecular weight carbon pool (kg C m^-3)"""

    def update_soil_carbon_pools(self, delta_pools: Dataset) -> None:
        """Update soil carbon pools based on previously calculated net change.

        The state of the soil carbon pools will effect the rate of other processes in
        the soil module. These processes in turn can effect the exchange rates between
        the soil organic matter pools. Thus, separate update functions (like this one)
        are necessary so that update increments for all soil module components can be
        calculated on a single state, which is only then updated when all increments
        have been calculated.

        Args:
            delta_pools: Array of updates for every pool
        """

        self.maom += delta_pools["delta_maom"]
        self.lmwc += delta_pools["delta_lmwc"]

    def calculate_soil_carbon_updates(
        self,
        pH: DataArray,
        bulk_density: DataArray,
        soil_moisture: DataArray,
        soil_temp: DataArray,
        percent_clay: DataArray,
        dt: float,
    ) -> Dataset:
        """Calculate net change for each carbon pool.

        This function calls lower level functions which calculate the transfers between
        pools. When all transfers have been calculated the net transfer is used to
        calculate the net change for each pool.

        Args:
            pH: pH values for each soil grid cell
            bulk_density: bulk density values for each soil grid cell (kg m^-3)
            soil_moisture: relative water content for each soil grid cell (unitless)
            soil_temp: soil temperature for each soil grid cell (degrees C)
            percent_clay: Percentage clay for each soil grid cell
            dt: time step (days)

        Returns:
            A vector containing net changes to each pool. Order [lmwc, moam].
        """
        # TODO - Add interactions which involve the three missing carbon pools

        lmwc_to_maom = self.mineral_association(
            pH, bulk_density, soil_moisture, soil_temp, percent_clay
        )

        # Determine net changes to the pools
        delta_maom = lmwc_to_maom * dt
        delta_lmwc = -lmwc_to_maom * dt

        return Dataset(
            data_vars=dict(
                delta_maom=DataArray(delta_maom, dims="cell_id"),
                delta_lmwc=DataArray(delta_lmwc, dims="cell_id"),
            )
        )

    def mineral_association(
        self,
        pH: DataArray,
        bulk_density: DataArray,
        soil_moisture: DataArray,
        soil_temp: DataArray,
        percent_clay: DataArray,
    ) -> DataArray:
        """Calculates net rate of LMWC association with soil minerals.

        Following :cite:t:`abramoff_millennial_2018`, mineral adsorption of carbon is
        controlled by a Langmuir saturation function. At present, binding affinity and
        Q_max are recalculated on every function called based on pH, bulk density and
        clay content. Once a decision has been reached as to how fast pH and bulk
        density will change (if at all), this calculation may need to be moved
        elsewhere.

        Args:
            pH: pH values for each soil grid cell
            bulk_density: bulk density values for each soil grid cell (kg m^-3)
            soil_moisture: relative water content for each soil grid cell (unitless)
            soil_temp: soil temperature for each soil grid cell (degrees C)
            percent_clay: Percentage clay for each soil grid cell

        Returns:
            The net flux from LMWC to MAOM (kg C m^-3 day^-1)
        """

        # Calculate
        Q_max = calculate_max_sorption_capacity(bulk_density, percent_clay)
        equib_maom = calculate_equilibrium_maom(pH, Q_max, self.lmwc)

        # Find scalar factors that multiple rates
        temp_scalar = convert_temperature_to_scalar(soil_temp)
        moist_scalar = convert_moisture_to_scalar(soil_moisture)

        return temp_scalar * moist_scalar * self.lmwc * (equib_maom - self.maom) / Q_max


def calculate_max_sorption_capacity(
    bulk_density: DataArray,
    percent_clay: DataArray,
    coef: MaxSorptionWithClay = MaxSorptionWithClay(),
) -> DataArray:
    """Calculate maximum sorption capacity based on bulk density and clay content.

    The maximum sorption capacity is the maximum amount of mineral associated organic
    matter that can exist per unit volume. This expression and its parameters are also
    drawn from :cite:t:`mayes_relation_2012`. In that paper max sorption also depends on
    Fe content, but we are ignoring this for now.

    Args:
        bulk_density: bulk density values for each soil grid cell (kg m^-3)
        percent_clay: Percentage clay for each soil grid cell

    Returns:
        Maximum sorption capacity (kg m^-3)
    """

    # Check that negative initial values are not given
    if np.any(percent_clay > 100.0) or np.any(percent_clay < 0.0):
        to_raise = ValueError(
            "Relative clay content must be expressed as a percentage!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    Q_max = bulk_density * 10 ** (coef.slope * np.log10(percent_clay) + coef.intercept)
    return Q_max


def calculate_equilibrium_maom(
    pH: DataArray,
    Q_max: DataArray,
    lmwc: DataArray,
) -> DataArray:
    """Calculate equilibrium MAOM concentration based on Langmuir coefficients.

    Equilibrium concentration of mineral associated organic matter (MAOM) is calculated
    by this function under the assumption that the concentration of low molecular weight
    carbon (LMWC) is fixed.

    Args:
        pH: pH values for each soil grid cell Q_max: Maximum sorption capacities (kg
        m^-3)
        lmwc: Low molecular weight carbon pool (kg C m^-3)

    Returns:
        Equilibrium concentration of MAOM (kg C m^-3)
    """

    binding_coefficient = calculate_binding_coefficient(pH)
    return (binding_coefficient * Q_max * lmwc) / (1 + lmwc * binding_coefficient)


def calculate_binding_coefficient(
    pH: DataArray, coef: BindingWithPH = BindingWithPH()
) -> DataArray:
    """Calculate Langmuir binding coefficient based on pH.

    This specific expression and its parameters are drawn from
    :cite:t:`mayes_relation_2012`.

    Args:
        pH: pH values for each soil grid cell

    Returns:
        Langmuir binding coefficients for mineral association of labile carbon (m^3
        kg^-1)
    """

    return 10.0 ** (coef.slope * pH + coef.intercept)


def convert_temperature_to_scalar(
    soil_temp: DataArray, coef: TempScalar = TempScalar()
) -> DataArray:
    """Convert soil temperature into a factor to multiply rates by.

    This form is used in :cite:t:`abramoff_millennial_2018` to minimise differences with
    the CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
       soil_temp: soil temperature for each soil grid cell (degrees C)

    Returns:
        A scalar that captures the impact of soil temperature on process rates
    """

    # This expression is drawn from Abramoff et al. (2018)
    numerator = coef.t_2 + (coef.t_3 / np.pi) * np.arctan(
        np.pi * (soil_temp - coef.t_1)
    )
    denominator = coef.t_2 + (coef.t_3 / np.pi) * np.arctan(
        np.pi * coef.t_4 * (coef.ref_temp - coef.t_1)
    )

    return DataArray(np.divide(numerator, denominator), dims="cell_id")


def convert_moisture_to_scalar(
    soil_moisture: DataArray,
    coef: MoistureScalar = MoistureScalar(),
) -> DataArray:
    """Convert soil moisture into a factor to multiply rates by.

    This form is used in :cite:t:`abramoff_millennial_2018` to minimise differences with
    the CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
        soil_moisture: relative water content for each soil grid cell (unitless)

    Returns:
        A scalar that captures the impact of soil moisture on process rates
    """

    if np.any(soil_moisture > 1.0) or np.any(soil_moisture < 0.0):
        to_raise = ValueError(
            "Relative water content cannot go below zero or above one!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    # This expression is drawn from Abramoff et al. (2018)
    return DataArray(
        1 / (1 + coef.coefficient * np.exp(-coef.exponent * soil_moisture)),
        dims="cell_id",
    )
