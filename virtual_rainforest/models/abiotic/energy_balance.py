"""The `abiotic.energy_balance` module.

This module calculates the energy balance for the Virtual Rainforest.
Under steady state, the heat balance equation for the leaves in each canopy layer is as
follows:
absorbed radiation - emitted radiation - sensible heat flux - latent heat flux = 0

The sequence of processes is based on Maclean et al, 2021: Microclimc: A mechanistic
model of above, below and within-canopy microclimate. Ecological Modelling
Volume 451, 109567. https://doi.org/10.1016/j.ecolmodel.2021.109567.
"""

# import numpy as np
# from numpy.typing import NDArray

# from core.constants import CONSTANTS as C


class EnergyBalance:
    """EnergyBalance method."""

    def __init__(self) -> None:
        """Initializes point-based energy_balance method."""
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_energy_balance(self, args: None, kwargs: None) -> None:
        """Calculates energy balance under steady state.

        Args: global variables: "soilparams", "climvars", "weather"
            climate variables:
                tair, air temperature at 2 m above canopy (deg C)
                relhum, relative humidity at 2 m above canopy (percentage)
                pk, pressure at 2 m above canopu (kPA)
                u, wind speed at reference height (m/s)
                tsoil, temperature below deepest soil layer
                Rsw, Incoming shortwave radiation (W / m2)
                dp, proportion of `Rsw` that is diffuse radiation
                H, Sensible heat flux (W / m^2)

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
    # Set limits to tcan
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

    def thomas(self, )->None:
        """Thomas algorithm for solving simultanious heat fluxes between soil/air.
        
        Args:
            tc vector of soil and air temperatures (deg C) from previous timestep
            tmsoil temperature (deg C) of deepest soil layer. Typically mean annual temperature
            tair air temperature at reference height 2 m above canopy in current time step (deg C)
            k vector of thermal conductances between layers (W / m^2 / K) (see details)
            cd thermal heat capacity of layers (J / m^3 / K)
            f forward / backward weighting of algorithm (see details)
            X vector of temperatures to be added resulting from e.g. leaf heat fluxes or radiation
            #' absorbed by top soil layer
        Returns:
            a vector of temperatures (deg C) for each soil / air layer for current time step. The first value
            #' is `tair` and the last `tmsoil`
    
        Details:
            The vector `tc` must be ordered with reference air temperature first and the soil temperature
#' of the  deepest layer last. I.e. the length of the vector `tc` is the number of nodes + 2.
#' The vector `k` is the conductivity between each node and that diectly below it, the first value
#' representing conductivity between reference height and the top canopy node. I.e. the length
#' of the vector `k` is the number of nodes + 1. The vector `cd` is the heat storage at each node.
#' I.e. the length of the vector `cd` is the same as the number of nodes. The  weighting factor `f`  may
#' range from 0 to 1. If `f` = 0, the flux is determined by the temperature difference at the beginning
#' of the time step. If `f` = 0.5, the average of the old and new temperatures is used to compute heat flux.
#' If `f` = 1, fluxes are computed using only the new temperatures. The best value to use
#' for `f` is determined by considerations of numerical stability and accuracy and experimentation
#' may be required. If `f` = 0  more heat transfer between nodes is predicted than would actually
#' occur, and can therefore become unstable if time steps are too large. When `f` > 0.5,
#' stable solutions will always be obtained, but heat flux will be underestimated. The
#' best accuracy is obtained with `f` around 0.4, while best stability is at `f` = 1.
#' A typical compromise is `f` = 0.6.
        """

    def thomasV()-> None:
    """Thomas algorithm for solving simultanious vapour fluxes between air layers.

    Args:
        Vo a vector of air vapour concentrations for each canopy node in the previos timestep (mol fraction)
        tn vector of air temperatures (deg C) for each canopy node in the current timestep (deg C)
        pk atmospheric pressure (kPa)
        theta Volumetric water content of the upper most soil layer in the current time step (m3 / m3)
        thetap Volumetric water content of the upper most soil layer in the previous time step (m3 / m3)
        relhum relative humidity (percentage) at reference height 2 m above canopy in current time step (percentage)
        tair air temperature at reference height 2 m above canopy in current time step (deg C)
        tsoil temperature of upper soil layer in current time step (deg C)
        zth heightdifference between each canopy node and that directly below it. the first value is
        #' the height difference between the lowest canopy node and the ground
        gt vector of molar conductances between each canopy node at that directly below it (mol / m^2 / sec).
        #' The first value is the conductivity between the ground and the lowest node, and the last value the
        #' conductivity between the highest node and reference height.
        Vflux Total vapour flux from leaves to air (mol /m^3)
        f forward / backward weighting of algorithm (as for [Thomas()])
        previn a list of model outputs form the previous timestep
        soilp a list of soil parameters as returned by [soilinit()]

    Returns:
    a vector of vapour concentrations expressed as mole fractions for each canopy node in the
    #' current time step. The first value is that for the ground and the last value that at reference height
"""