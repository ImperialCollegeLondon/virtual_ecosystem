"""The `abiotic.energy_balance` module.

Following the approach by Maclean et al., (2021), above-canopy temperature, humidity and
wind profiles are calculated using K-theory with estimates of bulk aerodynamic
resistance derived from canopy properties.

Within the canopy, radiation transmission and wind profiles are also estimated from
canopy properties. These, in turn, are used to estimate turbulent transfer within the
canopy and boundary layer ??and stomatal conductance for each canopy layer. Heat balance
equations for each canopy layer are then linearized, enabling simultaneous calculation
of leaf and air temperatures. Time-dependant differential equations for each canopy and
soil node are then specified and storage and simultaneous exchanges of heat and
vapour between each layer then computed using the Thomas algorithm.

Under steady-state, the heat balance equation for the leaves in each canopy layer is as
follows:
Rabs-Rem-H-lE= Rabs-esT^4-cp gHa(TL-TA)-lGv*(eL-eA)/Pa) = 0

The heat energy balance for the forest floor is as follows:
Rabs-Rem-H-lE-G=0

Rabs and lE are calculated in the plant module.

"""


class EnergyBalance:
    """EnergyBalance method.

    Attributes:
        rnet_profile

        wind_above_canopy
        wind_below_canopy

        temp_above_canopy
        temp_below_canopy
        temp_soil

        air_humidity

    """

    def __init__(self) -> None:
        """Initializes point-based energy_balance method."""
        pass

    def calc_netrad_profile(self, args: None, kwargs: None) -> None:
        """Calculate canopy net radiation profile.

        Args:
            rnet_in: net shortwave radiation top of the canopy [W m-2]
            r_abs: fraction of radiation absorbed by each canopy layer

        Returns:
            rnet_profile
        """
        raise NotImplementedError("Implementation of this feature is still missing")

    # above canopy
    def calc_wind_above_canopy(self, args: None, kwargs: None) -> None:
        """Calculates the wind profile above the canopy.

        Args:
            d: height above ground in canopy where wind profile extrapolates to zero [m]
            z_M: roughness length for momentum [m]
            psi_M: diabatic correction for momemtum
            u_star: friction velocity of wind [m s-1]

        Returns:
            u_z: wind speed at height z (-> vertical profile, above canopy) [m s-1]
        """
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_temp_above_canopy(self, args: None, kwargs: None) -> None:
        """Calculates the temperature at the top of the canopy.

        Args:
            t_dzH: temp at height of exchange surface d+zH [deg C]
            psi_H: diabatic correction factor for heat
            c_p: specific heat of air at constant pressure [J mol-1 K-1]
            rho_air: molar density of air [mol m-3]
            u_star: fricton velocity [m s-1]
            H: sensible heat flux (from canopy) [W m-2]
            d: height above ground in canopy where wind profile extrapolates to zero [m]
            z_H: roughness length for heat transfer [m]

        Returns:
            t_z: temperature above canopy [deg C]
        """
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_cond_above_canopy(self, args: None, kwargs: None) -> None:
        """Calculates heat conductance (sensible heat flux) at the top of the canopy.

        Args:
            rho_air: molar density of air [mol m-3]
            u_star: fricton velocity [m s-1]
            z: vector of heights that exchange heat [m]
            d: height above ground in canopy where wind profile extrapolates to zero [m]
            psi_H_above: diabatic correction factor for heat

        Returns:
            g_t_above: heat conducance above canopy [mol m-2 s-1]
        """
        raise NotImplementedError("Implementation of this feature is still missing")

    # below canopy
    def calc_wind_below_canopy(self, args: None, kwargs: None) -> None:
        """Calculates the wind profile below the canopy.

        Args:
            u_h: wind speed at top op canopy at height h [m s-1]
            h: top of canopy height [m]
            z: vector of heights that exchange heat [m]
            a: attenuation coefficient (function of canopy shape)

        Returns:
            u_z: wind speed at height z (-> vertical profile, below canopy) [m s-1]
        """
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_cond_below_canopy(self, args: None, kwargs: None) -> None:
        """Calculates heat conductance (sensible heat flux) below the canopy.

        Args:
            u_h: wind speed at top op canopy at height h [m s-1]
            l_m: mean mixing length
            i_w: relatove turbulence intensity
            a: attenuation coefficient (function of canopy shape)
            h: top of canopy height [m]
            psi_H_canopy: within canopy correction factor for heat

        Returns:
            g_t_canopy: within-canopy heat conductance [mol m-2 s-1]

        """
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_cond_canopy_air(self, args: None, kwargs: None) -> None:
        """Calculates heat conductance between canopy and air depending on wind speed.

        Args:
            rho_air: molar density of air [mol m-3]
            d_h: thermal diffusivity [m2 s-1]
            x_d: characteristic leaf dimesion [m]
            re_nr: Reynolds number
            pr_nr: Prantl number
            gr_nr: Grashof number

        Returns:
            g_Ha: heat conductance between canopy and air [mol m-2 s-1]

        """
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_surface_fluxes(self, args: None, kwargs: None) -> None:
        """Calculates sensible and latent heat flux from the surface."""
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_temp_below_canopy(self, args: None, kwargs: None) -> None:
        """Calculates the average leaf and air temperature of each canopy layer."""
        raise NotImplementedError("Implementation of this feature is still missing")

    def calc_vap_below_canopy(self, args: None, kwargs: None) -> None:
        """Calculates the air vapor concentration of each canopy layer."""
        raise NotImplementedError("Implementation of this feature is still missing")

    def thomas(self, args: None, kwargs: None) -> None:
        """Thomas algorithm for solving simultanious heat fluxe between soil/air layers.

        Implementation after Maclean et al., (2021).
        """
        raise NotImplementedError("Implementation of this feature is still missing")

    def thomasV(self, args: None, kwargs: None) -> None:
        """Thomas algorithm for solving simultanious vapour fluxes between air layers.

        Implementation after Maclean et al., (2021).
        """
        raise NotImplementedError("Implementation of this feature is still missing")

    # Run energy balance
    def run_energy_balance(self, args: None, kwargs: None) -> None:
        """Runs series of functions to compute energy balance."""
        # calc_netrad_profile()
        #
        # --- above canopy ---
        # calc_wind_above_canopy()
        # calc_temp_above_canopy()
        # calc_cond_above_canopy()
        #
        # --- below canopy ---
        # calc_wind_below_canopy()
        # calc_cond_below_canopy()
        # calc_cond_canopy_air()
        # calc_surface_fluxes()
        # calc_temp_below_canopy()
        # calc_vap_below_canopy()
        # thomas()
        # thomasV()
        raise NotImplementedError("Implementation of this feature is still missing")
