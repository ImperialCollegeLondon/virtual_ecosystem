"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from __future__ import annotations

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.constants import AnimalConsts
from virtual_ecosystem.models.animal.protocols import Consumer


class PlantResources:
    """Interface between plants model variables in ``Data`` and the animal module."""

    def __init__(
        self,
        resource_name: str,
        cell_id: int,
        data: Data,
        constants: AnimalConsts,
        pft_dim: str = "plant_functional_type",
        cnp_proportions: dict[str, float] | None = None,
    ) -> None:
        accepted_names = [
            "canopy_n_propagules",
            "fallen_n_propagules",
            "layer_leaf_mass",
            "subcanopy_vegetation_biomass",
            "subcanopy_seedbank_biomass",
        ]

        if resource_name not in accepted_names:
            err = ValueError(
                f"Invalid plant resource name provided ({resource_name}), "
                f"resources available for animal consumption are: {accepted_names}"
            )
            LOGGER.critical(err)
            raise err

        # Map resource names to their vertical occupancy
        vertical_map: dict[str, VerticalOccupancy] = {
            "canopy_n_propagules": VerticalOccupancy.CANOPY,
            "fallen_n_propagules": VerticalOccupancy.GROUND,
            "layer_leaf_mass": VerticalOccupancy.CANOPY,
            "subcanopy_vegetation_biomass": VerticalOccupancy.GROUND,
            "subcanopy_seedbank_biomass": VerticalOccupancy.SOIL,
        }

        self.resource_name = resource_name
        self.vertical_occupancy = vertical_map[resource_name]
        self.cell_id = cell_id
        self.constants = constants
        self.pft_dim = pft_dim

        # Stoichiometry (toy split until plant-side element data are exposed).
        self.cnp_proportions: dict[str, float] = (
            {"carbon": 0.7, "nitrogen": 0.2, "phosphorus": 0.1}
            if cnp_proportions is None
            else dict(cnp_proportions)
        )

        # Derived masses
        self.mass_current: float = 0.0
        self.mass_stoich: dict[str, float] = {
            "carbon": 0.0,
            "nitrogen": 0.0,
            "phosphorus": 0.0,
        }
        self.is_alive: bool = True

        # Initialize from data and compute stoichiometry.
        self.mass_current = self._extract_mass_from_data(data=data)
        if self.mass_current < 0:
            msg = (
                f"{resource_name}: negative mass detected in cell {cell_id} "
                f"({self.mass_current})."
            )
            raise ValueError(msg)
        self._update_stoichiometric_mass()

    def _extract_mass_from_data(self, data: Data) -> float:
        """Extracts per-cell resource mass, summing PFTs when present."""
        return 0

    def _update_stoichiometric_mass(self) -> None:
        """Updates C/N/P mass dict from ``mass_current`` and proportions."""
        self.mass_stoich = {
            element: self.mass_current * proportion
            for element, proportion in self.cnp_proportions.items()
        }

    def set_mass_current(self, new_mass: float) -> None:
        """Sets a new mass for the resource and updates stoichiometric mass.

        Args:
            new_mass: New resource mass (kg). Must be non-negative.

        Raises:
            ValueError: If ``new_mass`` is negative.
        """
        # Guard against negative mass.
        if new_mass < 0:
            raise ValueError("Mass cannot be negative.")
        self.mass_current = new_mass
        self._update_stoichiometric_mass()

    def get_eaten(
        self,
        consumed_mass: float,
        consumer: Consumer,
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Consumes resource mass and returns CNP flows to herbivore and to waste.

        The herbivore first loses a fraction of the ingested mass due to mechanical
        efficiency (chewing/handling). The remaining mass is the "effective mass"
        that can be converted into herbivore biomass according to conversion
        efficiency. The mechanical-loss fraction is returned as CNP waste, which the
        caller can route to litter/excrement pools as appropriate.

        Args:
            consumed_mass: Intended total consumed mass (kg).
            consumer: Consumer eating the plant resource.

        Returns:
            A tuple of the herbivore gain and plant waste additions as cnp dicts.

        """
        # Handle zero or invalid request fast.
        if consumed_mass <= 0:
            zero = {e: 0.0 for e in self.cnp_proportions}
            return zero, zero

        # Constrain by available mass.
        actual = min(self.mass_current, consumed_mass)

        # Remove from the pool (this also refreshes CNP split).
        self.set_mass_current(self.mass_current - actual)

        # Split consumed mass into effective vs mechanical loss.
        mech_eff = consumer.functional_group.mechanical_efficiency
        conv_eff = consumer.functional_group.conversion_efficiency

        # Effective mass that can be converted to tissue.
        effective = actual * mech_eff

        # Mechanical loss mass (becomes waste routed by caller).
        waste = actual * (1.0 - mech_eff)

        # Net gain after conversion efficiency.
        net_gain = effective * conv_eff

        # Translate scalar masses to CNP dicts.
        herbivore_gain_cnp = {e: net_gain * p for e, p in self.cnp_proportions.items()}
        plant_waste_cnp = {e: waste * p for e, p in self.cnp_proportions.items()}

        return herbivore_gain_cnp, plant_waste_cnp
