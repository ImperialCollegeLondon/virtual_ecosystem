"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest.
Under steady state, the heat balance equation for the leaves in each canopy layer is as
follows:
absorbed radiation - emitted radiation - sensible heat flux - latent heat flux = 0

The sequence of processes is based on Maclean et al, 2021: Microclimc: A mechanistic
model of above, below and within-canopy microclimate. Ecological Modelling
Volume 451, 109567. https://doi.org/10.1016/j.ecolmodel.2021.109567.
"""

import numpy as np
from numpy.typing import NDArray

# from core.constants import CONSTANTS as C


class EnergyBalance:
    """EnergyBalance method."""

    def __init__(self) -> None:
        """Initializes point-based energy_balance method."""
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_energy_balance(self, args: None, kwargs: None) -> None:
        """Calculates energy balance under steady state.

        Args:
            climate variables:
                tair, air temperature at 2 m above canopy (deg C)
                relhum, relative humidity at 2 m above canopy (percentage)
                pk, pressure at 2 m above canopy (kPA)
                u, wind speed at reference height (m/s)
                tsoil, temperature below deepest soil layer
                Rsw, Incoming shortwave radiation (W / m2)
                dp, proportion of `Rsw` that is diffuse radiation
                H, Sensible heat flux (W / m^2)

            soil varaibles:

        Returns:
            air_temperature
            canopy_temperature
            soil_temperature
            vapor_pressure_deficit

        """

    # --- this is the sequence of processes in microclimc for one time step ---
    # paraminit
    # soilinit
    # runonetimestep:
    # Check whether any vegetation layers have zero PAI
    # == Unpack climate variables ==
    # == calculate baseline variables: ==
    # - molar density of air
    # - specific heat of air
    # - latent heat of vaporisation
    # Adjust wind to 2 m above canopy
    # Generate heights of nodes
    # Set z above
    # == Calculate diabatic correction factors ==
    # Calculate temperatures and relative humidities for top of canopy
    # Set limits to temp can
    # Adjust relative humidity
    # == Calculate wind speed and turbulent conductances ==
    # == Calculate canopy turbulences ==
    # == Calculate conductivity to top of canopy and merge ==
    # Turbulent air conductivity and layer merge
    # == Calculate absorbed radiation
    # == Conductivities ==
    # Vapour conductivity
    # Leaf conductivity
    # == Soil conductivity ==
    # conductivity and specific heat
    # soil heat
    # Canopy air layer not in equilibrium with above canopy:
    # Heat to add / loose
    # vapour exchange
    # Interpolate
    # Canopy air layer in equilibrium with above canopy
    # Set limits to soil temperatures
    # Calculate Heat flux
    # Latent heat
    # dewpoints
    # Incoming radiation
    # internal function to sort out vegetation parameters

    def thomas(
        self,
        air_temperature: NDArray[np.float32],
        soil_temperature: NDArray[np.float32],
        mean_annual_temperature: NDArray[np.float32],
        air_temperature_2m: NDArray[np.float32],
        thermal_conductivity: NDArray[np.float32],
        thermal_heat_capacity: NDArray[np.float32],
        added_temperatures: NDArray[np.float32] = np.array(0.0, type=float),
        weighting_factor: float = 0.6,
    ) -> None:
        """Thomas algorithm for solving simultanious heat fluxes between soil/air.

        Args:
            air_temperature: NDArray[np.float32], air temperatures from previous
                timestep [C]
            soil_temperature: NDArray[np.float32], soil temperatures from previous
                timestep [C]
            mean_annual_temperature: NDArray[np.float32], mean annual temperature,
                here used as temperature of deepest soil layer [C]
            air_temperature_2m: NDArray[np.float32], air temperature at reference
                height 2 m above canopy in current time step [C]
            thermal_conductivity: NDArray[np.float32], thermal conductances between
                layers [W m-2 K-1], see details
            thermal_heat_capacity: NDArray[np.float32], thermal heat capacity of
                layers [J m-3 K-1]
            added_temperatures: NDArray[np.float32], temperatures to be added
                resulting from e.g. leaf heat fluxes or radiation absorbed by top soil
            weighting_factor:float = 0.6, forward / backward weighting of algorithm, see
                details

        Returns:
            air_temperature: NDArray[np.float32], air temperatures from current
                timestep [C]
            soil_temperature: NDArray[np.float32], soil temperatures from current
                timestep [C]

        Details:
            The vector `previous_temperatures` that combines air and soil temperatures
            must be ordered with reference air temperature first and the soil
            temperature of the deepest layer (= mean annual temperature) last. I.e. the
            length of the vector is the number of nodes + 2.
            The vector `thermal_conductivity` is the conductivity between each node and
            that dirctly below it, the first value representing conductivity between
            reference height and the top canopy node. I.e. the length of the vector is
            the number of nodes + 1.
            The vector `thermal_heat_capacity` is the heat storage at each node. I.e.
            the length of the vector is the same as the number of nodes.
            The `weighting_factor` may range from 0 to 1. If `weighting_factor` = 0, the
            flux is determined by the temperature difference at the beginning of the
            time step. If `weighting_factor` = 0.5, the average of the old and new
            temperatures is used to compute heat flux. If `weighting_factor` = 1, fluxes
            are computed using only the new temperatures. The best value to use for
            `weighting_factor` is determined by considerations of numerical stability
            and accuracy and experimentation may be required. If `weighting_factor` = 0
            more heat transfer between nodes is predicted than would actually occur, and
            can therefore become unstable if time steps are too large. When
            `weighting_factor` > 0.5, stable solutions will always be obtained, but heat
            flux will be underestimated. The best accuracy is obtained with
            `weighting_factor`around 0.4, best stability is at `weighting_factor`= 1.
            A typical compromise is `weighting_factor` = 0.6.

            m = n_layers ; check difference in starting from 0 or 1
            tn = current_temperature
        """
        # combine temperatures from previous timestep in one vector
        previous_temperatures = [
            air_temperature_2m,
            air_temperature,
            soil_temperature,
            mean_annual_temperature,
        ]

        # n_layers includes all soil and air layers
        n_layers = len(previous_temperatures) - 2

        # create empty array for current temperatures
        current_temperature = np.zeros(n_layers + 2, type=int)

        # assign first and last value, indices from maclean R code, needs changing!!
        current_temperature[n_layers + 2] = mean_annual_temperature
        current_temperature[1] = air_temperature_2m

        # derive factor `g` and `matrix zeros``
        a = [0, 0]
        b = 0
        cc = 0
        d = 0

        xx = range(2, (n_layers + 1))  ### ??? index ???

        previous_temperatures[xx] = (
            previous_temperatures[xx] + (1 - weighting_factor) * added_temperatures
        )
        cc[xx] = -thermal_conductivity[xx] * weighting_factor
        a[xx + 1] = cc[xx]
        b[xx] = (
            weighting_factor * (thermal_conductivity[xx] + thermal_conductivity[xx - 1])
            + thermal_heat_capacity
        )
        d[xx] = (
            (1 - weighting_factor)
            * thermal_conductivity[xx - 1]
            * previous_temperatures[xx - 1]
            + (
                thermal_heat_capacity
                - (1 - weighting_factor)
                * (thermal_conductivity[xx] + thermal_conductivity[xx - 1])
            )
            * previous_temperatures[xx]
            + (1 - weighting_factor)
            * thermal_conductivity[xx]
            * previous_temperatures[xx + 1]
        )
        d[2] = (
            d[2] + thermal_conductivity[1] * current_temperature[1] * weighting_factor
        )
        d[n_layers + 1] = (
            d[n_layers + 1]
            + thermal_conductivity[n_layers + 1]
            * weighting_factor
            * current_temperature[n_layers + 2]
        )

        for i in range(2, n_layers):
            cc[i] = cc[i] / b[i]
            d[i] = d[i] / b[i]
            b[i + 1] = b[i + 1] - a[i + 1] * cc[i]
            d[i + 1] = d[i + 1] - a[i + 1] * d[i]

        current_temperature[n_layers + 1] = d[n_layers + 1] / b[n_layers + 1]

        for i in range(
            2, n_layers
        ):  ### double-check, looks like error in original code
            current_temperature[i] = d[i] - cc[i] * current_temperature[i + 1]

        x_min = pmin(
            current_temperature[xx],
            current_temperature[xx - 1],
            current_temperature[xx + 1],
        )
        x_max = pmax(
            current_temperature[xx],
            current_temperature[xx - 1],
            current_temperature[xx + 1],
        )
        current_temperature[xx] = ifelse(
            current_temperature[xx] < x_min, x_min, current_temperature[xx]
        )
        current_temperature[xx] = ifelse(
            current_temperature[xx] > x_max, x_max, current_temperature[xx]
        )
        current_temperature[xx] = (
            current_temperature[xx] + weighting_factor * added_temperatures
        )

        return current_temperature

    def thomasV(self, args: None, kwargs: None) -> None:
        """Thomas algorithm for solving simultanious vapour fluxes between air layers.

        Args:
            Vo a vector of air vapour concentrations for each canopy node in the previos
            timestep (mol fraction)
            tn vector of air temperatures (deg C) for each canopy node in the current
            timestep (deg C)
            pk atmospheric pressure (kPa)
            theta Volumetric water content of the upper most soil layer in the current
            time step (m3 / m3)
            thetap Volumetric water content of the upper most soil layer in the previous
            time step (m3 / m3)
            relhum relative humidity (percentage) at reference height 2 m above canopy
            in current time step (percentage)
            tair air temperature at reference height 2 m above canopy in current time
            step (deg C)
            tsoil temperature of upper soil layer in current time step (deg C)
            zth heightdifference between each canopy node and that directly below it.
            The first value is the height difference between the lowest canopy node and
            the ground
            gt vector of molar conductances between each canopy node at that directly
            below it (mol / m^2 / sec). The first value is the conductivity between the
            ground and the lowest node, and the last value the conductivity between the
            highest node and reference height.
            Vflux Total vapour flux from leaves to air (mol /m^3)
            f forward / backward weighting of algorithm (as for [Thomas()])
            previn a list of model outputs form the previous timestep
            soilp a list of soil parameters as returned by [soilinit()]

        Returns:
            a vector of vapour concentrations expressed as mole fractions for each
            canopy node in the current time step. The first value is that for the ground
            and the last value that at reference height
        """
