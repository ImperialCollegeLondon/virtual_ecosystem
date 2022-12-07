"""The `abiotic.radiation` module.

The radiation module calculates the radiation balance of the Virtual Rainforest.
Top of canopy net shortwave radiation at a given location depends on
    1. extra-terrestrial radiation (affected by the earth's orbit, time of year and
        day, and location on the earth),
    2. terrestrial radiation (affected by atmospheric composition and clouds),
    3. topography (slope and aspect), and
    4. surface albedo (vegetation type and fraction of vegetation/bare soil).

Terrestial radiation can be derived from climatologies (e.g. WFDE5) or calculated here;
the implementation is based on Davis et al., (2017). The effects of topography are taken
into account with a factor derived from the preprocessing module.

The vertical profile of net radiation below the canopy depends on the canopy
structure, the amount of radiation absorbed by the canopy, and the longwave radiation
emitted by canopy and surface.

The radiation balance can be calculated with the radiation_balance() function. If
terrestrial radiation is NOT provided as an input, it will be calculated internally.

# the following structural components are not implemented yet
TODO core.constants
TODO include vertical structure (canopy layers)
TODO include data structure (->numpy array)
TODO include time dimension
TODO logging, raise errors
"""

# import numpy as np
# from core.constants import kc, kd, kfFEC, bolz # this doesn't exist yet
kc = 1
kd = 1
kfFEC = 1
bolz = 1


class Radiation:
    """Radiation balance.

    Attributes:
        topofcanopy_radiation: float, shortwave radiation, top of canopy [W m-2]
        ppfd: float, photosynth. photon flux density, top of canopy [mol m-2]
        rn_profile: float, net radiation profile, below canopy [W m-2]
    """

    def __init__(self) -> None:
        """Initializes point-based radiation method."""
        pass

    def calc_sw_down(self, n: int, y: int, lat: float) -> float:
        """Calculate shortwave downward radiation.

        This function calculated incoming shortwave radiation based on location and time
        of year if this is NOT provided as an input to the virtual rainforest.

        Args:
            n: day of the year
            y: year
            lat: latitude

        Ref:
            Davis et al. (2017): Simple process-led algorithms for simulating habitats
            (SPLASH v.1.0): robust indices of radiation, evapotranspiration and plant-
            available moisture, Geosci. Model Dev., 10, 689-708
        """
        raise NotImplementedError("Implementation of this feature is missing")

    def calc_topofcanopy_radiation(
        self,
        sw_in: float,
        n: int,
        y: int,
        lat: float,  # this is optional for the case of sw_in == FALSE
        elev: float,
        sf: float,
        topo_factor: float,
        sw_albedo: float,
        vis_albedo: float,
    ) -> None:
        """Calculate top of canopy shortwave radiation.

        If sw_in (extra-terrestrial) radiation is NOT provided as an input, it is
        calculated as a function of latitude and date based on the SPLASH model
        (Davis et al., 2017).

        Args:
            sw_in: shortwave downward radiation [W m-2]
            n: day of year
            y: year
            lat: latitude
            elev: elevation (m)
            sf: fraction of sunshine hours
            topo_factor: topographic adjustment factor for radiation (slope and aspect)
            sw_albedo: shortwave albedo (function of vegetation and bare soil fraction)
            vis_albedo: albedo visible light (for PPFD calculation)

        Returns:
            topofcanopy_radiation
            ppfd
        """
        # check if shortwave down is provided, else calculate
        if sw_in:
            sw_down = sw_in
        else:
            sw_down = self.calc_sw_down(n, y, lat)

        # atmospheric filtering (clouds, aerosols)
        tau_o = kc + kd * sf
        tau = tau_o * (1.0 + (2.67e-5) * elev)
        sw_down_f = sw_down * tau

        # topography and albedo effects on shortwave radiation
        sw_net_toc = (1 - sw_albedo) * sw_down_f * topo_factor
        self.sw_net_toc = sw_net_toc

        # PPFD
        # TODO integrate over duration of the day?
        ppfd = (1.0e-6) * kfFEC * (1.0 - vis_albedo) * sw_down_f
        self.ppfd = ppfd

    def calc_canopy_radiation(
        self, canopy_abs: float, tc: float, ts: float, emis: list
    ) -> None:
        """Calculates daily net radiation profile within the canopy.

        The output is a vector of net radiation, the first entry is the top
        of the canopy, the last entry is the net radiation that reaches the surface.

        Args:
            n_level: number of canopy layers
            canopy_abs: absorption by canopy (from plant module) [W m-2]
            emis: vector with canopy and soil emmissivity
            tc: vector of canopy temperatures
            ts: surface soil temperature

        Returns:
            rn_profile: vertical profile net shortwave radiation [W m-2]

           TODO: consider multiple layers
        """
        # Estimate net longwave emission
        lw_profile = emis[0] * bolz * (tc**4) + emis[1] * bolz * (ts**4)

        # We need a number of stept to integrate radiatio over the duration of the day,
        # this could happen here or in a different function?

        # Calculate net radiation cross-over hour angle (hn), degrees
        # Calculate daytime net radiation (rn_d), J/m^2
        # Calculate nighttime net radiation (rnn_d), J/m^2

        # calculate vertical canopy shortwave radiation profile
        sw_profile = self.sw_net_toc - canopy_abs

        # calculate vertical canopy net radiation profile
        rn_profile = sw_profile - lw_profile
        self.rn_profile = rn_profile

    def radiation_balance(
        self,
        sw_in: float,
        n: int,
        y: int,
        lat: float,
        elev: float,
        sf: float,
        topo_factor: float,
        sw_albedo: float,
        vis_albedo: float,
        canopy_abs: float,
        tc: float,
        ts: float,
        emis: list,
    ) -> None:
        """Calculate radiation balance."""
        self.calc_topofcanopy_radiation(
            sw_in, n, y, lat, elev, sf, topo_factor, sw_albedo, vis_albedo
        )
        self.calc_canopy_radiation(canopy_abs, tc, ts, emis)
